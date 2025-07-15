from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "reviews.db")

app = FastAPI()


# бдшка
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )
        conn.commit()


init_db()

# анализ текста (хорошо или плохо)
POSITIVE = ["хорош", "люблю"]
NEGATIVE = ["плохо", "ненавиж"]


def analyze_sentiment(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in POSITIVE):
        return "positive"
    if any(word in lowered for word in NEGATIVE):
        return "negative"
    return "neutral"


# модели
class ReviewIn(BaseModel):
    text: str


class ReviewOut(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str


# ручки
@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewIn):
    sentiment = analyze_sentiment(review.text)
    created_at = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",  # noqa: E501
            (review.text, sentiment, created_at),
        )
        review_id = cursor.lastrowid
        conn.commit()
    return ReviewOut(
        id=review_id, text=review.text, sentiment=sentiment, created_at=created_at
    )


@app.get("/reviews", response_model=List[ReviewOut])
def get_reviews(sentiment: str = None):
    query = "SELECT * FROM reviews"
    params = ()
    if sentiment:
        query += " WHERE sentiment = ?"
        params = (sentiment,)
    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [ReviewOut(**dict(row)) for row in rows]
