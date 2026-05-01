from .shared import request_sentence


async def gemini() -> str:
    return await request_sentence(
        "google/gemini-2.0-flash-exp:free",
        temperature=0.5,
    )
