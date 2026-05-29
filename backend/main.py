from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import redis
import os

app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "cache")

class Note(BaseModel):
    content: str

@app.on_event("startup")
def startup_event():
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()

@app.get("/health")
def health_check():
    return {"status": "OK"}

@app.post("/notes")
def add_note(note: Note):
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO notes (content) VALUES (%s) RETURNING id", (note.content,))
    note_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.incr("notes_count")
    
    return {"id": note_id, "message": "Zapisano i policzono w cache"}

@app.get("/notes")
def get_notes():
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    cursor.execute("SELECT id, content FROM notes")
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    count = r.get("notes_count") or 0
    
    notes_list = [{"id": row[0], "content": row[1]} for row in rows]
    return {"redis_session_counter": count, "postgres_notes": notes_list}