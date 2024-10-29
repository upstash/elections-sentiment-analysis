# US Elections Sentiment Analysis

## Overview

This project tries to analyze the public sentiment around U.S. political candidates by gathering and scoring posts related to them on Reddit. We use **QStash** to periodically fetch posts about each candidate, analyze their sentiment, and calculate sentiment scores for each candidate. The posts and scores are stored in **Upstash Redis**.

### Data Collection

We define a schedule using QStash to periodically fetch posts about each candidate from Reddit. The destination URL is set to the `fetch-posts` endpoint, which is responsible for the data collection.

Every 10 minutes, we fetch 10 "hot" posts and 10 "relevant" posts posted in the last hour about each candidate from Reddit. If these posts are already in the database, and they have a valid score (between 0 and 100), they are skipped. Otherwise, the posts are stored in the database with a default invalid score of -1 and they are sent to the `analyze-sentiment` endpoint.

Only the latest 50 posts are stored in the database to see a trend of the sentiment over time.

### Sentiment Analysis

Once a post reaches the `analyze-sentiment` endpoint, its sentiment is analyzed using OpenAI's `gpt-3.5-turbo` model. We used QStash's LLM integration which allows us to define a callback URL that is triggered when the model finishes processing the input. The callback URL is set to the `sentiment-callback` endpoint, which receives the encoded sentiment score from QStash and updates the post's score in the database.

If the sentiment analysis fails, but we encounter the same post again in a future fetch, we retry the sentiment analysis.

### Calculating Candidate Scores

To calculate and update the candidate scores, we define a schedule using QStash to periodically calculate and update the scores. The destination URL is set to the `update-scores` endpoint, which is responsible for the calculation and storage of the candidate scores.

Every hour, we calculate the average sentiment score of the latest 50 posts for each candidate. We then store the scores in the database. We only keep the latest 100 scores for each candidate. 

The posts with invalid scores are not included in the calculation of the candidate scores.

Sometimes this updating operation fails due to random errors such as function timeouts. In such cases the score update may happen for one candidate and not the other. To handle this situation we use QStash's failure callback feature. When defining a schedule with QStash we can also define a failure callback URL that is triggered when the operation fails. The callback URL is set to the `update-scores-failed` endpoint, which makes sure that the score history is consistent for all candidates.

# How to Run

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/upstash/elections-sentiment-analysis.git
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```