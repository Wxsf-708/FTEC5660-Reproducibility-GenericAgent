"""测试一组候选模型名，查看 API 是否接受以及实际返回的模型标识。"""
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # fork: framework at repo root
from mykey import native_oai_config as cfg  # noqa: E402

url = cfg["apibase"].rstrip("/") + "/v1/chat/completions"
headers = {"Authorization": "Bearer " + cfg["apikey"],
           "Content-Type": "application/json"}
candidates = ["deepseek-v4-pro", "deepseek-chat", "deepseek-flash"]
for name in candidates:
    payload = {
        "model": name,
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
        "max_tokens": 16,
        "stream": False,
        "temperature": 0.0,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            d = r.json()
            print(f"requested={name:18s} HTTP200  returned={d.get('model')}")
        else:
            print(f"requested={name:18s} HTTP{r.status_code}  {r.text[:200]}")
    except Exception as e:
        print(f"requested={name:18s} ERROR {e}")
