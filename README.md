# US Elections FastAPI Project

## Overview
This project is a FastAPI application designed to provide information and analytics about US elections using Reddit posts.

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