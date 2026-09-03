import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.core.config import settings
from src.core.deadman_switch import deadman_switch
from src.exchange.indodax_client import indodax_client
from src.exchange.xauusd_client import xauusd_client
from src.memory.in_context_memory import in_context_memory
from src.engine.evaluator import evaluator
from src.engine.technical_analyzer import technical_analyzer

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI Expert Trading Assistant Backend & Dashboard API"
)

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class TradeRequest(BaseModel):
    pair: str
    action: str
    price: float
    amount: float

class JournalEntryRequest(BaseModel):
    market: str
    event_type: str
    macro_context: str
    market_structure: str
    pattern: str
    outcome: str
    rr_achieved: float
    confidence_rating: int
    key_takeaway: str

@app.on_event("startup")
def startup_event():
    # Arm deadman switch automatically if enabled
    if settings.ENABLE_DEADMAN_SWITCH:
        deadman_switch.arm()

@app.get("/", response_class=HTMLResponse)
def index():
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        return html_file.read_text(encoding="utf-8")
    return "<h1>AI Expert Trading Assistant API Active</h1><p>Visit /docs for API documentation.</p>"

@app.get("/api/status")
def get_system_status():
    account_info = indodax_client.get_info()
    deadman_status = deadman_switch.get_status()

    return {
        "status": "ONLINE",
        "live_trading": settings.LIVE_TRADING,
        "deadman_switch": deadman_status,
        "account": account_info,
        "confluence_weights": {
            "trend_weight": settings.WEIGHT_TREND,
            "snd_weight": settings.WEIGHT_SND,
            "macro_weight": settings.WEIGHT_MACRO
        },
        "thresholds": {
            "min_buy_score": settings.MIN_CONFLUENCE_BUY_SCORE,
            "min_sell_score": settings.MIN_CONFLUENCE_SELL_SCORE
        }
    }

@app.post("/api/deadman/heartbeat")
def deadman_heartbeat():
    deadman_switch.heartbeat()
    return {"success": True, "status": deadman_switch.get_status()}

@app.post("/api/deadman/reset")
def deadman_reset():
    deadman_switch.reset()
    return {"success": True, "message": "Deadman Switch reset and re-armed.", "status": deadman_switch.get_status()}

@app.post("/api/deadman/toggle")
def deadman_toggle(arm: bool = True):
    if arm:
        deadman_switch.arm()
    else:
        deadman_switch.disarm()
    return {"success": True, "status": deadman_switch.get_status()}

@app.get("/api/ticker")
def get_ticker(pair: str = "btc_idr"):
    pair_lower = pair.lower()
    if "xau" in pair_lower or "gold" in pair_lower:
        return xauusd_client.get_ticker()
    return indodax_client.get_ticker(pair_lower)

@app.get("/api/klines")
def get_klines(pair: str = "btc_idr", timeframe: str = "1h", limit: int = 1500):
    pair_lower = pair.lower()
    if "xau" in pair_lower or "gold" in pair_lower:
        candles = xauusd_client.get_klines(timeframe=timeframe, limit=limit)
    else:
        candles = indodax_client.get_klines(pair=pair_lower, timeframe=timeframe, limit=limit)

    if candles and len(candles) >= 5:
        try:
            df = technical_analyzer.compute_indicators(candles)
            df["ema18"] = df["ema18"].fillna(df["close"])
            df["ema50"] = df["ema50"].fillna(df["close"])
            df = df.fillna(0.0)
            return df.to_dict(orient="records")
        except Exception as e:
            return candles
    return candles

@app.get("/api/depth")
def get_depth(pair: str = "btc_idr"):
    pair_lower = pair.lower()
    if "xau" in pair_lower or "gold" in pair_lower:
        ticker = xauusd_client.get_ticker()
        px = ticker["last"]
        return {
            "buy": [[round(px - (0.3 * (i + 1)), 2), round(1.2 + (0.4 * i), 2)] for i in range(12)],
            "sell": [[round(px + (0.3 * (i + 1)), 2), round(1.2 + (0.4 * i), 2)] for i in range(12)]
        }
    return indodax_client.get_depth(pair_lower)

@app.get("/api/trades")
def get_trades(pair: str = "btc_idr"):
    pair_lower = pair.lower()
    if "xau" in pair_lower or "gold" in pair_lower:
        ticker = xauusd_client.get_ticker()
        px = ticker["last"]
        now = int(time.time())
        return [
            {"date": str(now - (i * 12)), "price": str(round(px + (0.15 * ((-1)**i) * i), 2)), "amount": str(round(0.8 + 0.3 * i, 2)), "tid": str(now - i), "type": "buy" if i % 2 == 0 else "sell"}
            for i in range(10)
        ]
    trades = indodax_client.get_trades(pair_lower)
    if not trades:
        ticker = indodax_client.get_ticker(pair_lower)
        px = ticker["last"]
        now = int(time.time())
        trades = [
            {"date": str(now - (i * 15)), "price": str(int(px * (1 + 0.0005 * ((-1)**i)))), "amount": str(round(0.015 + 0.008 * i, 4)), "tid": str(now - i), "type": "buy" if i % 2 == 0 else "sell"}
            for i in range(10)
        ]
    return trades

@app.get("/api/orders")
def get_orders():
    return {
        "open_orders": indodax_client.get_open_orders(),
        "recent_history": indodax_client.paper_orders[-15:] if hasattr(indodax_client, "paper_orders") else []
    }

@app.get("/api/evaluate")
def evaluate_market(pair: str = "btc_idr", timeframe: str = "1h"):
    deadman_switch.heartbeat()
    eval_result = evaluator.evaluate_pair(pair=pair, timeframe=timeframe, print_report=True)
    return eval_result

@app.post("/api/trade")
def execute_trade(req: TradeRequest):
    deadman_switch.heartbeat()
    if "xau" in req.pair.lower():
        return {
            "success": False,
            "error": "XAUUSD is in analytical mode; execute on your broker."
        }

    res = indodax_client.create_order(
        pair=req.pair,
        order_type=req.action.lower(),
        price=req.price,
        amount=req.amount
    )
    return res

@app.get("/api/memory/journal")
def get_journal():
    return in_context_memory.journal_entries

@app.post("/api/memory/journal")
def add_journal(entry: JournalEntryRequest):
    entry_dict = entry.model_dump()
    entry_dict["id"] = f"JRN-{len(in_context_memory.journal_entries) + 1:03d}"
    success = in_context_memory.add_journal_entry(entry_dict)
    return {"success": success, "entry": entry_dict}

@app.post("/api/memory/upload-chart")
async def upload_chart_image(file: UploadFile = File(...)):
    contents = await file.read()
    res = in_context_memory.analyze_chart_image(contents)
    return res

@app.post("/api/memory/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    import io
    contents = await file.read()
    buffer = io.BytesIO(contents)
    res = in_context_memory.parse_historical_csv(buffer)
    return res
