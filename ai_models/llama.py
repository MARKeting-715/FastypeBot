import httpx

prompt = """
Generate 1 Russian sentence for language practice. It must:

- Be grammatically and orthographically correct
- Start with a capital letter and end with a period
- Contain 10 to 15 words
- Include commas where appropriate
- Be of medium complexity — not too simple, not too advanced
- Be interesting and natural
- Be on a unique topic

Do not include translation or explanation — only output the sentence.
"""


async def llama():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer AI_KEY",
                "Content-Type": "application/json",
                "HTTP-Referer": "<YOUR_SITE_URL>",  # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "<YOUR_SITE_NAME>",  # Optional. Site title for rankings on openrouter.ai.
            },
            json = {
                "model": "meta-llama/llama-3.3-8b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 75,
                "temperature": 0.4
            })
    try:
        return response.json()["choices"][0]["message"]["content"]
    except KeyError:
        return "Не удалось получит ответ, смените модель на другую доступную"