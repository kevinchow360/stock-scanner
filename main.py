from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import json

app = FastAPI(title="Stock Trade Scanner")

# Allow frontend to connect (update with your Render static site URL later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Signal(BaseModel):
    action: str
    symbol: str
    exchange: str | None = None
    timeframe: str
    price: float
    timestamp: str

# Simple DB setup
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

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        body = await request.body()
        data = json.loads(body.decode()) if body else await request.json()
        
        signal = {
            "action": data.get("action"),
            "symbol": data.get("symbol"),
            "exchange": data.get("exchange"),
            "timeframe": data.get("timeframe"),
            "price": float(data.get("price", 0)),
            "timestamp": data.get("timestamp"),
            "received_at": datetime.utcnow().isoformat()
        }
        
        # Save to DB
        conn.execute("""
            INSERT INTO signals (action, symbol, exchange, timeframe, price, timestamp, received_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (signal["action"], signal["symbol"], signal["exchange"], 
              signal["timeframe"], signal["price"], signal["timestamp"], signal["received_at"]))
        conn.commit()
        
        print(f"New signal received: {signal}")
        # TODO: Later add WebSocket broadcast here for live updates
        
        return {"status": "success", "signal": signal}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/signals")
def get_recent_signals(limit: int = 50):
    cursor = conn.execute("SELECT * FROM signals ORDER BY received_at DESC LIMIT ?", (limit,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)