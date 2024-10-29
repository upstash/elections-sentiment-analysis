import os
from qstash import QStash
from qstash.chat import openai
from dotenv import load_dotenv
from urllib.parse import quote

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
Please assess the sentiment of the following text on a scale from 0 to 100, where 0 represents strong negativity (hate) and 100 represents strong positivity (love):

{text}

The text mentions {candidate}, a 2024 presidential candidate. Rate the sentiment based on the tone toward {candidate}.

Provide a single number between 0 and 100 to reflect the overall sentiment in the text.

Do not include any additional information in your response. Just a number between 0 and 100.
                    """,
                }
            ],
        },
        callback = f"{api_base_url}/sentiment-callback?candidate={quote(candidate)}&title={quote(title)}",
        retries=1,
    )

def parse_response(response):
    score = float(''.join(filter(str.isdigit, response)))
    print("Parsed score from response:", score)
    if score > 100:
        score = 100
    if score < 0:
        score = 0
    return score