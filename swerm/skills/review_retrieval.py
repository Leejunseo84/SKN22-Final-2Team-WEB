from .base import BaseSkill
from db_helper import fetch_sample_reviews

class ReviewRetrievalSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "get_reviews"

    @property
    def description(self) -> str:
        return "특정 상품 ID를 바탕으로 최신 고객 리뷰 샘플을 가져옵니다. 입력: goods_id(상품 ID), limit(가져올 리뷰 개수, 기본 3개)"

    def run(self, goods_id: int, limit: int = 3) -> list:
        """
        특정 상품의 리뷰를 가져옵니다.
        """
        try:
            return fetch_sample_reviews(goods_id, limit)
        except Exception as e:
            return f"Error fetching reviews: {str(e)}"
