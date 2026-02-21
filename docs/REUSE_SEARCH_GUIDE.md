# Reuse Search Guide

## Purpose
- Find reusable images with semantic relevance and low token cost.
- Use only local static metadata.
- Avoid forced or low-confidence matches.

## Inputs
- `raw_url`
- `path` or filename
- Korean or English semantic query

## Metadata Dependency
- Source files:
- `metadata/image_tags.jsonl`
- `metadata/query_alias.json`
- Expected format: `grouped-sem-v1`
- `raw_url` derivation: `cfg.b + path`

## Query Normalization (Bilingual)
Normalize query words to semantic code sets before scoring.

Order:
1. lowercase + trim + punctuation cleanup
2. phrase-first (`2-gram`) alias lookup
3. unigram alias lookup
4. build `Q.t`, `Q.o`, `Q.n`

Examples:
- Korean:
- `요리` -> `Q.t += food`
- `빵 요리` -> `Q.o += bread`, `Q.t += food`
- `정장 인물` -> `Q.o += suit/person`
- English:
- `cooking` -> `Q.t += food`
- `bread cooking` -> `Q.o += bread`, `Q.t += food`
- `fashion portrait` -> `Q.t += fashion`, `Q.n += portrait_editorial`

## Search Order
1. Exact path/url match
- If input is `raw_url`, strip base prefix and match path in group `p`.
- If input is `path` or filename, exact-match path in group `p`.

2. Semantic overlap gate
- If all of `Q.t`, `Q.o`, `Q.n` are empty -> `mode=no_match` (`unmapped_query_terms`).
- If `Q.o` is non-empty, group must overlap in `s.o`.
- If `Q.t` is non-empty, group must overlap in `s.t`.
- `Q.n` is optional boost only.

3. Scoring
- `score = 3 * |Q.o ∩ G.o| + 2 * |Q.t ∩ G.t| + 1 * |Q.n ∩ G.n|`
- Rank by `score desc`, then `group_id asc`, then `path asc`.

4. Diversity filter
- Select at most one path from each group in the first pass.
- Exclude exact binary duplicates in the same response.

5. Result shaping
- If qualified unique candidates >= 2: `mode=match`, return 2 to 3.
- If qualified unique candidates < 2: `mode=no_match`.

## Output Contract
### `match` mode
- `query`
- `mode`: `match`
- `result_count`: `2` to `3`
- `results[]`:
- `raw_url`
- `match_reason`
- `confidence_note`

### `no_match` mode
- `query`
- `mode`: `no_match`
- `result_count`: `0`
- `no_match_reason`

## Restrictions
- No external APIs.
- No server execution.
- No automation-script dependency for daily operations.
