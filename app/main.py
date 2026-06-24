from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect('/home/connormunger/tcg-app/tcg.db')
    conn.row_factory = sqlite3.Row 
    return conn

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "message": "TCG app backend is online!"}

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
