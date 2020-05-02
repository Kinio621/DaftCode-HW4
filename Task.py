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


@app.get("/")
async def root():
    cursor = app.db_connection.cursor()
    tracks = cursor.execute("SELECT name FROM tracks").fetchall()
    return {
        "tracks":tracks,
    }

@app.get("/tracks")
async def single_track(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute(
        "SELECT Trackid, Name, AlbumId, MediaTypeId, GenreId, Composer, Milliseconds, Bytes, UnitPrice FROM tracks ORDERBY Trackid LIMIT ? OFFSET ?", (per_page, per_page*page)).fetchone()

    return data
