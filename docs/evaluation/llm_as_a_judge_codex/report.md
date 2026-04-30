# Codex Evaluation Report

## Summary
- total_cases: 93
- passed_cases: 2
- failed_cases: 91

## Cases
| case_id | passed | route | search_query | reranked_overlap | error |
| --- | --- | --- | --- | --- | --- |
| case_001_no_profile_A | FAIL | query | 강아지 사료 | 100.0 |  |
| case_001_no_profile_B | FAIL | query | 강아지 간식 | 100.0 |  |
| case_001_with_profile | FAIL | profile | 강아지 말티즈 사료 | 80.0 |  |
| case_002_no_profile | FAIL | query | 강아지 사료 | 20.0 |  |
| case_002_with_profile | PASS | profile | 강아지 포메라니안 사료 | 100.0 |  |
| case_003_with_profile | FAIL | profile | 강아지 사료 피부 헤어볼 | 0.0 |  |
| case_004_with_profile | FAIL | profile | 강아지 골든 리트리버 사료 | 0.0 |  |
| case_003_with_profile | FAIL | profile | 강아지 사료 피부 헤어볼 건강 | 0.0 |  |
| case_004_no_profile_A | FAIL | profile | 강아지 골든 리트리버 사료 퍼피 | 0.0 |  |
| case_004_no_profile_B | FAIL | profile | 강아지 골든 리트리버 간식 | 0.0 |  |
| case_004_with_profile_A | PASS | profile | 강아지 말티즈 사료 | 100.0 |  |
| case_004_with_profile_B | FAIL | profile | 강아지 말티즈 간식 | 100.0 |  |
| case_005_no_profile_A | FAIL | profile | 강아지 사료 피부 헤어볼 건강 | 20.0 |  |
| case_005_no_profile_B | FAIL | profile | 강아지 간식 | 0.0 |  |
| case_005_with_profile_A | FAIL | profile | 강아지 말티즈 사료 피부 헤어볼 건강 | 0.0 |  |
| case_005_with_profile_B | FAIL | profile | 강아지 말티즈 간식 | 0.0 |  |
| case_006_no_profile_A | FAIL | profile | 강아지 골든 리트리버 용품 장난감 | 20.0 |  |
| case_006_no_profile_B | FAIL | profile | 면으로 된걸로 보여줘 강아지 골든 리트리버 용품 장난감 | 20.0 |  |
| case_006_with_profile_A | FAIL | profile | 강아지 말티즈 용품 장난감 | 20.0 |  |
| case_006_with_profile_B | FAIL | profile | 강아지 말티즈 용품 장난감 | 20.0 |  |
| case_007_no_profile | FAIL | profile | 강아지 말티즈 용품 | 0.0 |  |
| case_007_with_profile | FAIL | profile | 고양이 러시안 블루 모래 | 60.0 |  |
| case_008_no_profile_A | FAIL | profile | 강아지 말티즈 사료 퍼피 | 0.0 |  |
| case_008_no_profile_B | FAIL | profile | 강아지 말티즈 사료 퍼피 | 0.0 |  |
| case_008_no_profile_C | FAIL | profile | 강아지 말티즈 간식 | 0.0 |  |
| case_008_with_profile_A | FAIL | profile | 강아지 말티즈 사료 퍼피 | 0.0 |  |
| case_008_with_profile_B | FAIL | profile | 강아지 말티즈 간식 | 0.0 |  |
| case_008_with_profile_C | FAIL | profile | 강아지 말티즈 용품 | 20.0 |  |
| case_009_no_profile_A | FAIL | clarify |  | None |  |
| case_009_no_profile_B | FAIL | clarify |  | None |  |
| case_009_with_profile_A | FAIL | clarify |  | None |  |
| case_009_with_profile_B | FAIL | clarify |  | None |  |
| case_010_no_profile_A | FAIL | profile | 강아지 말티즈 사료 퍼피 | 0.0 |  |
| case_010_no_profile_B | FAIL | profile | 고양이 말티즈 사료 퍼피 | None |  |
| case_010_no_profile_C | FAIL | profile | 고양이 말티즈 사료 퍼피 | 20.0 |  |
| case_010_with_profile_A | FAIL | profile | 강아지 말티즈 사료 퍼피 | 0.0 |  |
| case_010_with_profile_B | FAIL | profile | 아니 바나나 꺼 보여줘 고양이 러시안 블루 사료 피부 헤어볼 건강 | None |  |
| case_010_with_profile_C | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_011_no_profile_A | FAIL | profile | 고양이 러시안 블루 사료 키튼 | None |  |
| case_011_no_profile_B | FAIL | profile | 강아지 러시안 블루 사료 키튼 | 0.0 |  |
| case_011_with_profile | FAIL | profile | 고양이 사료 | 0.0 |  |
| case_012_no_profile_A | FAIL | profile | 고양이 러시안 블루 간식 | None |  |
| case_012_no_profile_B | FAIL | profile | 강아지 러시안 블루 간식 | 0.0 |  |
| case_012_with_profile | FAIL | profile | 고양이 러시안 블루 간식 | 40.0 |  |
| case_013_no_profile | FAIL | profile | 제일 싼 고양이 모래 보여줘 고양이 러시안 블루 모래 벤토나이트 | 60.0 |  |
| case_013_with_profile | FAIL | profile | 그중에서 제일 저렴한 거로 알려줘 고양이 러시안 블루 모래 벤토나이트 | 60.0 |  |
| case_014_no_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_001_no_profile_A | FAIL | profile | 고양이 사료 | 40.0 |  |
| case_001_no_profile_B | FAIL | profile | 고양이 러시안 블루 간식 | 0.0 |  |
| case_001_with_profile | FAIL | profile | 고양이 말티즈 사료 퍼피 | 0.0 |  |
| case_002_no_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_002_with_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_003_with_profile | FAIL | profile | 강아지 포메라니안 사료 | 0.0 |  |
| case_004_with_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_003_with_profile | FAIL | profile | 강아지 포메라니안 사료 | 0.0 |  |
| case_004_no_profile_A | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 80.0 |  |
| case_004_no_profile_B | FAIL | profile | 고양이 러시안 블루 간식 | 20.0 |  |
| case_004_with_profile_A | FAIL | profile | 고양이 아비시니안 사료 | 0.0 |  |
| case_004_with_profile_B | FAIL | profile | 고양이 아비시니안 간식 | None |  |
| case_005_no_profile_A | FAIL | profile | 고양이 사료 | 40.0 |  |
| case_005_no_profile_B | FAIL | profile | 강아지 포메라니안 간식 | 0.0 |  |
| case_005_with_profile_A | FAIL | profile | 강아지 포메라니안 사료 퍼피 | 0.0 |  |
| case_005_with_profile_B | FAIL | profile | 강아지 용품 | 0.0 |  |
| case_006_no_profile_A | FAIL | profile | 고양이 러시안 블루 용품 장난감 | 0.0 |  |
| case_006_no_profile_B | FAIL | profile | 면으로 된걸로 보여줘 고양이 러시안 블루 용품 장난감 | 20.0 |  |
| case_006_with_profile_A | FAIL | profile | 고양이 러시안 블루 용품 장난감 | 0.0 |  |
| case_006_with_profile_B | FAIL | profile | 고양이 러시안 블루 용품 장난감 | 40.0 |  |
| case_007_no_profile | FAIL | profile | 고양이 아비시니안 용품 치아 | 0.0 |  |
| case_007_with_profile | FAIL | profile | 강아지 포메라니안 용품 배변패드 | None |  |
| case_008_no_profile_A | FAIL | profile | 고양이 사료 | 40.0 |  |
| case_008_no_profile_B | FAIL | profile | 강아지 간식 | 0.0 |  |
| case_008_no_profile_C | FAIL | profile | 강아지 간식 | 0.0 |  |
| case_008_with_profile_A | FAIL | profile | 고양이 아비시니안 사료 | 0.0 |  |
| case_008_with_profile_B | FAIL | profile | 고양이 아비시니안 간식 | None |  |
| case_008_with_profile_C | FAIL | profile | 고양이 아비시니안 용품 치아 | 20.0 |  |
| case_009_no_profile_A | FAIL | clarify |  | None |  |
| case_009_no_profile_B | FAIL | clarify |  | None |  |
| case_009_with_profile_A | FAIL | clarify |  | None |  |
| case_009_with_profile_B | FAIL | clarify |  | None |  |
| case_010_no_profile_A | FAIL | profile | 고양이 아비시니안 사료 키튼 | 20.0 |  |
| case_010_no_profile_B | FAIL | profile | 고양이 아비시니안 사료 키튼 | None |  |
| case_010_no_profile_C | FAIL | clarify |  | 0.0 |  |
| case_010_with_profile_A | FAIL | profile | 고양이 아비시니안 사료 | 0.0 |  |
| case_010_with_profile_B | FAIL | profile | 고양이 아비시니안 사료 | None |  |
| case_010_with_profile_C | FAIL | profile | 고양이 러시안 블루 사료 | 40.0 |  |
| case_011_no_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_011_with_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 0.0 |  |
| case_012_no_profile_A | FAIL | profile | 고양이 러시안 블루 간식 | None |  |
| case_012_no_profile_B | FAIL | profile | 고양이 러시안 블루 간식 | 20.0 |  |
| case_012_with_profile | FAIL | profile | 고양이 러시안 블루 간식 | None |  |
| case_013_no_profile | FAIL | profile | 제일 싼 강아지 패드 보여줘 강아지 러시안 블루 배변용품 | 20.0 |  |
| case_013_with_profile | FAIL | profile | 그중에서 제일 저렴한 거로 알려줘 고양이 러시안 블루 배변용품 | None |  |
| case_014_no_profile | FAIL | profile | 고양이 러시안 블루 사료 키튼 | 20.0 |  |
