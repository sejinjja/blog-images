# Tagging Guide

## Purpose
- Maintain reusable semantic metadata with minimum token footprint.
- Keep `metadata/image_tags.jsonl` as the single source of truth.
- Keep tagging semantic-only (topic/object/intent).

## File Format
`metadata/image_tags.jsonl` uses `grouped-sem-v1`.

### Line 1: config row (`_ = cfg`)
- `_`: record type (`cfg`)
- `f`: format version (`grouped-sem-v1`)
- `b`: raw URL base prefix
- `tv`: tag version
- `ts`: tagging timestamp
- `qp`: query policy (`bilingual`)
- `nm`: no-match policy (`allow_zero`)
- `tm`: topic codebook (`tXX -> canonical_english_topic`)
- `om`: object codebook (`oXX -> canonical_english_object`)
- `im`: intent codebook (`nXX -> canonical_english_intent`)

### Line 2..N: group rows
- `i`: group id
- `p`: path array (`posts/*.png`)
- `s`: semantic code object
  - `t`: topic code array
  - `o`: object code array
  - `n`: intent code array

## Semantic Policy
- Canonical terms in codebooks are English.
- Query language is bilingual through alias normalization.
- `s.t`, `s.o`, `s.n` arrays must be sorted and unique.
- All codes in group rows must exist in config codebooks.

## Why grouped-sem-v1
- Removes repeated long keyword arrays.
- Merges paths sharing identical semantic code tuple.
- Keeps input tokens lower than per-image direct keyword storage.

## Update Procedure
1. Resolve target path.
2. Determine semantic tuple (`topic`, `object`, `intent`).
3. Convert terms to code arrays via config codebooks.
4. If a matching group exists, append path to that group `p`.
5. Otherwise create a new group with new `i`.
6. Keep config row as line 1.

## Validation Checklist
- Config row exists and is first.
- `f == grouped-sem-v1`.
- All paths are unique across all groups.
- Each group row has `i`, `p`, `s`.
- Each `s` has `t`, `o`, `n`.
- Every code in group rows resolves in `tm`, `om`, `im`.

## Operating Constraints
- No external APIs.
- No server execution.
- No automation-script dependency for daily operations.
