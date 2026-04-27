from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
from datetime import datetime

app = FastAPI(title="Stock Trade Scanner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup
conn = sqlite3.connect("signals.db", check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
async def receive_signal(request: Request):
    try:
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
        """, (signal["action"], signal["symbol"], signal["exchange"],
              signal["timeframe"], signal["price"], signal["timestamp"], signal["received_at"]))
        conn.commit()

        print(f"✅ New signal: {signal.get('action')} {signal.get('symbol')} on {signal.get('timeframe')}")
        return {"status": "success"}
    except Exception as e:
        print("❌ Webhook error:", e)
        return {"status": "error", "message": str(e)}

@app.get("/signals")
def get_signals(limit: int = 50):
    cursor = conn.execute("SELECT * FROM signals ORDER BY received_at DESC LIMIT ?", (limit,))
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Serve the React Dashboard
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)