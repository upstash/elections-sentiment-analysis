# A script to fetch posts from Reddit and fill our Redis store
from qstash import QStash
import os
from dotenv import load_dotenv
from services.reddit_client import fetch_posts

load_dotenv()

qstash_client = QStash(os.getenv("QSTASH_TOKEN"))

CANDIDATES = ["Donald Trump", "Kamala Harris"]

for candidate in CANDIDATES:
    top_posts = fetch_posts(candidate, limit=10, sort="top")
    print("Top posts fetched")

    # Print
    for post in top_posts:
        print(post)
        print(post.title)
        print(post.url)
        print(post.selftext)

    hot_posts = fetch_posts(candidate, limit=10, sort="hot")
    print("Hot posts fetched")

    qstash_client.message.publish_json(
        url=f"{os.getenv('API_BASE_URL')}/store-post",
        body={
            "posts": top_posts,
            "candidate": candidate
        },
        headers={"Content-Type": "application/json"},
        retries=1,
    )

if __name__ == "__main__":
    print("Fetching posts from Reddit...")