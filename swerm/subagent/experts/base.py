import os
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

class ExpertAgent:
    def __init__(self, name: str, persona_path: str, model_name: str = "gpt-4o"):
        self.name = name
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.persona = self._load_persona(persona_path)

    def _load_persona(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return f"You are the {self.name}. Stay in character."

    def think_and_talk(self, context: str, history: List[str], turn_limit: int = 3) -> str:
        prompt = f"""
        당신은 {self.name} 서브에이전트입니다.
        
        [상품 및 반려동물 정보]
        {context}
        
        [현재까지의 토론 기록]
        {"".join(history)}
        
        [지침]
        1. 본인의 전문 분야에 집중하여 의견을 제시하거나 다른 에이전트의 주장에 반론하세요.
        2. 답변은 반드시 **{turn_limit}줄 이내**로 핵심만 전달하세요.
        3. 한국어로 답변하세요.
        """
        messages = [
            SystemMessage(content=self.persona),
            HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        return f"**{self.name.replace('_', ' ').title()}**: {response.content}"
