from upstash_redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
redis_client = Redis.from_env()

def store_post(candidate: str, title: str, url: str, score: float):
    key = f"{candidate}:{title}"
    data = {"title": title, "url": url, "score": score}
    redis_client.hset(key, values=data)
    # store all post keys in a set 
    redis_client.sadd(f"{candidate}:posts", key)

def store_score(candidate: str, title: str, score: float):
    key = f"{candidate}:{title}"
    redis_client.hset(key, "score", score)

def get_all_posts(candidate: str):
    keys = redis_client.smembers(f"{candidate}:posts")
    posts = []
    for key in keys:
        post = redis_client.hgetall(key)
        posts.append(post)
    return posts

def get_recent_posts(candidate: str, limit: int):
    keys = redis_client.smembers(f"{candidate}:posts")
    posts = []
    for key in keys:
        post = redis_client.hgetall(key)
        # Skip posts with a score of -1 (invalid)
        if post['score'] == "-1":
            continue
        posts.append(post)
        # Limit the number of posts to display
        if len(posts) >= limit:
            break
    return posts

def check_post_exists(candidate: str, title: str):
    key = f"{candidate}:{title}"
    return redis_client.exists(key)

def get_score(candidate: str, title: str):
    key = f"{candidate}:{title}"
    return redis_client.hget(key, "score")