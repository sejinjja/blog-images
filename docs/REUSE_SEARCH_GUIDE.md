# Reuse Search Guide

## 목적
- 특정 이미지를 가장 적은 비용으로 찾아 재사용한다.
- 외부 API 없이 저장소의 기존 메타데이터만 사용한다.
- 결과는 최소 2개, 기본 3개 후보를 제공한다.

## 금지사항
- 비전 API, 임베딩 API, 외부 검색 API 사용 금지
- 서버 실행 금지
- 자동화 스크립트 운영 금지

## 입력 유형
- `raw_url`
- `path` 또는 파일명
- 텍스트 설명(한글/영문)

## 탐색 순서 (비용 최소 우선)
1. 정확 일치 탐색
- `raw_url` 또는 `path`가 정확히 일치하는 레코드를 먼저 찾는다.

2. 태그/캡션 유사 탐색
- `caption_ko`, `caption_en`, `tags_ko`, `tags_en`, `subject`, `style`, `scene`를 기준으로 유사 후보를 찾는다.
- 텍스트 일치 근거를 명시한다.

3. 후보 부족 시 수동 확장 1회
- 동의어/유사 표현으로 검색을 1회 확장한다.
- 그래도 후보가 부족하면 부족 사유를 보고한다.

## 출력 계약
- 최소 2개, 기본 3개 후보
- 각 후보는 아래 3개 필드를 반드시 포함
- `raw_url`
- `match_reason`
- `confidence_note`

## 출력 템플릿
```text
query: <사용자 질의>
result_count: <N>

1) raw_url: <url>
   match_reason: <매칭 근거>
   confidence_note: <신뢰도/주의사항>

2) raw_url: <url>
   match_reason: <매칭 근거>
   confidence_note: <신뢰도/주의사항>
```

## 운영 기준
- 결과가 2개 미만이면 그 이유를 명확히 기록한다.
- 후보 제시 시 중복 URL을 제거한다.
- 신규 생성 관여는 하지 않고 재사용 탐색에만 집중한다.
