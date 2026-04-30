import os
import re
from typing import List, Dict, Generator
from .experts.base import ExpertAgent
from .database import DatabaseHandler

class SwarmSubAgent:
    def __init__(self):
        self.db = DatabaseHandler()
        current_dir = os.path.dirname(__file__)
        
        self.experts = {
            "health_agent": ExpertAgent("health_agent", os.path.join(current_dir, "health_agent.md")),
            "review_critic": ExpertAgent("review_critic", os.path.join(current_dir, "review_critic.md")),
            "budget_manager": ExpertAgent("budget_manager", os.path.join(current_dir, "budget_manager.md")),
            "search_strategist": ExpertAgent("search_strategist", os.path.join(current_dir, "search_strategist.md")),
            "concierge": ExpertAgent("concierge", os.path.join(current_dir, "concierge.md"))
        }

    def _prepare_context(self, products: List[Dict], pet_info: Dict) -> str:
        product_list = []
        for p in products:
            reviews_text = ""
            if p.get('sample_reviews'):
                reviews_text = "\n[실제 리뷰]\n" + "\n".join([
                    f"- {r['content'][:50]} (기호성: {r['기호성']})" for r in p['sample_reviews']
                ])
            p_text = f"- {p['goods_name']} ({p['discount_price']}원): {p['main_ingredients']}{reviews_text}"
            product_list.append(p_text)
            
        return f"펫 정보: {pet_info}\n현재 상품 후보:\n" + "\n\n".join(product_list)

    def _run_discussion_phase(self, products: List[Dict], pet_info: Dict, history: List[str], phase_name: str) -> Generator[Dict, None, None]:
        """지정된 상품들로 3라운드 토론을 진행합니다."""
        yield {"type": "header", "content": f"🚀 [Phase: {phase_name}] 전문가 토론 시작"}
        context = self._prepare_context(products, pet_info)
        
        round_emojis = ["❶", "❷", "❸"]
        for r in range(1, 4):
            emoji = round_emojis[r-1]
            yield {"type": "header", "content": f"{emoji} Round {r}: 전문가 상호 비판 토론"}
            for name in ["health_agent", "review_critic", "budget_manager"]:
                agent = self.experts[name]
                response = agent.think_and_talk(context, history)
                history.append(f"{response}\n")
                yield {"type": "message", "agent": name, "content": response}

    def run_collaboration(self, query: str, pet_info: Dict) -> Generator[Dict, None, None]:
        current_query = query
        total_history = []
        
        # --- PHASE 1: 최초 검색 및 토론 ---
        products = self.db.fetch_top_3_products(current_query, pet_type=pet_info.get("species"))
        if not products:
            yield {"type": "error", "content": "상품을 찾을 수 없습니다."}
            return
        yield {"type": "products", "content": products}
        
        yield from self._run_discussion_phase(products, pet_info, total_history, "1차 분석")

        # --- EVALUATION: 컨시어지의 1차 평가 ---
        yield {"type": "header", "content": "🎩 컨시어지 1차 평가 중..."}
        eval_context = self._prepare_context(products, pet_info)
        eval_response = self.experts["concierge"].think_and_talk(eval_context, total_history)
        yield {"type": "message", "agent": "concierge", "content": eval_response}

        # 재검색 여부 확인
        if "[RE-SEARCH]" in eval_response:
            yield {"type": "header", "content": "🔄 조건 부적합 판정: 재검색 전략 수립 중..."}
            
            # 검색 전략가 호출하여 새로운 쿼리 생성
            strat_response = self.experts["search_strategist"].think_and_talk(eval_context, total_history)
            yield {"type": "message", "agent": "search_strategist", "content": strat_response}
            
            new_query_match = re.search(r"\[RE-SEARCH:\s*(.+?)\]", strat_response)
            if new_query_match:
                new_query = new_query_match.group(1).strip()
                yield {"type": "header", "content": f"✨ 새로운 조건으로 재검색: '{new_query}'"}
                
                # --- PHASE 2: 새로운 상품으로 재토론 ---
                new_products = self.db.fetch_top_3_products(new_query, pet_type=pet_info.get("species"))
                if new_products:
                    products = new_products
                    yield {"type": "products", "content": products}
                    total_history.append(f"\n[시스템 알림]: '{new_query}'로 재검색된 새로운 상품들로 2차 토론을 시작합니다.\n")
                    
                    # 다시 3라운드 토론 진행
                    yield from self._run_discussion_phase(products, pet_info, total_history, "2차 정밀 분석")
                else:
                    yield {"type": "error", "content": f"'{new_query}'에 해당하는 추가 상품이 없습니다."}

        # --- FINAL DECISION: 최종 결론 ---
        yield {"type": "header", "content": "🏆 최종 의사결정"}
        final_context = self._prepare_context(products, pet_info)
        final_decision = self.experts["concierge"].think_and_talk(final_context, total_history, turn_limit=15)
        yield {"type": "final", "content": final_decision}
