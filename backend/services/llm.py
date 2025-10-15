import os
import httpx
from dotenv import load_dotenv


async def complete_chat(prompt_text: str) -> str:
    load_dotenv()  # Ensure env vars are loaded
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY environment variable not set")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "alibaba/tongyi-deepresearch-30b-a3b:free",
                "messages": [{"role": "user", "content": prompt_text}],
            },
            timeout=30.0,
        )

    data = resp.json()
    answer = None
    if "choices" in data and len(data["choices"]) > 0:
        answer = data["choices"][0].get("message", {}).get("content")
    if not answer and "output" in data and len(data["output"]) > 0:
        out = data["output"][0]
        if "content" in out and len(out["content"]) > 0:
            answer = out["content"][0].get("text")
    if not answer:
        raise RuntimeError(f"Unexpected model response {data}")
    return answer


