from groq import AsyncGroq
from app.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def call_llm(prompt:str, model:str = "openai/gpt-oss-120b")->str:
    response = await client.chat.completions.create(
        model= model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

