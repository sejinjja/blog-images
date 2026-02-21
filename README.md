# blog-images

This repository stores blog PNG images.

It now includes `optimize_pngs.py` for safe in-place PNG optimization for web use.

## Requirements covered

- Keep file names and `.png` extension unchanged.
- No new `originals` folder.
- Safe to run multiple times without cumulative lossy degradation.

## Usage

1. Dry-run (no file changes):
```bash
python optimize_pngs.py posts
```

2. Apply in place:
```bash
python optimize_pngs.py posts --write
```

3. Custom options:
```bash
python optimize_pngs.py posts --write --colors 256 --min-reduction-bytes 1024
```

## Safety rules

- Palette PNG (`mode=P`) is never re-quantized with lossy conversion.
- Files are written to a temp file first, then atomically replaced with `os.replace`.
- `.png-opt-manifest.json` skips unchanged files on repeated runs.

## Daily operation

- Control file: `tasks/rule.md`
- Tagging guide: `docs/TAGGING_GUIDE.md`
- Reuse search guide: `docs/REUSE_SEARCH_GUIDE.md`
- No-API policy: `docs/NO_API_POLICY.md`
- Compact metadata index: `metadata/image_tags.jsonl` (`grouped-sem-v1`)
- Bilingual query alias map: `metadata/query_alias.json` (`sem-alias-v1`)
- Review log: `metadata/review_samples.md`
