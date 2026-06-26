import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from fastapi import Request
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3

app = FastAPI()

load_dotenv()

# Enables secure cookies
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "fallback-secret"))

# Setup Google OAuth
oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    client_kwargs={'scope': 'openid email profile'}
)

# Tell FastAPI to serve everything in the static folder publicly at the /static URL
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def get_db_connection():
    conn = sqlite3.connect('/home/connormunger/tcg-app/tcg.db')
    conn.row_factory = sqlite3.Row 
    return conn

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "TCG app backend is online!"}

@app.get("/auth/login")
async def login(request: Request):
    # This URL must exactly match what you put in the Google Cloud Console
    redirect_uri = "https://connormunger.com/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = token.get('userinfo')
    if user:
        request.session['user'] = user
    return RedirectResponse(url='/')

@app.get("/auth/logout")
def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get("/api/me")
def get_me(request: Request):
    user = request.session.get('user')
    if not user:
        return {"logged_in": False}
    
    email = user.get('email')
    
    # Check if this email matches a friend in your database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE email = ?", (email,))
    db_user = cursor.fetchone()
    conn.close()

    if db_user:
        return {"logged_in": True, "name": db_user['name'], "email": email}
    else:
        # Logged in to Google, but not in your database
        return {"logged_in": False, "error": "Unauthorized email"}

@app.get("/api/inventory")
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.set_code, 
            c.collector_number, 
            c.name as card_name,
            c.tcgplayer_id,
            c.is_alt_art, 
            c.is_signature, 
            c.is_overnumbered,
            i.quantity, 
            i.is_holo, 
            i.is_promo,
            u.name as owner_name,
            (SELECT price FROM price_history ph WHERE ph.card_id = c.id AND ph.is_holo = i.is_holo ORDER BY ph.updated_at DESC LIMIT 1) as price
        FROM inventory i
        JOIN cards c ON i.card_id = c.id
        JOIN users u ON i.user_id = u.id
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/api/logs")
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            t.created_at as timestamp,
            t.event_type,
            c.name as card_name,
            c.set_code,
            c.collector_number,
            c.is_overnumbered,
            t.is_holo,
            t.is_promo,
            u.name as owner_name,
            t.borrower_name as borrower,
            t.quantity,
            t.notes
        FROM transaction_log t
        JOIN cards c ON t.card_id = c.id
        JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- NEW ROUTES FOR THE FRONTEND ---

# Mount the static folder so any linked CSS/JS files work
app.mount("/static", StaticFiles(directory="/home/connormunger/tcg-app/app/static"), name="static")

# Serve index.html when visiting the root URL
@app.get("/")
def serve_frontend():
    return FileResponse("/home/connormunger/tcg-app/app/static/index.html")
