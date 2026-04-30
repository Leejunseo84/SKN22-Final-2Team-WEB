import json
import os

def convert_json_to_jsonl(input_file, output_file):
    """
    JSON 리스트 파일을 JSONL(JSON Lines) 포맷으로 변환합니다.
    """
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: Input JSON must be a list of objects.")
        return

    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"Successfully converted {len(data)} entries to {output_file}")

if __name__ == "__main__":
    input_path = "/home/playdata/SKN22-Final-2Team-WEB/docs/evaluation/ai_logic_golden_dataset.json"
    output_path = "/home/playdata/SKN22-Final-2Team-WEB/docs/evaluation/ragas_dataset/ai_logic_golden_dataset.jsonl"
    
    convert_json_to_jsonl(input_path, output_path)
