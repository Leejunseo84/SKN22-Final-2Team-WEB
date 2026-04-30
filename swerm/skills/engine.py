import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "../../services/fastapi/.env"))

class AgentSwerm:
    def __init__(self, model_name="gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.skills = self._load_skills()
        
    def _load_skills(self) -> str:
        skill_dir = os.path.dirname(__file__)
        skills_text = "\n[Available Skills/Criteria]\n"
        if os.path.exists(skill_dir):
            for file in os.listdir(skill_dir):
                if file.endswith(".md"):
                    with open(os.path.join(skill_dir, file), "r", encoding="utf-8") as f:
                        skills_text += f"\n--- {file} ---\n{f.read()}\n"
        return skills_text

    def _get_committee_response(self, role: str, assigned_product: str, context: str, history: List[str]) -> str:
        prompt = f"""
        당신은 반려동물 상품 추천 전문가 위원회의 일원인 '{role}'입니다.
        당신은 아래의 종합 분석 가이드를 완벽히 숙지하고 있습니다.
        
        {self.skills}

        [당신의 특별 임무]
        당신은 이번 토론에서 아래의 상품을 전담하여 수호하고 어필해야 합니다:
        >> **전담 상품: {assigned_product}** <<

        [현재 전체 후보 상품 정보]
        {context}
        
        [위원회 토론 내역]
        {"".join(history)}
        
        [지침]
        1. 당신의 전담 상품({assigned_product})이 왜 최적의 선택인지 모든 스킬(안전성, 기호성, 영양, 건강, 가성비)을 동원해 어필하세요.
        2. 다른 전문가가 맡은 상품의 약점을 찾아 날카롭게 비판하고, 왜 당신의 상품이 더 나은지 증명하세요.
        3. 상대방의 비판이 들어오면 논리적으로 방어하세요.
        4. 반드시 **최대 4줄 이내**로 강렬하고 설득력 있게 답변하세요.
        5. 한국어로 답변하세요.
        """
        messages = [
            SystemMessage(content=f"You are a fiercely protective advocate for '{assigned_product}' in a professional expert panel."),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return f"**{role}**: {response.content}"

    def run_debate(self, products: List[Dict], pet_info: Dict, rounds: int = 1):
        product_list = []
        for i, p in enumerate(products):
            p_text = f"상품 {i+1}: {p['goods_name']} (가격: {p['discount_price']}원, 평점: {p['rating']}, 성분: {p['main_ingredients']})"
            product_list.append(p_text)
            
        product_context = "\n\n".join(product_list)
        context = f"반려동물 정보: {pet_info}\n제안된 상품들:\n{product_context}"
        debate_history = []
        
        # 전문가 역할 정의
        roles = [
            "안전성 수호자 (Safety)", 
            "기호성 가디언 (Palatability)", 
            "영양 전략가 (Nutrition)", 
            "건강 마스터 (Health)", 
            "가성비 위원 (Economics)"
        ]
        
        # 상품과 역할 매칭 (상품이 5개 미만인 경우 순환 매칭)
        role_product_map = {}
        for i, role in enumerate(roles):
            assigned_p = products[i % len(products)]['goods_name']
            role_product_map[role] = assigned_p

        # 통합 토론 진행
        header = f"\n### 🏛️ 상품 전담 마크 전문가 토론\n"
        yield {"type": "header", "content": header}
        
        for role in roles:
            assigned_p = role_product_map[role]
            response = self._get_committee_response(role, assigned_p, context, debate_history)
            debate_history.append(f"{response}\n")
            
            # 역할별 고유 키 매핑 (UI 아이콘용)
            if "Safety" in role: agent_key = "safety_expert"
            elif "Palatability" in role: agent_key = "palatability_expert"
            elif "Nutrition" in role: agent_key = "nutrition_expert"
            elif "Health" in role: agent_key = "health_expert"
            else: agent_key = "economics_expert"
            
            yield {"type": "message", "agent": agent_key, "content": response}

        # 최종 권고
        yield {"type": "header", "content": "\n### 🏆 전문가 위원회 최종 의결\n"}
        
        final_prompt = f"""
        각 전문가들의 치열한 전담 상품 어필과 상호 비판이 끝났습니다.
        중립적인 입장에서 모든 토론 내용을 종합하여 반려동물에게 가장 적합한 최종 1위 상품을 선정하세요.
        
        [토론 내역]
        {"".join(debate_history)}
        
        [최종 가이드]
        1. 토론에서 가장 논리적이고 설득력이 높았던 포인트를 짚어주세요.
        2. 최종 1등 상품과 그 결정적인 이유(모든 지표 종합)를 설명하세요.
        3. 2등 상품에 대해서도 짧게 언급하며 어떤 경우에 대안이 될 수 있는지 덧붙이세요.
        4. 한국어로 답변하세요.
        """
        
        final_decision = self.llm.invoke([HumanMessage(content=final_prompt)])
        yield {"type": "final", "content": final_decision.content}
