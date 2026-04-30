import sys
import os
import asyncio
import json
from decimal import Decimal

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "services/fastapi")))
os.environ["POSTGRES_USER"] = "postgres" # Example, adapt if needed
# .env loading is usually handled in builder or elsewhere

from final_ai.graph.builder import build_graph

async def debug_capture():
    graph = build_graph()
    
    # 1. Case 001 A (First turn)
    initial_state_a = {
        "user_input": "강아지 사료 추천해줘",
        "user_id": "2",
        "conversation_history": [],
        "messages": [],
        "response": None
    }
    config = {"configurable": {"thread_id": "debug_session_1"}}
    
    print("\n--- Testing Case A ---")
    async for event in graph.astream(initial_state_a, config=config, stream_mode="values"):
        res = event.get("response")
        msg_len = len(event.get("messages", []))
        print(f"Event: response={res[:20] if res else None}, msg_len={msg_len}, keys={list(event.keys())}")

    # 2. Case 001 B (Second turn)
    initial_state_b = {
        "user_input": "간식도 같이 추천해줘",
        "user_id": "2",
        "conversation_history": [
            {"role": "user", "content": "강아지 사료 추천해줘"},
            {"role": "assistant", "content": "..."} # Placeholder
        ],
        "messages": [],
        "response": None
    }
    
    print("\n--- Testing Case B ---")
    async for event in graph.astream(initial_state_b, config=config, stream_mode="values"):
        res = event.get("response")
        msg_len = len(event.get("messages", []))
        print(f"Event: response={res[:20] if res else None}, msg_len={msg_len}, keys={list(event.keys())}")

if __name__ == "__main__":
    asyncio.run(debug_capture())
