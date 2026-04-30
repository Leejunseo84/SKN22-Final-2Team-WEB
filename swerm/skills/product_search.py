from .base import BaseSkill
from db_helper import fetch_top_products
from typing import Optional

class ProductSearchSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "product_search"

    @property
    def description(self) -> str:
        return "반려동물의 정보와 검색어를 바탕으로 최적의 상품 5개를 검색합니다. 입력: query(검색어), pet_type('dog' 또는 'cat')"

    def run(self, query: str, pet_type: Optional[str] = None) -> list:
        """
        DB에서 상품 정보를 검색하여 리스트로 반환합니다.
        """
        try:
            return fetch_top_products(query, pet_type, limit=5)
        except Exception as e:
            return f"Error searching products: {str(e)}"
