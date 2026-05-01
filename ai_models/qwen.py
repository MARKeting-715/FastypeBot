from .shared import request_sentence


async def qwen() -> str:
    return await request_sentence(
        "qwen/qwen-2.5-7b-instruct:free",
        temperature=0.7,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.3,
    )
