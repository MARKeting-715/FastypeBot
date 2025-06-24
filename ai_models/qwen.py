import httpx

prompt = """
请你生成一个用于俄语盲打练习的句子。

严格要求如下：
- 句子必须为**仅一个俄语句子**，长度为10到15个单词。
- 不得输出中文或英文翻译，不得解释或说明。
- 不得使用引号。
- 句子必须使用自然、日常的俄语词汇。避免书面语、罕见词或比喻。
- 句子首字母需大写，可使用逗号。
- 输出必须是俄语句子本身，禁止添加任何额外内容。

重要：只返回一个俄语句子，**禁止翻译、解释或附加内容**。
"""

async def qwen():
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
                "model": "qwen/qwen-2.5-7b-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,  # Устанавливаем температуру для большей вариативности
                "max_tokens": 75,  # Ограничение на количество токенов (примерно 10-15 слов)
                "top_p": 0.9,  # Вероятностный сэмплинг
                "frequency_penalty": 0.5,  # Уменьшение частоты повторений
                "presence_penalty": 0.3,  # Штраф за уже использованные темы
            })
    try:
        return response.json()["choices"][0]["message"]["content"]
    except KeyError:
        print(response.json())
        return "Не удалось получит ответ, смените модель на другую доступную"