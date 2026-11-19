import os
import socket

import redis
from flask import Flask

app = Flask(__name__)

cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=6379,
    password=os.environ.get("REDIS_PASSWORD") or None,
    decode_responses=True,
)


@app.get("/")
def index():
    visites = cache.incr("visites")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Compteur</title></head>
<body style="font-family: system-ui, sans-serif; text-align: center; margin-top: 15vh;">
  <h1>{visites}</h1>
  <p>visites depuis la mise en service</p>
  <p style="color: #888; font-size: .8rem;">Servi par le conteneur {socket.gethostname()}</p>
</body>
</html>"""
