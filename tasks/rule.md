# Daily Rule (Single Control File)

## Fixed Instruction
`tasks/rule.md를 보고 작업을 진행해주세요.`

## Goal
- Operate this repository for image reuse only.
- Use semantic words only (topic/object/intent).
- Keep token cost low with codebook-based metadata.

## Scope
Included:
- Reuse search on existing images
- Semantic metadata maintenance in `metadata/image_tags.jsonl`
- Query alias maintenance in `metadata/query_alias.json`
- Guide maintenance in `docs/`

Excluded:
- New image generation
- Any external API usage
- Any server execution
- Automation-script dependency for daily operations

## Required Report Format
1. Summary
2. Changed files
3. Verification results

## Metadata Format Policy
- File: `metadata/image_tags.jsonl`
- Format: `grouped-sem-v1`
- Config keys: `_`, `f`, `b`, `tv`, `ts`, `qp`, `nm`, `tm`, `om`, `im`
- Group keys: `i`, `p`, `s`
- Semantic code object in `s`: `t`, `o`, `n`
- `raw_url` is derived at read time: `cfg.b + path`

## Query Alias Policy
- File: `metadata/query_alias.json`
- Version key: `v = sem-alias-v1`
- Buckets: `t`, `o`, `n`
- Query mapping order:
1. phrase-first (`2-gram`)
2. unigram

## Reuse Search Contract
- Two modes are allowed:
1. `match`: return 2 to 3 candidates
2. `no_match`: return 0 candidates with explicit reason

- Candidate fields:
- `raw_url`
- `match_reason`
- `confidence_note`

- No-match fields:
- `query`
- `mode` = `no_match`
- `result_count` = `0`
- `no_match_reason`

## Result Diversity Rule
- Do not return duplicate images in one response.
- Selection order for diversity:
1. one path per group first
2. then fill remaining slots from next-ranked groups
- If identical binary duplicates are detected, keep only one canonical path in the same response.

## Scoring and Gate Rules
- Normalize query to code sets `Q.t`, `Q.o`, `Q.n`.
- Hard gate:
- if all sets are empty -> `no_match` (`unmapped_query_terms`)
- if `Q.o` is non-empty, group must overlap in `s.o`
- if `Q.t` is non-empty, group must overlap in `s.t`
- `Q.n` is optional boost
- Score:
- `3 * |Q.o ∩ G.o| + 2 * |Q.t ∩ G.t| + 1 * |Q.n ∩ G.n|`
- Sort:
- score desc, then `group_id` asc, then `path` asc

## Hard Restrictions
- No external APIs (vision/embedding/search APIs included).
- No local/remote server execution.
- No automation-script dependency for daily operations.

## Reference Docs
- `docs/NO_API_POLICY.md`
- `docs/TAGGING_GUIDE.md`
- `docs/REUSE_SEARCH_GUIDE.md`
