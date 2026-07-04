import subprocess
import re

paths = [
    "app.ai.claude_client.stream_claude_response",
    "app.api.chat.stream_claude_response",
    "api.chat.stream_claude_response",
]

for p in paths:
    print(f"Trying path: {p}")
    with open("tests/test_chat.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = re.sub(r'patch\("[^"]+", side_effect=_mock_claude_stream\)', f'patch("{p}", side_effect=_mock_claude_stream)', content)
    
    with open("tests/test_chat.py", "w", encoding="utf-8") as f:
        f.write(new_content)
        
    result = subprocess.run(["pytest", "tests/test_chat.py", "-v", "--tb=short"], capture_output=True, text=True)
    if "failed" not in result.stdout.lower() and "error" not in result.stdout.lower():
        print(f"SUCCESS with {p}")
        break
    else:
        print(f"FAILED with {p}")
        print("Output:", result.stdout[-500:])
