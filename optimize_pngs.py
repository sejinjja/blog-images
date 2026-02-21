#!/usr/bin/env python3
"""Safe in-place PNG optimizer for web serving.

Goals:
- Keep original file names/extensions (.png) unchanged.
- Be safe to run multiple times without cumulative lossy degradation.
- Avoid partial/corrupted files via atomic replace.

Strategy:
1) For non-palette images, evaluate a lossy candidate (palette quantization) and a
   lossless candidate (PNG optimize). Pick the smallest that beats the original.
2) For palette images (mode 'P'), never apply lossy quantization again. Only test
   lossless re-save.
3) Use a manifest to skip unchanged files for repeated batch runs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image

SCRIPT_VERSION = "1.0"
MANIFEST_DEFAULT = ".png-opt-manifest.json"


@dataclass
class OptimizeResult:
    path: Path
    action: str
    strategy: str
    original_size: int
    new_size: int
    reason: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe in-place PNG batch optimizer")
    parser.add_argument(
        "targets",
        nargs="*",
        default=["posts"],
        help="Target directories or PNG files (default: posts)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Apply changes in place. Without this flag, runs as dry-run.",
    )
    parser.add_argument(
        "--colors",
        type=int,
        default=256,
        choices=range(2, 257),
        metavar="[2-256]",
        help="Palette size for first-pass lossy conversion (default: 256)",
    )
    parser.add_argument(
        "--min-reduction-bytes",
        type=int,
        default=1024,
        help="Minimum bytes saved required to replace a file (default: 1024)",
    )
    parser.add_argument(
        "--manifest",
        default=MANIFEST_DEFAULT,
        help=f"Manifest path (default: {MANIFEST_DEFAULT})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore manifest skip and re-check all target files.",
    )
    return parser.parse_args()


def list_png_files(targets: Iterable[str]) -> List[Path]:
    out: List[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_file() and p.suffix.lower() == ".png":
            out.append(p)
            continue
        if p.is_dir():
            out.extend(sorted(x for x in p.rglob("*.png") if x.is_file()))
    # dedupe while keeping deterministic order
    seen = set()
    deduped = []
    for p in out:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        deduped.append(p)
    return deduped


def load_manifest(path: Path) -> Dict:
    if not path.exists():
        return {"version": SCRIPT_VERSION, "signature": "", "files": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": SCRIPT_VERSION, "signature": "", "files": {}}


def save_manifest(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def png_bytes_lossless(im: Image.Image) -> bytes:
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def png_bytes_quantized(im: Image.Image, colors: int) -> bytes:
    has_alpha = "A" in im.getbands()
    if has_alpha:
        src = im.convert("RGBA")
        # FASTOCTREE is the safest practical method for RGBA quantization.
        quant = src.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    else:
        src = im.convert("RGB")
        quant = src.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)

    buf = io.BytesIO()
    quant.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def atomic_replace_bytes(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def optimize_one(path: Path, colors: int, min_reduction: int) -> OptimizeResult:
    orig_size = path.stat().st_size

    try:
        with Image.open(path) as im:
            mode = im.mode
            lossless = png_bytes_lossless(im)
            candidates: List[Tuple[str, bytes]] = [("lossless", lossless)]

            # Safety rule: never re-apply lossy quantization to palette PNGs.
            if mode != "P":
                try:
                    lossy = png_bytes_quantized(im, colors=colors)
                    candidates.append((f"palette-{colors}", lossy))
                except Exception:
                    pass
    except Exception as exc:
        return OptimizeResult(
            path=path,
            action="error",
            strategy="none",
            original_size=orig_size,
            new_size=orig_size,
            reason=str(exc),
        )

    best_name, best_bytes = min(candidates, key=lambda c: len(c[1]))
    best_size = len(best_bytes)

    if best_size >= orig_size:
        return OptimizeResult(
            path=path,
            action="skip",
            strategy=best_name,
            original_size=orig_size,
            new_size=orig_size,
            reason="not smaller",
        )

    if (orig_size - best_size) < min_reduction:
        return OptimizeResult(
            path=path,
            action="skip",
            strategy=best_name,
            original_size=orig_size,
            new_size=orig_size,
            reason=f"save<{min_reduction}B",
        )

    return OptimizeResult(
        path=path,
        action="replace",
        strategy=best_name,
        original_size=orig_size,
        new_size=best_size,
        reason="",
    )


def signature(colors: int, min_reduction: int) -> str:
    data = f"v={SCRIPT_VERSION};colors={colors};min_reduction={min_reduction}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def main() -> int:
    args = parse_args()

    files = list_png_files(args.targets)
    if not files:
        print("No PNG files found in targets.")
        return 0

    manifest_path = Path(args.manifest)
    man = load_manifest(manifest_path)
    man_files = man.get("files", {}) if isinstance(man.get("files"), dict) else {}

    sig = signature(args.colors, args.min_reduction_bytes)
    if man.get("signature") != sig:
        # Different settings => keep file history but refresh signature.
        man["signature"] = sig
    if "files" not in man or not isinstance(man["files"], dict):
        man["files"] = {}

    replaced = 0
    skipped = 0
    errored = 0
    bytes_before = 0
    bytes_after = 0

    print(f"targets={len(files)} write={args.write} colors={args.colors} min_reduction={args.min_reduction_bytes}")

    for idx, path in enumerate(files, 1):
        rel = str(path).replace("\\", "/")
        st = path.stat()
        bytes_before += st.st_size

        entry = man_files.get(rel, {}) if isinstance(man_files.get(rel, {}), dict) else {}
        unchanged_by_stat = (
            entry.get("size") == st.st_size
            and entry.get("mtime_ns") == st.st_mtime_ns
            and entry.get("signature") == sig
        )
        if unchanged_by_stat and not args.force:
            skipped += 1
            bytes_after += st.st_size
            if idx % 50 == 0 or idx == len(files):
                print(f"[{idx}/{len(files)}] skip(manifest): {rel}")
            continue

        result = optimize_one(path, colors=args.colors, min_reduction=args.min_reduction_bytes)

        if result.action == "error":
            errored += 1
            skipped += 1
            bytes_after += st.st_size
            print(f"[{idx}/{len(files)}] error: {rel} ({result.reason})")
            continue

        if result.action == "replace":
            if args.write:
                # Rebuild bytes from chosen strategy to keep memory low and ensure deterministic output.
                with Image.open(path) as im:
                    if result.strategy == "lossless":
                        data = png_bytes_lossless(im)
                    else:
                        data = png_bytes_quantized(im, colors=args.colors)
                atomic_replace_bytes(path, data)
                new_st = path.stat()
                bytes_after += new_st.st_size
                man["files"][rel] = {
                    "size": new_st.st_size,
                    "mtime_ns": new_st.st_mtime_ns,
                    "signature": sig,
                }
            else:
                bytes_after += result.new_size
            replaced += 1
            saved = result.original_size - result.new_size
            print(f"[{idx}/{len(files)}] replace: {rel} {result.original_size} -> {result.new_size} ({saved}B, {result.strategy})")
        else:
            skipped += 1
            bytes_after += st.st_size
            print(f"[{idx}/{len(files)}] skip: {rel} ({result.reason})")
            man["files"][rel] = {
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "signature": sig,
            }

    if args.write:
        save_manifest(manifest_path, man)

    total_saved = bytes_before - bytes_after
    pct = (total_saved / bytes_before * 100.0) if bytes_before else 0.0
    print("---")
    print(f"replaced={replaced} skipped={skipped} errors={errored}")
    print(f"before={bytes_before} after={bytes_after} saved={total_saved} ({pct:.2f}%)")
    print(f"mode={'WRITE' if args.write else 'DRY-RUN'}")

    return 0 if errored == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
