from hashlib import sha256
from fastapi import FastAPI, Response, Request, Cookie, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import secrets
import sqlite3

app = FastAPI()

@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')

@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()

@app.get("/tracks")
async def get_tracks_page(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    tracks_page = app.db_connection.execute(
        "SELECT * FROM tracks LIMIT ? OFFSET ?", (per_page, per_page*page)).fetchall()
    return tracks_page
