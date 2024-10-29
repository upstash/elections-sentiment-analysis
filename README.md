# 2024 US Elections Sentiment Analysis Using Reddit Posts with QStash and Upstash Redis

## Overview

This project analyzes public sentiment toward U.S. political candidates by gathering and scoring Reddit posts related to them. We use **QStash** to periodically fetch posts about each candidate, analyze their sentiment, and calculate sentiment scores, storing these in **Upstash Redis**.

### Data Collection

Using QStash, we define a schedule to periodically fetch posts about each candidate from Reddit. The destination URL is set to the `fetch-posts` endpoint, which handles data collection.

Every 10 minutes, we retrieve 10 "hot" and 10 "relevant" posts with 10 or more upvotes about each candidate posted in the last hour. Posts already in the database with a valid score (between 0 and 100) are skipped. Otherwise, they are stored in the database with a default invalid score of -1 and sent to the `analyze-sentiment` endpoint.

Only the latest 50 posts are stored in the database to track sentiment trends over time.

### Sentiment Analysis

Once a post reaches the `analyze-sentiment` endpoint, its sentiment is analyzed using OpenAI's `gpt-4-turbo` model. We use QStash's LLM integration, allowing us to define a callback URL triggered when the model finishes processing the input. This callback URL, set to the `sentiment-callback` endpoint, receives the encoded sentiment score and updates the post’s score in the database.

If sentiment analysis fails, and the same post is encountered again in a future fetch, we retry the sentiment analysis.

### Calculating Candidate Scores

To calculate and update candidate scores, we define a schedule using QStash to run the calculations. The destination URL is set to the `update-scores` endpoint, responsible for score calculation and storage.

Every hour, we calculate the average sentiment score of the latest 50 posts for each candidate and store the scores in the database. Only the latest 100 scores for each candidate are retained.

Posts with invalid scores are not included in candidate score calculations.

Occasionally, this update operation fails due to random errors, such as function timeouts. When this occurs, the score update may succeed for one candidate and not the other. To address this, we use QStash's failure callback feature, defining a failure callback URL triggered if the operation fails. This callback URL, set to the `update-scores-failed` endpoint, ensures score history consistency across all candidates.

### Displaying Candidate Scores and Posts

The candidate scores are displayed on a line chart with each color representing a different candidate. The x-axis represents the time, and the y-axis represents the sentiment score. The chart is updated every hour to reflect the latest scores.

Below the chart, the latest 10 posts for each candidate are displayed, including the post title, post URL, and sentiment score. You can click on the post title to view the post on Reddit.

Sometimes these URLs may take you to news articles or other external sources. This happens because some Reddit posts link to external content, which is not always a direct link to the post itself.

## How to Run

### Installation

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

### Usage

1. **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```
