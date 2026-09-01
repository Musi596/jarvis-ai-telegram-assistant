from groq import AsyncGroq

from config import GROQ_API_KEY, TEXT_MODEL, AUDIO_MODEL, SYSTEM_PROMPT

client = AsyncGroq(api_key=GROQ_API_KEY)


async def ask_ai(history: list[dict]):
    response = await client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history],
        temperature=0.5,
        max_completion_tokens=800,
        reasoning_effort="low",
        reasoning_format="hidden"
    )
    return response.choices[0].message.content.strip()


async def transcribe(audio_bytes: bytes, filename: str = "voice.ogg"):
    result = await client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model=AUDIO_MODEL,
    )
    return result.text.strip()
