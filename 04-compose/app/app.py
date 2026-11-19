import os
import socket

import psycopg
from flask import Flask, redirect, render_template, request

# L'adresse de la base est fournie par docker-compose.yml (variable d'environnement)
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)


def get_conn():
    return psycopg.connect(DATABASE_URL)


@app.get("/")
def index():
    with get_conn() as conn:
        messages = conn.execute(
            "SELECT author, content, created_at FROM messages "
            "ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    # hostname = l'ID du conteneur qui a répondu
    return render_template("index.html", messages=messages, hostname=socket.gethostname())


@app.post("/")
def post_message():
    author = request.form.get("author", "").strip()[:50] or "Anonyme"
    content = request.form.get("content", "").strip()[:500]
    if content:
        with get_conn() as conn:  # commit automatique à la sortie du bloc
            conn.execute(
                "INSERT INTO messages (author, content) VALUES (%s, %s)",
                (author, content),
            )
    return redirect("/", code=303)
