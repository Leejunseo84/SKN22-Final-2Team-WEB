import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "../services/fastapi/.env"))

class AgentSwerm:
    def __init__(self, model_name="gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.personas = self._load_personas()
        self.skills = self._load_skills()
        
    def _load_personas(self) -> Dict[str, str]:
        persona_dir = os.path.join(os.path.dirname(__file__), "personas")
        agents = ["health_agent", "review_critic", "budget_manager", "concierge"]
        personas = {}
        for agent in agents:
            path = os.path.join(persona_dir, f"{agent}.md")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    personas[agent] = f.read()
            else:
                personas[agent] = f"You are the {agent}. Stay in character."
        return personas

    def _load_skills(self) -> str:
        skill_dir = os.path.join(os.path.dirname(__file__), "skills")
        skills_text = "\n[Available Skills]\n"
        if os.path.exists(skill_dir):
            for file in os.listdir(skill_dir):
                if file.endswith(".md"):
                    with open(os.path.join(skill_dir, file), "r", encoding="utf-8") as f:
                        skills_text += f"\n--- {file} ---\n{f.read()}\n"
        return skills_text

    def _get_agent_response(self, agent_name: str, context: str, history: List[str], turn_limit: int = 3) -> str:
        prompt = f"""
        당신은 {agent_name}입니다.
        아래는 당신이 사용할 수 있는 스킬 목록과 현재 토론 정보입니다.
        
        {self.skills}

        [상품 정보]
        {context}
        
        [토론 내역]
        {"".join(history)}
        
        [지침]
        1. 위의 [Available Skills]를 참고하여 필요하다면 특정 스킬을 사용하겠다고 언급하며 의견을 제시하세요. (예: "Product Search 스킬로 확인해본 결과...")
        2. 다른 에이전트의 의견을 참고하여 자기 관점에서 의견을 제시하거나 반론하세요.
        3. 반드시 **최대 {turn_limit}줄 이내**로 짧고 강렬하게 답변하세요.
        4. 한국어로 답변하세요.
        """
        messages = [
            SystemMessage(content=self.personas.get(agent_name, "")),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return f"**{agent_name.replace('_', ' ').title()}**: {response.content}"

    def run_debate(self, products: List[Dict], pet_info: Dict, rounds: int = 3):
        product_list = []
        for p in products:
            reviews_text = ""
            if p.get('sample_reviews'):
                reviews_text = "\n[실제 리뷰 샘플]\n" + "\n".join([
                    f"- 평점 {r['score']}: {r['content'][:100]}... (기호성: {r['기호성']}, 배변: {r['소화/배변']})" 
                    for r in p['sample_reviews']
                ])
            
            p_text = f"- {p['goods_name']} (가격: {p['discount_price']}원, 평점: {p['rating']}, 성분: {p['main_ingredients']}){reviews_text}"
            product_list.append(p_text)
            
        product_context = "\n\n".join(product_list)
        
        context = f"반려동물 정보: {pet_info}\n제안된 상품들:\n{product_context}"
        debate_history = []
        
        # 전문가 리스트
        experts = ["health_agent", "review_critic", "budget_manager"]
        
        # 토론 라운드 진행
        for r in range(1, rounds + 1):
            round_header = f"\n### [Round {r}] 토론 진행\n"
            yield {"type": "header", "content": round_header}
            
            for expert in experts:
                response = self._get_agent_response(expert, context, debate_history)
                debate_history.append(f"{response}\n")
                yield {"type": "message", "agent": expert, "content": response}

        # 최종 의사결정 (Concierge)
        yield {"type": "header", "content": "\n### 🏆 최종 의사결정 (Lead Concierge)\n"}
        
        final_prompt = f"""
        토론이 종료되었습니다. 최종 의사결정자로서 결론을 내려주세요.
        
        [토론 최종 내역]
        {"".join(debate_history)}
        
        [결론 지침]
        1. 각 전문가의 핵심 포인트를 요약하세요.
        2. 상위 3개 상품 중 가장 추천하는 제품과 그 이유를 설명하세요.
        3. 유저에게 따뜻한 환영의 인사를 건네며 마무리하세요.
        """
        
        concierge_messages = [
            SystemMessage(content=self.personas.get("concierge", "")),
            HumanMessage(content=final_prompt)
        ]
        final_decision = self.llm.invoke(concierge_messages)
        yield {"type": "final", "content": final_decision.content}
