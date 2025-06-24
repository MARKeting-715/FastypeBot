import httpx

prompt = """
DO NOT TRANSLATE. DO NOT EXPLAIN. DO NOT USE QUOTES.

You MUST output ONLY ONE Russian sentence for blind typing practice.

MANDATORY RULES:
- Only ONE sentence in Russian.
- Sentence must be 10–15 words long.
- NO English. NO Chinese. NO translation. NO explanation.
- Do NOT use quotation marks or parentheses.
- Use natural, everyday Russian — no rare words, no formal tone.
- Start with a capital letter. Use commas only if needed.

REPEAT: OUTPUT ONLY ONE RUSSIAN SENTENCE. NOTHING ELSE. NO TRANSLATION. NO EXTRA TEXT. NO QUOTES.

do not somehow ever make a translation. Please
"""


async def mistral():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer AI_KEY",
                "Content-Type": "application/json",
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
            },
            json={
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 75,
                "temperature": 0.5
            })
    try:
        return response.json()["choices"][0]["message"]["content"]
    except KeyError:
        print(response.json())
        return "Не удалось получит ответ, смените модель на другую доступную"