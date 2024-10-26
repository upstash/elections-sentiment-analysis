import os
from qstash import QStash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize QStash client
qstash_client = QStash(os.getenv("QSTASH_TOKEN"))

# Function to publish a message to QStash
def publish_message_to_qstash(body, url):
    qstash_client.message.publish_json(
        url=f"{os.getenv('API_BASE_URL')}/{url}",
        body=body,
        retries=1,
        headers={"Content-Type": "application/json"},
    )