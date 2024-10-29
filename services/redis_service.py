from upstash_redis import Redis
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
redis_client = Redis.from_env()

DEFAULT_SCORE = -1 # Default score for a post (invalid)
SCORE_HISTORY_LIMIT = 100 # Limit for the number of scores to keep
POST_LIMIT = 50  # Limit for the number of recent posts to keep

def store_post(candidate: str, title: str, url: str, score: float):
    key = f"{candidate}:{title}"
    data = {"title": title, "url": url, "score": score}
    
    # Store the post in a hash
    redis_client.hset(key, values=data)
    
    # Store all post keys in a set for fast retrieval and in a sorted set for ordering
    redis_client.sadd(f"{candidate}:posts", key)
    redis_client.zadd(f"{candidate}:post_order", {key: time.time()})
    
    # Trim posts to keep only the most recent 50
    trim_old_posts(candidate)

def trim_old_posts(candidate: str):
    # Check if the number of posts exceeds POST_LIMIT
    post_count = redis_client.zcard(f"{candidate}:post_order")
    print(f"Number of posts for {candidate}: {post_count}")
    
    if post_count > POST_LIMIT:
        # Get the oldest posts that exceed the POST_LIMIT
        excess_posts = redis_client.zrange(f"{candidate}:post_order", 0, post_count - POST_LIMIT - 1)
        print(f"Excess post count: {len(excess_posts)}")
        
        # Remove the excess posts from both the `post_order` sorted set and `posts` set
        for post_key in excess_posts:
            print(f"Removing post: {post_key}")
            redis_client.srem(f"{candidate}:posts", post_key)
            redis_client.delete(post_key)  # Remove the post data from the hash
            redis_client.zrem(f"{candidate}:post_order", post_key)

def store_score(candidate: str, title: str, score: float):
    key = f"{candidate}:{title}"
    url = redis_client.hget(key, "url")
    data = {"title": title, "url": url, "score": score}
    redis_client.hset(key, values=data)

def get_all_posts(candidate: str):
    # Get all posts based on the ordered list in post_order
    keys = redis_client.zrevrange(f"{candidate}:post_order", 0, -1)  # Newest to oldest
    print(f"Number of posts for {candidate}: {len(keys)} in post_order")
    posts = []
    for key in keys:
        post = redis_client.hgetall(key)
        posts.append(post)
    print(f"Number of posts for {candidate}: {len(posts)} in hashes")
    return posts

def get_recent_posts(candidate: str, limit: int):
    # Get only the most recent posts based on post_order
    keys = redis_client.zrevrange(f"{candidate}:post_order", 0, limit - 1)
    posts = []
    for key in keys:
        post = redis_client.hgetall(key)
        # Skip posts with a score of -1 (invalid)
        if post['score'] == str(DEFAULT_SCORE):
            continue
        posts.append(post)
    return posts

def check_post_exists(candidate: str, title: str):
    key = f"{candidate}:{title}"
    return redis_client.exists(key)

def get_score(candidate: str, title: str):
    key = f"{candidate}:{title}"
    return redis_client.hget(key, "score")

def store_score_history(candidate: str, score: float):
    key = f"{candidate}:scores"
    redis_client.rpush(key, score)
    # Limit the number of scores to store to SCORE_HISTORY_LIMIT
    redis_client.ltrim(key, -SCORE_HISTORY_LIMIT, -1)

def get_score_history(candidate: str):
    key = f"{candidate}:scores"
    return redis_client.lrange(key, 0, -1)

def make_score_histories_equal_length(candidate1: str, candidate2: str):
    scores1 = get_score_history(candidate1)
    scores2 = get_score_history(candidate2)
    if len(scores1) > len(scores2):
        redis_client.ltrim(f"{candidate1}:scores", 0, len(scores2) - 1)
    elif len(scores2) > len(scores1):
        redis_client.ltrim(f"{candidate2}:scores", 0, len(scores1) - 1)
