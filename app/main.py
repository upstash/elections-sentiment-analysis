from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from services.reddit_client import fetch_posts
from services.sentiment_analysis import analyze_sentiment
from services.redis_service import store_post, get_all_posts, store_score, get_recent_posts
from qstash import QStash
import base64
import os
import json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Initialize QStash client
qstash_client = QStash(os.getenv("QSTASH_TOKEN"))

NUMBER_OF_POSTS = 2
CANDIDATES = ["Donald Trump", "Kamala Harris"]
NUMBER_OF_POSTS_TO_DISPLAY = 10

# This endpoint will display the sentiment scores for each candidate
@app.get("/")
def read_root(request: Request, candidate_name: str = None):
    candidates = CANDIDATES
    scores = {}
    posts = []

    # Calculate sentiment scores for all candidates
    for candidate in candidates:
        candidate_posts = get_all_posts(candidate)
        if candidate_posts:
            average_score = sum(float(post['score']) for post in candidate_posts) / len(candidate_posts)
            scores[candidate] = round(average_score, 2)
        else:
            scores[candidate] = "No data"

    # If a candidate is selected, fetch their recent posts
    if candidate_name:
        posts = get_recent_posts(candidate_name, limit=NUMBER_OF_POSTS_TO_DISPLAY)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "scores": scores,
        "selected_candidate": candidate_name,
        "posts": posts
    })

# This endpoint will be called by the scheduler to fetch the latest posts
@app.post("/fetch-posts")
def fetch_posts_endpoint():
    candidates = CANDIDATES
    for candidate in candidates:
        posts = fetch_posts(candidate, limit=NUMBER_OF_POSTS)

        # Publish the posts to the /store-post endpoint
        qstash_client.message.publish_json(
            url=f"{os.getenv('API_BASE_URL')}/store-post",
            body={
                "posts": posts,
                "candidate": candidate
            },
            headers={"Content-Type": "application/json"},
            retries=1,
        )

# This endpoint will be used to store posts that come from /fetch-posts
@app.post("/store-post")
async def store_post_endpoint(request: Request):
    data = await request.json()

    candidate = data["candidate"]
    posts = data["posts"]

    # Iterate over the posts and store each one, while analyzing its sentiment
    for post in posts:
        print(f"Storing post: {post['title']}")
        store_post(candidate, post["title"], post["url"], 50)  # Default score of 50

        # Analyze the sentiment of the post
        qstash_client.message.publish_json(
            url=f"{os.getenv('API_BASE_URL')}/analyze-sentiment",
            body={
                "candidate": candidate,
                "title": post["title"],
                "selftext": post["selftext"]
            },
            headers={"Content-Type": "application/json"},
            retries=1,
        )

# This endpoint will be used to analyze the sentiment of a post
@app.post("/analyze-sentiment")
async def analyze_sentiment_endpoint(request: Request):
    data = await request.json()
    selftext = data["selftext"]
    candidate = data["candidate"]
    title = data["title"]

    response = analyze_sentiment(f"Candidate: {candidate}, Title: {title}, Text: {selftext}", candidate, title)

    return JSONResponse(content={"status": "Sentiment analysis started", "message_id": response})

# This endpoint will be used as the callback URL for the sentiment analysis
# It will parse the response and store the sentiment score to redis
@app.post("/sentiment-callback")
async def sentiment_callback(candidate: str, title: str, request: Request):

    # Parse the request body to JSON format
    data = await request.json()
    print(data)

    # Decode the base64-encoded 'body' field from the callback
    encoded_body = data.get('body', '')
    decoded_body = base64.b64decode(encoded_body).decode('utf-8')

    # Parse the decoded body to JSON format
    decoded_data = json.loads(decoded_body)

    # Extract the summary from the decoded response
    response = decoded_data['choices'][0]['message']['content']

    # Parse the response to extract the sentiment score
    score = parse_response(response)

    # Store the sentiment score to redis
    store_score(candidate, title, score)

    return JSONResponse(content={"status": "Sentiment score stored"})

# Function to parse the response and extract the sentiment score
def parse_response(response):
    score = float(''.join(filter(str.isdigit, response)))
    return score

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')