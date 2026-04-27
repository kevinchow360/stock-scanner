from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
import json
import asyncio

app = FastAPI(title="Stock Trade Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB ----------------
conn = sqlite3.connect("signals.db", check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY,
        action TEXT,
        symbol TEXT,
        exchange TEXT,
        timeframe TEXT,
        price REAL,
        timestamp TEXT,
        received_at TEXT
    )
""")

# ---------------- WebSocket ----------------
class ConnectionManager:
    def __init__(self):
        self.active = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, msg):
        for c in self.active:
            try:
                await c.send_json(msg)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)

# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    signal = {
        "action": data.get("action"),
        "symbol": data.get("symbol"),
        "exchange": data.get("exchange"),
        "timeframe": data.get("timeframe"),
        "price": float(data.get("price", 0)),
        "timestamp": data.get("timestamp"),
        "received_at": datetime.utcnow().isoformat()
    }

    conn.execute("""
        INSERT INTO signals (action, symbol, exchange, timeframe, price, timestamp, received_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        signal["action"], signal["symbol"], signal["exchange"],
        signal["timeframe"], signal["price"],
        signal["timestamp"], signal["received_at"]
    ))
    conn.commit()

    asyncio.create_task(manager.broadcast(signal))

    return {"status": "ok", "signal": signal}

# ---------------- SIGNALS ----------------
@app.get("/signals")
def signals(limit: int = 50):
    cur = conn.execute("SELECT * FROM signals ORDER BY received_at DESC LIMIT ?", (limit,))
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

@app.get("/")
def home():
    return {"status": "running"}