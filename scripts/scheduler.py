from qstash import QStash
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_base_url = os.getenv("API_BASE_URL")
qstash_token = os.getenv("QSTASH_TOKEN")

qstash_client = QStash(token=qstash_token)

def schedule_reddit_fetch():
    qstash_client.schedule.create(
        destination=f"{api_base_url}/fetch-posts",
        cron="*/10 * * * *",  # Every 10 minutes
        retries=1,
    )

def schedule_updating_scores():
    qstash_client.schedule.create(
        destination=f"{api_base_url}/update-scores",
        cron="0 * * * *",  # Every hour
        retries=1,
    )

if __name__ == "__main__":
    # schedule_reddit_fetch()
    schedule_updating_scores()