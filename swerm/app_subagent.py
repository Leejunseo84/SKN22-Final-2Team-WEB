import streamlit as st
from subagent.core import SwarmSubAgent

# 페이지 설정
st.set_page_config(page_title="TailTalk Chat Lab", layout="wide")

# 카카오톡 스타일 CSS (배경 컨테이너 제거 버전)
st.markdown("""
<style>
    /* 메시지 한 줄 (가로 전체 사용) */
    .message-row {
        display: flex;
        width: 100%;
        margin-bottom: 15px;
        flex-direction: column;
    }
    
    /* 왼쪽 정렬용 컨테이너 */
    .row-left { align-items: flex-start; }
    /* 오른쪽 정렬용 컨테이너 */
    .row-right { align-items: flex-end; }

    /* 에이전트 이름 */
    .agent-label {
        font-size: 12px;
        color: #333333;
        margin-bottom: 4px;
        font-weight: bold;
    }

    /* 말풍선 공통 */
    .bubble {
        max-width: 70%;
        padding: 10px 14px;
        border-radius: 15px;
        font-size: 14px;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.1);
        line-height: 1.5;
    }

    /* 왼쪽 말풍선 (흰색) */
    .bubble-left {
        background-color: #FFFFFF;
        color: #000000;
        border: 1px solid #E0E0E0;
        border-top-left-radius: 2px;
    }

    /* 오른쪽 말풍선 (노란색) */
    .bubble-right {
        background-color: #FEE500;
        color: #000000;
        border-top-right-radius: 2px;
    }

    /* 시스템 공지 스타일 */
    .system-banner {
        text-align: center;
        width: 100%;
        margin: 20px 0;
    }
    .system-text {
        background-color: rgba(0,0,0,0.05);
        color: #666666;
        padding: 4px 20px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        border: 1px solid #EEEEEE;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗨️ TailTalk AI Expert Chat Lab")

with st.sidebar:
    st.header("🐾 반려동물 프로필")
    pet_name = st.text_input("이름", value="초코")
    species = st.selectbox("종류", ["강아지", "고양이"])
    breed = st.text_input("품종", value="말티즈")
    
    st.subheader("⚠️ 건강 및 제약 사항")
    allergies = st.text_input("알러지 성분", value="닭고기")
    health_concerns = st.text_input("건강 고민", value="눈물 자국")
    budget = st.slider("예산 범위 (원)", 10000, 200000, 50000, step=5000)

pet_info = {"name": pet_name, "species": species, "breed": breed, "allergies": [s.strip() for s in allergies.split(",") if s.strip()], "health_concerns": [s.strip() for s in health_concerns.split(",") if s.strip()], "budget": budget}

search_query = st.text_input("찾으시는 상품이 무엇인가요?", placeholder="예: 닭고기 사료")

if st.button("전문가 대화 시작 🚀"):
    if not search_query:
        st.warning("검색어를 입력해 주세요.")
    else:
        swarm_engine = SwarmSubAgent()
        product_container = st.empty()
        
        # 탭이나 다른 영역 없이 바로 메시지 출력
        for step in swarm_engine.run_collaboration(search_query, pet_info):
            if step["type"] == "products":
                products = step["content"]
                with product_container:
                    st.subheader(f"🎯 실시간 후보 리스트")
                    cols = st.columns(len(products))
                    for i, p in enumerate(products):
                        with cols[i]:
                            st.info(f"**{p['goods_name']}**")
                            st.caption(f"💰 {p['discount_price']:,}원")
                
            elif step["type"] == "header":
                st.markdown(f'<div class="system-banner"><span class="system-text">{step["content"]}</span></div>', unsafe_allow_html=True)
                
            elif step["type"] == "message":
                agent = step["agent"]
                content = step["content"].split(": ", 1)[1]
                
                if agent in ["health_agent", "budget_manager", "concierge"]:
                    row_class = "row-left"
                    bubble_class = "bubble-left"
                    avatar = "🩺" if agent == "health_agent" else "💰" if agent == "budget_manager" else "🎩"
                else:
                    row_class = "row-right"
                    bubble_class = "bubble-right"
                    avatar = "📊" if agent == "review_critic" else "🔍"

                st.markdown(f"""
                    <div class="message-row {row_class}">
                        <div class="agent-label">{avatar} {agent.replace('_', ' ').title()}</div>
                        <div class="bubble {bubble_class}">{content}</div>
                    </div>
                """, unsafe_allow_html=True)
                    
            elif step["type"] == "final":
                st.markdown(f'<div class="system-banner" style="margin-top:30px;"><span class="system-text" style="background-color:#F0F2F6; color:#333; padding:10px 30px; font-size:14px; border:1px solid #DDD;">🏆 {step["content"]}</span></div>', unsafe_allow_html=True)
            
            elif step["type"] == "error":
                st.error(step["content"])
