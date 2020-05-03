from hashlib import sha256
from fastapi import FastAPI, Response, Request, Cookie, HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import secrets
import sqlite3

app = FastAPI()

class AlbumRQ(BaseModel):
    title: str
    artist_id: int

@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect('chinook.db')

@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()

@app.get("/")
async def hello():
    return{
        "message":"Hello There"
    }

@app.get("/tracks")
async def get_tracks_page(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    tracks_page = app.db_connection.execute(
        "SELECT * FROM tracks LIMIT ? OFFSET ?", (per_page, per_page*page)).fetchall()
    return tracks_page

@app.get("/tracks/composers/")
async def get_composer_tracks(composer_name: str):
    app.db_connection.row_factory = lambda cursor, x: x[0]
    composer_tracks = app.db_connection.execute(
        "SELECT Name FROM tracks WHERE Composer = ? ORDER BY Name", (composer_name, )).fetchall()
    if composer_tracks==[]:
        raise HTTPException(status_code=404, detail=json.dumps({"error": "No composer to be found"}))
    return composer_tracks

@app.post("/albums")
async def add_album(request: AlbumRQ, response: Response):
    app.db_connection.row_factory = sqlite3.Row
    artist_check = app.db_connection.execute(
        "SELECT * FROM albums WHERE artistid = ? LIMIT 1", (request.artist_id, )).fetchall()
    if artist_check==[]:
        raise HTTPException(status_code=404, detail=json.dumps({"error": "No artist with such ID"}))
    app.db_connection.execute(
        "INSERT INTO albums (artistid, title) VALUES (?,?)",(request.artist_id,request.title,))
    album = app.db_connection.execute("SELECT * FROM albums WHERE artistid = ? ORDER BY AlbumId DESC",(request.artist_id,)).fetchone()
    response.status_code = 201
    return album

@app.get("/albums/{album_id}")
async def get_album(album_id: int):
    app.db_connection.row_factory = sqlite3.Row
    return app.db_connection.execute(
        "SELECT * FROM albums WHERE AlbumId = ?",(album_id,)).fetchone()
