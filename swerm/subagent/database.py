import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "../../services/fastapi/.env"))

# 프로젝트 메인 로직에서 사용하는 건강 고민 매핑 사전
HEALTH_CONCERN_MAP = {
    "다이어트": ["체중", "살", "비만", "체중조절", "저칼로리", "슬림"],
    "눈물": ["눈물자국", "눈건강", "눈세정", "아이케어"],
    "피부": ["아토피", "가려움", "알러지", "피부염", "피부건강", "피부/모질"],
    "관절": ["슬개골", "뼈", "관절건강", "다리", "튼튼"],
    "소화": ["장", "변비", "설사", "소화불량", "위건강", "소화/장"],
}

class DatabaseHandler:
    @staticmethod
    def get_db_connection():
        host = (os.getenv("POSTGRES_HOST") or "localhost").strip() or "localhost"
        try:
            return psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "tailtalk_db"),
                user=os.getenv("POSTGRES_USER", "mungnyang"),
                password=os.getenv("POSTGRES_PASSWORD", "finalprojectljs1908"),
                host=host,
                port=os.getenv("POSTGRES_PORT", "5432"),
            )
        except Exception as e:
            raise ConnectionError(f"DB Connection Error: {e}")

    def fetch_top_3_products(self, query, pet_type=None):
        conn = self.get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. 필터 조건 (실험실 환경이므로 soldout 제한 해제하여 결과 보장)
        filters = ["goods_name NOT ILIKE '%%샘플%%'"]
        params = []
        
        # 2. 검색어 처리
        if query:
            words = query.split()
            for word in words:
                expanded_keywords = [word]
                for key, synonyms in HEALTH_CONCERN_MAP.items():
                    if key in word or any(s in word for s in synonyms):
                        expanded_keywords.extend(synonyms)
                
                sub_filters = []
                for kw in set(expanded_keywords):
                    sub_filters.append("(goods_name ILIKE %s OR brand_name ILIKE %s OR ARRAY_TO_STRING(health_concern_tags, ' ') ILIKE %s)")
                    params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
                filters.append(f"({' OR '.join(sub_filters)})")
        
        # 3. 펫 타입 (있을 때만 필터링)
        if pet_type:
            # DB 형태에 따라 다를 수 있으므로 조금 더 유연하게 매칭
            filters.append("(%s = ANY(pet_type) OR goods_name ILIKE %s)")
            params.extend([pet_type, f"%{pet_type}%"])

        sql = f"""
            SELECT 
                goods_id, goods_name, brand_name, price, discount_price, 
                rating, review_count, sentiment_avg, repeat_rate,
                main_ingredients, health_concern_tags, popularity_score
            FROM product 
            WHERE {" AND ".join(filters)}
            ORDER BY popularity_score DESC NULLS LAST, review_count DESC NULLS LAST
            LIMIT 3
        """
        
        cur.execute(sql, params)
        products = cur.fetchall()
        
        # 4. 만약 검색 결과가 없으면 종류 필터를 빼고 다시 시도 (Fallback)
        if not products and pet_type:
            # pet_type 필터(마지막 조건)를 제거하고 재검색
            filters.pop()
            # 펫 타입 관련 파라미터 2개 제거
            params = params[:-2]
            sql_fallback = f"SELECT goods_id, goods_name, brand_name, price, discount_price, rating, review_count, sentiment_avg, repeat_rate, main_ingredients, health_concern_tags, popularity_score FROM product WHERE {' AND '.join(filters)} ORDER BY popularity_score DESC NULLS LAST LIMIT 3"
            cur.execute(sql_fallback, params)
            products = cur.fetchall()

        for p in products:
            p['sample_reviews'] = self._fetch_reviews(cur, p['goods_id'])

        cur.close()
        conn.close()
        return products

    def _fetch_reviews(self, cur, goods_id, limit=3):
        sql = """
            SELECT content, score, "기호성", "소화/배변"
            FROM review
            WHERE product_id = %s
            LIMIT %s
        """
        cur.execute(sql, (goods_id, limit))
        return cur.fetchall()
