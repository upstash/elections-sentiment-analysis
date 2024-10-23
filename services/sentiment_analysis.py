import os
from qstash import QStash
from qstash.chat import openai
from dotenv import load_dotenv

load_dotenv()

qstash_token = os.getenv("QSTASH_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
api_base_url = os.getenv("API_BASE_URL")

qstash_client = QStash(qstash_token)

def analyze_sentiment(text: str, candidate: str, title: str):
    qstash_client.message.publish_json(
        api={"name": "llm", "provider": openai(openai_api_key)},
        body={
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                    Rate the sentiment of the following text between 0 (hate) and 100 (love): '{text}'
                    Kamala Harris and Donald Trump are both running for president in 2024. Harris is a Democrat, while Trump is a Republican.
                    Rate the sentiment based on the candidate mentioned in the text.
                    If the sentiment is positive, rate it closer to 100. If it's negative, rate it closer to 0.
                    Just type a number between 0 and 100.
                    """,
                }
            ],
        },
        callback=f"{api_base_url}/sentiment-callback?candidate={candidate}&title={title}",
        headers={"Upstash-Callback-Retries": "1"},
        retries=1,
    )