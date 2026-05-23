FROM python:3.11-slim as builder

#wchodzimy do folderu app i kopiujemy tylko plik requirements.txt
WORKDIR /app 
COPY requirements.txt .

# tworzymy wirtualne środowisko (venv) i ładujemy tam wszystkie pakiety
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# znów zaczynamy od FROM czyli wyrzucamy do kosza kontener z poprzedniego etapu
FROM python:3.11-slim

# kopiujemy tylko gotowe biblioteki z etapu 1
WORKDIR /app
# instalacju curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# na koniec  kopiujemy plik main.py
COPY main.py .

# brak root, tworzymy zwykłego użytkownika i przełączmy się na niego
RUN useradd -m student
USER student

# uvicorn nasłuchuje na portach sieciowych
# 0.0.0.0 oznacza że aplikacja będzie nasłuchiwać na wszystkich interfejsach wewnątrz swojej sieci izolowanej
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]