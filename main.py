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

class CustomerRQ(BaseModel):
    company: str = ''
    address: str = ''
    city: str = ''
    state: str = ''
    country: str = ''
    postalcode: str = ''
    fax: str = ''

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
        raise HTTPException(status_code=404, detail={"error": "No composer to be found"})
    return composer_tracks

@app.post("/albums")
async def add_album(request: AlbumRQ, response: Response):
    app.db_connection.row_factory = sqlite3.Row
    artist_check = app.db_connection.execute(
        "SELECT * FROM albums WHERE artistid = ? LIMIT 1", (request.artist_id, )).fetchall()
    if artist_check==[]:
        raise HTTPException(status_code=404, detail={"error": "No artist with such ID"})
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

@app.put("/customers/{customer_id}")
async def edit_customer(customer_id: int, request: CustomerRQ):
    app.db_connection.row_factory = sqlite3.Row
    customer_check = app.db_connection.execute(
        "SELECT * FROM customers WHERE CustomerId = ? LIMIT 1", (customer_id,)).fetchall()
    if customer_check == []: raise HTTPException(status_code=404, detail={"error": "No customer with such ID"})
    update_data = request.dict(exclude_unset=True)
    for item in update_data:
        app.db_connection.execute(f'UPDATE customers SET {item} = "{update_data[item]}" WHERE CustomerId = {customer_id}')
    return app.db_connection.execute("SELECT * FROM customers WHERE CustomerId = ?",(customer_id,)).fetchone()

@app.get("/sales")
async def get_sales(category: str):
    if category=='customers':
        app.db_connection.row_factory = sqlite3.Row
        data = app.db_connection.execute(
            "SELECT customers.CustomerId,customers.Email,customers.Phone, "
            "ROUND(SUM(invoices.Total),2) Sum FROM invoices "
            "INNER JOIN customers ON invoices.CustomerId = customers.CustomerId "
            "GROUP BY customers.CustomerId,customers.Email,customers.Phone "
            "ORDER BY Sum DESC, customers.CustomerId").fetchall()
        return data
    elif category=='genres':
        app.db_connection.row_factory = sqlite3.Row
        data = app.db_connection.execute(
            "SELECT genres.Name, SUM(invoice_items.Quantity) AS SUM FROM genres"
            "INNER JOIN tracks ON tracks.GenreId = genres.GenreId"
            "INNER JOIN invoice_items ON invoice_items.TrackId = tracks.TrackId"
            "GROUP BY genres.Name ORDER BY Sum DESC, genres.Name ").fetchall()
        return data
    else: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "No category to be found"})
