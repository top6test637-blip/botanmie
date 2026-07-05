import json
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    path = r"C:\Users\monsm\.gemini\antigravity-ide\brain\2535569d-521c-4aff-96a7-2ad033032980\.system_generated\logs\transcript.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            obj = json.loads(line)
            content_str = str(obj)
            # Find all user requests or container logs containing 404 and thumbnail
            if "404" in content_str and "thumb" in content_str:
                print(f"Line {i} - Type: {obj.get('type')}")
                if "content" in obj:
                    c = obj["content"]
                    if isinstance(c, str):
                        # print lines with 404 and thumb
                        for cl in c.split("\n"):
                            if "404" in cl or "thumb" in cl:
                                print(f"  Log: {cl}")
                if "tool_calls" in obj:
                    print(f"  Tool: {str(obj['tool_calls'])[:300]}")

if __name__ == "__main__":
    main()
