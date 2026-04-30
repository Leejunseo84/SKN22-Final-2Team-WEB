import streamlit as st
from db_helper import fetch_top_products
from skills.engine import AgentSwerm
import os

# 페이지 설정
st.set_page_config(page_title="TailTalk Multi-Agent Lab", layout="wide")

# 카카오톡 스타일 CSS 추가
st.markdown("""
<style>
    .chat-bubble {
        padding: 10px 15px;
        border-radius: 15px;
        margin-bottom: 5px;
        max-width: 80%;
        font-size: 15px;
        line-height: 1.4;
    }
    .chat-left {
        background-color: #FFFFFF;
        border: 1px solid #DDD;
        align-self: flex-start;
        border-top-left-radius: 2px;
    }
    .chat-right {
        background-color: #FEE500; /* 카카오톡 노란색 */
        align-self: flex-end;
        border-top-right-radius: 2px;
    }
    .agent-name {
        font-size: 12px;
        color: #555;
        margin-bottom: 2px;
        font-weight: bold;
    }
    .left-container { 
        align-items: flex-start; 
        display: flex; 
        flex-direction: column; 
        margin-bottom: 15px;
    }
    .right-container { 
        align-items: flex-end; 
        display: flex; 
        flex-direction: column; 
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🐶 TailTalk Expert Swarm Lab")
st.markdown("""
이곳은 AI 에이전트들이 당신의 반려동물을 위해 최적의 상품을 토론하는 **가상 실험실**입니다.
5명의 전문가가 **안전성, 기호성, 영양, 건강, 가성비** 관점에서 정밀 검토를 진행합니다.
""")

# 사이드바: 반려동물 프로필 설정
with st.sidebar:
    st.header("🐾 반려동물 프로필")
    pet_name = st.text_input("이름", value="초코")
    species = st.selectbox("종류", ["강아지", "고양이"])
    breed = st.text_input("품종", value="말티즈")
    
    st.subheader("⚠️ 건강 및 제약 사항")
    allergies = st.text_input("알러지 성분", value="닭고기, 옥수수")
    health_concerns = st.text_input("건강 고민", value="눈물 자국, 슬개골")
    
    budget = st.slider("예산 범위 (원)", 10000, 200000, 50000, step=5000)

pet_info = {
    "name": pet_name,
    "species": species,
    "breed": breed,
    "allergies": [s.strip() for s in allergies.split(",") if s.strip()],
    "health_concerns": [s.strip() for s in health_concerns.split(",") if s.strip()],
    "budget": budget
}

# 메인 화면: 상품 검색
search_query = st.text_input("찾으시는 상품이 무엇인가요?", placeholder="예: 알러지 없는 사료, 다이어트 간식")

if st.button("토론 시작하기 🚀"):
    if not search_query:
        st.warning("먼저 검색어를 입력해 주세요.")
    else:
        with st.spinner("DB에서 최적의 후보 상품을 찾는 중..."):
            products = fetch_top_products(search_query, pet_type=species, limit=5)
            
        if not products:
            st.error("조건에 맞는 상품을 찾을 수 없습니다.")
        else:
            # 1. 후보 상품 출력
            st.subheader("🎯 후보 상품 (Top 5)")
            cols = st.columns(len(products))
            for i, p in enumerate(products):
                with cols[i]:
                    st.image("https://via.placeholder.com/150", caption=p['goods_name'])
                    st.markdown(f"**{p['goods_name']}**")
                    st.markdown(f"💰 {p['discount_price']:,}원")
                    st.markdown(f"⭐ {p['rating']}")

            st.divider()
            
            # 2. 에이전트 토론 섹션
            st.subheader("💬 전문가 위원회 집중 검토")
            swerm = AgentSwerm()
            
            msg_idx = 0
            for step in swerm.run_debate(products, pet_info, rounds=1):
                if step["type"] == "header":
                    st.markdown(step["content"])
                elif step["type"] == "message":
                    msg_idx += 1
                    is_left = msg_idx % 2 != 0
                    align_class = "left-container" if is_left else "right-container"
                    bubble_class = "chat-left" if is_left else "chat-right"
                    
                    emoji_map = {
                        "safety_expert": "🛡️",
                        "palatability_expert": "😋",
                        "nutrition_expert": "🧬",
                        "health_expert": "🏥",
                        "economics_expert": "🪙"
                    }
                    icon = emoji_map.get(step["agent"], "🤖")
                    
                    content = step["content"].split(": ", 1)[1] if ": " in step["content"] else step["content"]
                    role_name = step["content"].split(": ", 1)[0].replace("**", "")
                    
                    st.markdown(f"""
                    <div class="{align_class}">
                        <div class="agent-name">{icon} {role_name}</div>
                        <div class="chat-bubble {bubble_class}">{content}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif step["type"] == "final":
                    st.divider()
                    st.subheader("🎩 최종 통합 권고")
                    st.success(step["content"])

# 실행 방법 안내
st.sidebar.divider()
st.sidebar.info("`streamlit run swerm/app.py` 명령으로 실행하세요.")
