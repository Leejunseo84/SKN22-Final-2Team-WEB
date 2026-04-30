# 02. UI/UX 및 인터페이스

## 2.1 3-Panel 레이아웃 전략
* **Panel 1 (Left)**: 대화 이력 관리 (Session History) - 끊김 없는 사용자 경험 제공
* **Panel 2 (Center)**: 메인 챗봇 인터페이스 - LLM과의 자연스러운 대화 창구
* **Panel 3 (Right)**: 실시간 추천 패널 (대화 맥락에 맞는 상품 카드 배치)

## 2.2 기술 구현
* **Frontend**: Django Template 엔진 기반의 서버 사이드 렌더링(SSR)
* **Interactive UI**: Vanilla JavaScript 및 CSS를 활용하여 SPA와 같은 매끄러운 패널 전환 및 데이터 업데이트 구현
* **반응형 디자인**: 다양한 디바이스 환경에서도 최적의 쇼핑 환경 제공
