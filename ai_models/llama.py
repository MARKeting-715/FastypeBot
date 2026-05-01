from .shared import request_sentence


async def llama() -> str:
    return await request_sentence(
        "meta-llama/llama-3.3-8b-instruct:free",
        temperature=0.4,
    )
