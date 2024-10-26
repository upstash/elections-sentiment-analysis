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
def fetch_posts(candidate: str, limit: int = 10, sort: str = "hot", time_filter: str = "all") -> list:
    posts = []
    query = candidate
    subreddit = reddit.subreddit("all")
    
    for submission in subreddit.search(query, sort=sort, time_filter=time_filter):
        if submission.selftext == "":  # Skip posts without text
            continue
        if submission.score < 10:  # Skip posts with low scores
            continue
        
        # Clean title and selftext to only contain chars that are safe for JSON
        safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>? ")
        title = "".join(c for c in submission.title if c in safe_chars)
        selftext = "".join(c for c in submission.selftext if c in safe_chars)
        
        posts.append({
            "title": title,
            "selftext": selftext,
            "url": submission.url
        })
        
        if len(posts) >= limit:  # Limit the number of posts
            break
            
    return posts