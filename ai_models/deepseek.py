from .shared import request_sentence


async def deepseek() -> str:
    return await request_sentence(
        "deepseek/deepseek-chat-v3-0324:free",
        temperature=0.5,
    )
