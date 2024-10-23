import os
import praw
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

# Create a Reddit instance
reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent
)

# Function to fetch posts from Reddit
def fetch_posts(candidate: str, limit: int = 10, sort: str = "new"):
    posts = []
    query = candidate
    subreddit = reddit.subreddit("all")
    for submission in subreddit.search(query, sort=sort):
        if submission.selftext == "": # Skip posts without text
            continue
        posts.append({
            "title": submission.title,
            "selftext": submission.selftext,
            "url": submission.url
        })
        if len(posts) >= limit: # Limit the number of posts
            break
    return posts