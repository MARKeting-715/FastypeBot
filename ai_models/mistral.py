from .shared import request_sentence


async def mistral() -> str:
    return await request_sentence(
        "mistralai/mistral-7b-instruct:free",
        temperature=0.5,
    )
