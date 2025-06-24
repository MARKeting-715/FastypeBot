import httpx

prompt = """
Please generate a grammatically correct and meaningful Russian sentence for blind typing practice.
The sentence must:
- Contain exactly 10 to 15 words (no more, no less)
- Start with a capital letter
- Be clear, logical, and grammatically correct
- Include commas only where necessary (for compound or complex sentences)
- Use natural vocabulary, avoiding overly formal or rare words
- The sentence must be about a completely different topic from any previous sentence; avoid repeating any subject or theme.
Do not use metaphors, idioms, or topics that have been covered before.
The sentence must be free of quotes, including quotation marks around the sentence.
If you cannot generate a valid sentence, return an error message instead (e.g., 'Error: unable to generate sentence').
Return only the sentence, with no explanations, formatting, or extra information.
"""






async def deepseek():
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
                "model": "deepseek/deepseek-chat-v3-0324:free",
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
        return "Не удалось получит ответ, смените модель на другую доступную"
