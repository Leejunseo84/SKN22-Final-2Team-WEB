import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# .env 파일 로드 (상위 디렉토리의 .env 활용 가능성 고려)
load_dotenv(os.path.join(os.path.dirname(__file__), "../services/fastapi/.env"))

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
        print(f"DB Connection Error: {e}")
        raise

def fetch_sample_reviews(goods_id, limit=3):
    """
    특정 상품의 실제 리뷰 샘플을 가져옵니다.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    sql = """
        SELECT content, score, sentiment_label, "기호성", "소화/배변", "배송/포장"
        FROM review
        WHERE product_id = %s
        ORDER BY written_at DESC
        LIMIT %s
    """
    cur.execute(sql, (goods_id, limit))
    reviews = cur.fetchall()
    cur.close()
    conn.close()
    return reviews

def fetch_top_products(query, pet_type=None, limit=5):
    """
    Search for top products based on query and pet_type.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # 간단한 검색 구현 (상위 3개)
    # 실제 서비스에서는 벡터 검색을 쓰지만 프로토타입에서는 ILIKE 검색 사용
    filters = ["soldout_yn = FALSE", "goods_name NOT ILIKE '%%샘플%%'"]
    params = []
    
    if query:
        # 검색어를 공백 단위로 쪼개어 각각 필터링 (다이어트 사료 -> 다이어트, 사료)
        words = query.split()
        for word in words:
            filters.append("""
                (goods_name ILIKE %s 
                OR brand_name ILIKE %s 
                OR ARRAY_TO_STRING(health_concern_tags, ' ') ILIKE %s
                OR main_ingredients::text ILIKE %s)
            """)
            params.extend([f"%{word}%", f"%{word}%", f"%{word}%", f"%{word}%"])
    
    if pet_type:
        filters.append("%s = ANY(pet_type)")
        params.append(pet_type)

    sql = f"""
        SELECT 
            goods_id, goods_name, brand_name, price, discount_price, 
            rating, review_count, sentiment_avg, repeat_rate,
            main_ingredients, health_concern_tags
        FROM product 
        WHERE {" AND ".join(filters)}
        ORDER BY popularity_score DESC NULLS LAST, review_count DESC NULLS LAST
        LIMIT %s
    """
    
    params.append(limit)
    cur.execute(sql, params)
    products = cur.fetchall()
    
    # 각 상품별 실제 리뷰 추가 주입
    for p in products:
        p['sample_reviews'] = fetch_sample_reviews(p['goods_id'])

    cur.close()
    conn.close()
    return products

# 하위 호환성 및 독립적인 subagent 폴더를 위한 별칭
def fetch_top_3_products(query, pet_type=None):
    return fetch_top_products(query, pet_type, limit=3)
