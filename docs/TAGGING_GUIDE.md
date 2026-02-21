# Tagging Guide

## 목적
- 기존 이미지 재사용률을 높이기 위해 태그/캡션 메타데이터를 관리한다.
- `metadata/image_tags.jsonl`를 단일 원본으로 유지한다.
- 운영은 문서+수동 절차만 사용한다.

## 데이터 계약
각 JSONL 레코드는 아래 키를 반드시 포함한다.

| key | type | rule |
|---|---|---|
| `path` | string | `posts/*.png` 경로 |
| `raw_url` | string | `https://raw.githubusercontent.com/sejinjja/blog-images/main/<path>` |
| `caption_ko` | string | 한국어 설명 |
| `caption_en` | string | 영어 설명 |
| `tags_ko` | array[string] | 한국어 태그 |
| `tags_en` | array[string] | 영어 태그 |
| `subject` | string | 핵심 대상 |
| `style` | string | 스타일 |
| `scene` | string | 장면/배경 |
| `mood` | string | 분위기 |
| `palette` | string | 색감/팔레트 |
| `tag_version` | string | 태깅 규칙 버전 |
| `tagged_at` | string | ISO8601 시각 |

## 운영 원칙
- 한/영 병기 태깅을 기본으로 한다.
- 같은 의미를 과도하게 중복 태깅하지 않는다.
- 추측 기반 태깅을 피하고 불명확하면 보수적으로 기록한다.
- API/서버/자동화 스크립트는 사용하지 않는다.

## 전수 태깅 절차 (기존 550장)
1. 배치 단위를 정한다. 기본 50장.
2. 배치 대상 `path` 목록을 확정한다.
3. Codex에게 배치 태깅 요청 템플릿으로 지시한다.
4. `metadata/image_tags.jsonl`의 해당 레코드를 갱신한다.
5. 필수 키 누락/중복 path를 점검한다.
6. 검수 대상 샘플에 반영한다.

### 배치 태깅 요청 템플릿
```text
다음 path 목록을 태깅해주세요.
조건:
- metadata/image_tags.jsonl 계약 키만 사용
- caption/tags는 한/영 병기
- 불확실한 항목은 보수적으로 작성
- 기존 path/raw_url은 변경하지 않음
결과:
- 해당 레코드만 갱신
- 변경 요약 + 검증결과 보고
```

## 신규 이미지 태깅 절차
1. 새 이미지가 `posts/`에 추가되면 같은 작업 흐름에서 레코드 1건을 추가한다.
2. `path`와 `raw_url`을 우선 확정한다.
3. 캡션/태그를 한/영 병기로 작성한다.
4. 저장 후 중복 path와 필수 키 누락을 확인한다.

## 검수 절차
- 샘플 기준: 랜덤 50 + 유사군 20
- 검수 기록 파일: `metadata/review_samples.md`

검수 체크:
- 캡션 정확성
- 태그 일관성
- 한/영 대응 정확성
- 재사용 검색 적합성

## 완료 보고 형식
항상 아래 형식으로 보고한다.
1. 요약
2. 변경파일
3. 검증결과
