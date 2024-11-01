from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from services.reddit_client import fetch_posts
from services.sentiment_analysis import analyze_sentiment, parse_response
from services.redis_service import store_post, get_all_posts, store_score, get_recent_posts, check_post_exists, get_score, store_score_history, get_score_history, make_score_histories_equal_length
from services.qstash_service import publish_message_to_qstash
import base64
import json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

NUMBER_OF_POSTS_TO_FETCH = 10 
CANDIDATES = ["Donald Trump", "Kamala Harris"]
NUMBER_OF_POSTS_TO_DISPLAY = 10
DEFAULT_SCORE = -1

# This endpoint will display the sentiment scores for each candidate
@app.get("/")
def read_root(request: Request):
    print("Accessed root endpoint")
    candidates = CANDIDATES
    posts = {}
    score_history = {}

    # Get the score history for each candidate
    for candidate in candidates:
        score_history[candidate] = get_score_history(candidate)

    # Fetch recent posts for both Trump and Harris
    for candidate in ["Donald Trump", "Kamala Harris"]:
        posts[candidate] = get_recent_posts(candidate, limit=NUMBER_OF_POSTS_TO_DISPLAY)
        print(f"Recent posts for {candidate} fetched")

    return templates.TemplateResponse("index.html", {
        "request": request,
        "score_history": score_history,
        "posts": posts
    })

@app.post("/update-scores")
def update_scores_endpoint():
    print("Accessed update-scores endpoint")
    candidates = CANDIDATES
    for candidate in candidates:
        print(f"Getting posts for {candidate}")
        candidate_posts = get_all_posts(candidate)
        print(f"Updating scores for {candidate}")
        total_score = 0
        number_of_valid_scores = 0
        i = 0
        if candidate_posts:
            for post in candidate_posts:
                print(f"Post {i}: {post['title']}")
                i += 1
                # Skip posts with a score of -1
                if post['score'] == str(DEFAULT_SCORE):
                    continue
                total_score += float(post['score'])
                number_of_valid_scores += 1
            if number_of_valid_scores > 0:
                average_score = total_score / number_of_valid_scores
                store_score_history(candidate, round(average_score, 2))
                print(f"Updated score for {candidate}")
            else:
                print(f"No valid scores found for {candidate}")

    return JSONResponse(content={"status": "Scores updated"})

@app.post("/update-scores-failed")
def update_scores_failed_endpoint():
    print("Accessed update-scores-failed endpoint")

    # Make the score_history for each candidate the same length as the shortest one
    candidates = CANDIDATES
    make_score_histories_equal_length(candidates[0], candidates[1])

    return JSONResponse(content={"status": "Scores update failed"})

# This endpoint will be called by the scheduler to fetch the latest posts
@app.post("/fetch-posts")
def fetch_posts_endpoint():
    print("Accessed fetch-posts endpoint")
    candidates = CANDIDATES
    for candidate in candidates:
        hot_posts = fetch_posts(candidate, limit=NUMBER_OF_POSTS_TO_FETCH, sort="hot")
        relevant_posts = fetch_posts(candidate, limit=NUMBER_OF_POSTS_TO_FETCH, sort="relevant", time_filter="day")
        print(f"Fetched hot posts for {candidate}")
        print(f"Fetched relevant posts for {candidate}")

        hot_posts_body = {
            "posts": hot_posts,
            "candidate": candidate
        }

        relevant_posts_body = {
            "posts": relevant_posts,
            "candidate": candidate
        }

        publish_message_to_qstash(hot_posts_body, "store-post")
        publish_message_to_qstash(relevant_posts_body, "store-post")

# This endpoint will be used to store posts that come from /fetch-posts
@app.post("/store-post")
async def store_post_endpoint(request: Request):
    data = await request.json()
    candidate = data["candidate"]
    posts = data["posts"]
    print(f"Storing posts for {candidate}")

    # Iterate over the posts and store each one, while analyzing its sentiment
    for post in posts:
        # Skip posts that already exist in the store with a valid score
        if check_post_exists(candidate, post["title"]):
            if get_score(candidate, post["title"]) != str(DEFAULT_SCORE):
                print(f"Post already exists with valid score, skipping: {post['title']}")
                continue

        print(f"Storing new post: {post['title']}")
        store_post(candidate, post["title"], post["url"], DEFAULT_SCORE)

        body = {
            "candidate": candidate,
            "title": post["title"],
            "selftext": post["selftext"]
        }

        publish_message_to_qstash(body, "analyze-sentiment")

# This endpoint will be used to analyze the sentiment of a post
@app.post("/analyze-sentiment")
async def analyze_sentiment_endpoint(request: Request):
    data = await request.json()
    selftext = data["selftext"]
    candidate = data["candidate"]
    title = data["title"]
    print(f"Analyzing sentiment for candidate: {candidate}, Title: {title}")

    analyze_sentiment(f"Candidate: {candidate}, Title: {title}, Text: {selftext}", candidate, title)
    print("Sentiment analysis started")

    return JSONResponse(content={"status": "Sentiment analysis started"})

# This endpoint will be used as the callback URL for the sentiment analysis
# It will parse the response and store the sentiment score to redis
@app.post("/sentiment-callback")
async def sentiment_callback(candidate: str, title: str, request: Request):
    data = await request.json()
    print("Received callback data:")

    encoded_body = data.get('body', '')
    decoded_body = base64.b64decode(encoded_body).decode('utf-8')

    decoded_data = json.loads(decoded_body)
    response = decoded_data['choices'][0]['message']['content']
    print("Parsed response:", response)

    score = parse_response(response)
    print(f"Storing score for {candidate} - Title: {title}, Score: {score}")
    store_score(candidate, title, score)

    return JSONResponse(content={"status": "Sentiment score stored"})

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')