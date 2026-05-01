from __future__ import annotations

import os

import httpx


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_ERROR_MESSAGE = "Не удалось получить ответ, смените модель на другую доступную"
DEFAULT_SENTENCE_PROMPT = (
    "Сгенерируй одно грамотное русское предложение для тренировки слепой печати.\n\n"
    "Требования:\n"
    "- только одно предложение;\n"
    "- 10-15 слов;\n"
    "- без перевода, пояснений и лишнего текста;\n"
    "- без кавычек и скобок;\n"
    "- с заглавной буквы;\n"
    "- с запятыми только если они действительно нужны;\n"
    "- тема должна быть естественной и бытовой.\n\n"
    "Верни только предложение на русском языке."
)


def load_openrouter_key() -> str:
    for env_name in ("OPENROUTER_API_KEY", "AI_KEY"):
        value = os.getenv(env_name)
        if value:
            return value

    try:
        from config import AI_KEY as config_ai_key  # type: ignore
    except Exception:
        config_ai_key = None

    if config_ai_key:
        return config_ai_key

    raise RuntimeError(
        "OpenRouter API key is not configured. Set OPENROUTER_API_KEY, AI_KEY, or config.py"
    )


def build_openrouter_headers() -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {load_openrouter_key()}",
        "Content-Type": "application/json",
    }

    referer = os.getenv("OPENROUTER_REFERER")
    title = os.getenv("OPENROUTER_TITLE")

    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title

    return headers


async def request_sentence(
    model: str,
    *,
    prompt: str = DEFAULT_SENTENCE_PROMPT,
    temperature: float = 0.5,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
    presence_penalty: float | None = None,
) -> str:
    payload: dict[str, object] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 75,
        "temperature": temperature,
    }

    if top_p is not None:
        payload["top_p"] = top_p
    if frequency_penalty is not None:
        payload["frequency_penalty"] = frequency_penalty
    if presence_penalty is not None:
        payload["presence_penalty"] = presence_penalty

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers=build_openrouter_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError, RuntimeError):
        return DEFAULT_ERROR_MESSAGE

    try:
        content = data["choices"][0]["message"]["content"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError):
        return DEFAULT_ERROR_MESSAGE

    if not isinstance(content, str):
        return DEFAULT_ERROR_MESSAGE

    content = content.strip()
    return content or DEFAULT_ERROR_MESSAGE
