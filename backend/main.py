from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import redis
import os

app = FastAPI()

DB_URL = os.getenv("DATABASE_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "cache")

# FastAPI samo sprawdza czy to co ktoś wysłał to słownik i czy ma pole content a w nim jakiś string
class Note(BaseModel):
    content: str

# tworzenie tabeli notes przy starcie, o ile już nie istnieje
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
    # produkcyjna wersja otwierałaby szybkie połączenie z bazą i wysyłała SELECT 1 + wysyłała ping do Redisa
    return {"status": "OK"}

@app.post("/notes")
def add_note(note: Note):
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO notes (content) VALUES (%s) RETURNING id", (note.content,))
    note_id = cursor.fetchone()[0] # RETURNING id daje nam możliwość pobrania id ze zwracanej krotki w ten prosty sposób
    connection.commit()
    cursor.close()
    connection.close()
    
    # inkrementacja licznika w Redis
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True) # redis zapisuje i zwraca wszystko jako surowe bajty więc dekodujemy
    r.incr("notes_count") # NIE używając get(), zwiększania o 1 i potem set(), zapobiegamy race condition
    
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
    return {"redis_total_created": count, "postgres_notes": notes_list}