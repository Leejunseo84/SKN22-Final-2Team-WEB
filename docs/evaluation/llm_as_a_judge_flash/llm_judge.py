import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMJudge:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def judge_query(self, user_input: str, expected_query: str, actual_query: str) -> dict:
        """골든 쿼리와 시스템 쿼리의 의도적 동일성을 판정합니다."""
        prompt = f"""
        당신은 AI 검색 엔진의 성능 평가 전문가입니다.
        사용자의 입력과 '골든(정답) 검색 쿼리', 그리고 시스템이 생성한 '실제 검색 쿼리'를 비교하여, 
        시스템 쿼리가 사용자 의도를 충분히 반영하고 골든 쿼리와 실질적으로 동일한 검색 의도를 가졌는지 평가하세요.

        [사용자 입력]: {user_input}
        [골든 쿼리]: {expected_query}
        [실제 쿼리]: {actual_query}

        평가 기준:
        1. 핵심 키워드(펫 종류, 카테고리, 특정 요구사항 등)가 포함되었는가?
        2. 조사나 단어 순서가 다르더라도 검색 결과가 유사할 것으로 판단되는가?
        3. 골든 쿼리보다 더 나은 의도 파악이 이루어졌는가? (이 경우에도 높은 점수 부여)

        결과는 반드시 다음 JSON 형식으로만 응답하세요:
        {{
            "score": 0.0 ~ 1.0 (실질적 동일성 점수),
            "reasoning": "평가 사유 (한국어)"
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"score": 0, "reasoning": f"Error: {str(e)}"}

    def judge_response(self, user_input: str, expected_keywords: list, actual_response: str) -> dict:
        """응답의 자연스러움과 키워드 포함 적절성을 판정합니다."""
        prompt = f"""
        당신은 펫 상품 추천 서비스의 QA 담당자입니다.
        시스템의 응답이 사용자의 질문에 적절하며, 필수 키워드를 문맥에 맞게 잘 포함했는지 평가하세요.

        [사용자 입력]: {user_input}
        [필수 포함 키워드]: {", ".join(expected_keywords)}
        [시스템 응답]: {actual_response}

        평가 기준:
        1. 필수 키워드가 문맥 속에 자연스럽게 녹아있는가?
        2. 말투가 친절하고 펫 주인에게 유용한 정보를 제공하는가?
        3. 할루시네이션(잘못된 정보 제공)이 의심되는 부분이 있는가?

        결과는 반드시 다음 JSON 형식으로만 응답하세요:
        {{
            "score": 0.0 ~ 1.0 (정성적 품질 점수),
            "keyword_match": true/false (정말 키워드가 다 들어있는가),
            "reasoning": "평가 사유 (한국어)"
        }}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"score": 0, "keyword_match": False, "reasoning": f"Error: {str(e)}"}
