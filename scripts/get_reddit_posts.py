# A script to fetch posts from Reddit and fill our Redis store
from services.reddit_client import fetch_posts
from services.qstash_service import publish_message_to_qstash

CANDIDATES = ["Donald Trump", "Kamala Harris"]
NUMBER_OF_POSTS_TO_FETCH = 100

for candidate in CANDIDATES:
    relevant_posts = fetch_posts(candidate, limit=NUMBER_OF_POSTS_TO_FETCH, sort="relevant", time_filter="day")
    print(f"Relevant posts fetched for {candidate}, count:", len(relevant_posts))

    publish_message_to_qstash(
        body={
            "posts": relevant_posts,
            "candidate": candidate
        },
        url="store-post"
    )

    hot_posts = fetch_posts(candidate, limit=NUMBER_OF_POSTS_TO_FETCH, sort="hot")
    print(f"Hot posts fetched for {candidate}, count:", len(hot_posts))

    publish_message_to_qstash(
        body={
            "posts": hot_posts,
            "candidate": candidate
        },
        url="store-post"
    )
