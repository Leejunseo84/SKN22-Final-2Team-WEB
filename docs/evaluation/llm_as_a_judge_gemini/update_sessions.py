import json
import uuid
import re

file_path = "docs/evaluation/llm_as_a_judge_gemini/ai_logic_golden_dataset.json"

def update_session_ids():
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 그룹별 세션 ID를 저장할 딕셔너리
    session_map = {}

    for i, case in enumerate(data):
        case_id = case.get("id", "")
        if not case_id:
            continue
            
        # [핵심 수정] 전반부(0~45)와 후반부(46~)를 구분하여 세션 키 생성
        # 사용자의 4209줄(고양이 시작점) 요청에 따라 인덱스 기반 파티셔닝
        part_prefix = "dog_part_" if i < 46 else "cat_part_"
        
        # 그룹 키 추출 (예: case_001_no_profile_A -> case_001_no_profile)
        group_key = part_prefix + re.sub(r'_[A-Z]$', '', case_id)
        
        # 새로운 세션 ID 할당
        if group_key not in session_map:
            session_map[group_key] = str(uuid.uuid4())
            
        # 세션 ID 업데이트
        if "input" in case:
            case["input"]["session_id"] = session_map[group_key]

    # 파일에 다시 쓰기
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully updated session IDs for {len(data)} cases.")
    print(f"Total Unique Sessions Created: {len(session_map)}")

if __name__ == "__main__":
    update_session_ids()
