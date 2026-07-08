#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D-finans Live Backend
---------------------
Bu dosya iPhone uygulamasının bağlanacağı canlı backend'dir.

ÖNEMLİ:
- API anahtarlarını ASLA Swift içine yazma.
- Anahtarları Terminal'de environment variable olarak ver.
- İlk testlerde LIVE_TRADING=false kullan.

Kurulum:
    python3 -m pip install flask flask-cors requests

Çalıştırma:
    export BINANCE_LIVE_API_KEY="BURAYA_API_KEY"
    export BINANCE_LIVE_SECRET_KEY="BURAYA_SECRET_KEY"
    export BINANCE_LIVE_TRADING="false"
    python3 dfinans_live_backend.py

Railway için Procfile:
    web: gunicorn dfinans_live_backend:app --bind 0.0.0.0:$PORT
"""

from __future__ import annotations

import os
import asyncio
import hmac
import time
import json
import math
import uuid
import queue
import sqlite3
import hashlib
import smtplib
import threading
from email.mime.text import MIMEText
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

APP_NAME = "D-finans Live Backend"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", os.getenv("DFINANS_BACKEND_PORT", "5055")))

BINANCE_API_KEY = os.getenv("BINANCE_LIVE_API_KEY", os.getenv("BINANCE_API_KEY", ""))
BINANCE_SECRET_KEY = os.getenv("BINANCE_LIVE_SECRET_KEY", os.getenv("BINANCE_SECRET_KEY", ""))
LIVE_TRADING = os.getenv("BINANCE_LIVE_TRADING", os.getenv("LIVE_TRADING", "false")).lower() == "true"
IBKR_ENABLED = os.getenv("IBKR_ENABLED", "false").lower() == "true"  # Disabled by default; VPS connectivity issues
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "21"))
IBKR_ACCOUNT = os.getenv("IBKR_ACCOUNT", "")
IBKR_KEEPALIVE_SEC = int(os.getenv("IBKR_KEEPALIVE_SEC", "20"))
IBKR_LIVE_TRADING = os.getenv("IBKR_LIVE_TRADING", "false").lower() == "true"
AUTO_TRADER_ENABLED = os.getenv("AUTO_TRADER_ENABLED", "false").lower() == "true"
AUTO_TRADER_MODE = os.getenv("AUTO_TRADER_MODE", "paper").lower()
RUNTIME_DB_PATH = os.getenv("DFINANS_RUNTIME_DB_PATH", "/data/dfinans_runtime.db" if os.path.isdir("/data") else "/tmp/dfinans_runtime.db")
BINANCE_PROXY_BASE_URL = os.getenv("BINANCE_PROXY_BASE_URL", "").rstrip("/")
BINANCE_PROXY_TOKEN = os.getenv("BINANCE_PROXY_TOKEN", "")
# Emir (order) islemleri icin ayri bir proxy hedefi tanimlanabilir. VPS'teki bazi
# proxy servisleri sadece okuma (balance/positions) route'larina sahipken, emir
# gonderme route'lari (/binance/private/order, /manual-order, /close-position)
# baska bir instance'da olabilir. Ayarlanmazsa BINANCE_PROXY_BASE_URL kullanilir.
BINANCE_ORDER_PROXY_BASE_URL = os.getenv("BINANCE_ORDER_PROXY_BASE_URL", "").rstrip("/") or BINANCE_PROXY_BASE_URL
BINANCE_PROXY_TIMEOUT = int(os.getenv("BINANCE_PROXY_TIMEOUT", "12"))
PUBLIC_HTTP_TIMEOUT = int(os.getenv("PUBLIC_HTTP_TIMEOUT", "5"))
SIGNED_HTTP_TIMEOUT = int(os.getenv("SIGNED_HTTP_TIMEOUT", "8"))

# === PORTFOLIO CACHE (60 seconds TTL) ===
_portfolio_cache = {"data": None, "expires_at": 0}
_cache_lock = threading.Lock()

def get_cached_portfolio() -> Optional[Dict[str, Any]]:
    global _portfolio_cache
    with _cache_lock:
        if _portfolio_cache["data"] and time.time() < _portfolio_cache["expires_at"]:
            return _portfolio_cache["data"]
    return None

def set_cached_portfolio(data: Dict[str, Any], ttl_seconds: int = 60):
    global _portfolio_cache
    with _cache_lock:
        _portfolio_cache["data"] = data
        _portfolio_cache["expires_at"] = time.time() + ttl_seconds

# Railway / cloud IP bloklarında Binance bazen ana endpoint'i 451 ile engelleyebiliyor.
# Not: api1/fapi1/api2/fapi2/api3/fapi3 gibi numaralı mirror'lar bazı VPS IP'lerinden
# POST (emir) isteklerinde 302 redirect (www.binance.com'a) dönebiliyor; bu durumda
# requests kütüphanesi redirect'i otomatik takip edip boş/HTML gövdeli 2xx sonuç
# üretiyor ve bu yanlışlıkla "başarı" sanılabiliyor. Bu yüzden resmi (numarasız)
# endpoint'i öncelikli yapıyoruz, numaralı mirror'ları sadece fallback olarak tutuyoruz.
SPOT_BASE = os.getenv("BINANCE_SPOT_BASE", "https://api.binance.com")
FUTURES_BASE = os.getenv("BINANCE_FUTURES_BASE", "https://fapi.binance.com")
SPOT_BASES = [SPOT_BASE, "https://api1.binance.com", "https://api2.binance.com", "https://api3.binance.com"]
FUTURES_BASES = [FUTURES_BASE, "https://fapi1.binance.com", "https://fapi2.binance.com", "https://fapi3.binance.com"]

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
COINBASE_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD",
    "XRPUSDT": "XRP-USD",
    "ADAUSDT": "ADA-USD",
}
COINGECKO_MAP = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "BNBUSDT": "binancecoin",
    "XRPUSDT": "ripple",
    "ADAUSDT": "cardano",
}
YAHOO_MAP = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD",
    "XRPUSDT": "XRP-USD",
    "ADAUSDT": "ADA-USD",
    "XAUUSD": "GC=F",
    "VNQ": "VNQ",
    "VIX": "^VIX",
    "NASDAQ": "^IXIC",
    "SP500": "^GSPC",
    "DXY": "DX-Y.NYB",
    "GOLD": "GC=F",
    "OIL": "CL=F",
    "US10Y": "^TNX",
}

app = Flask(__name__)
CORS(app)


@app.after_request
def apply_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

state_lock = threading.Lock()


@dataclass
class EngineState:
    enabled: bool = False
    last_update: str = ""
    last_symbol: str = "ETHUSDT"
    last_market: str = "FUTURES"
    last_signal: str = "WAIT"
    confidence: int = 0
    reason: str = "AI motoru henüz karar üretmedi."
    daily_trade_count: int = 0
    max_daily_trades: int = 3
    risk_profile: str = "Dengeli"
    live_trading: bool = LIVE_TRADING


ENGINE = EngineState()
TRADE_LOG: List[Dict[str, Any]] = []
DB_LOCK = threading.Lock()


@dataclass
class AutoTraderState:
    enabled: bool = AUTO_TRADER_ENABLED
    mode: str = AUTO_TRADER_MODE if AUTO_TRADER_MODE in ["paper", "live"] else "paper"
    broker: str = "BINANCE"
    symbol: str = "ETHUSDT"
    # Cok sembollu tarama listesi: doluysa auto_trader_cycle her dongude 'symbol'
    # yerine bu listedeki TUM sembolleri tek tek tarar ve uygun olanlarda islem acar.
    # Bos birakilirsa geriye donuk uyumluluk icin sadece 'symbol' kullanilir.
    symbols: List[str] = field(default_factory=list)
    market: str = "FUTURES"
    asset_type: str = "STK"
    exchange: str = "SMART"
    currency: str = "USD"
    quantity: float = 0.01
    interval_sec: int = 20
    min_confidence: int = 67
    evaluation_window_sec: int = 300
    max_daily_trades: int = 5
    daily_trade_count: int = 0
    last_action: str = "WAIT"
    last_confidence: int = 0
    last_reason: str = "Auto trader henüz başlamadı."
    last_price: float = 0.0
    last_update: str = ""
    last_error: str = ""
    updated_at_epoch: float = 0.0


AUTO_TRADER = AutoTraderState()
AUTO_LOCK = threading.Lock()
AUTO_HISTORY: List[Dict[str, Any]] = []

# Varsayilan cok-sembol tarama listeleri (env ile ozellestirilebilir, virgullu).
# Kullanici basta "havuzdaki tum varliklar taransin" seklinde kurulmasini istemisti;
# tek sembole (ETHUSDT/AAPL) daralmis olmasi bir gerileme idi - simdi geri getirildi.
_BINANCE_WATCHLIST_DEFAULT = "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT,DOGEUSDT,ADAUSDT,AVAXUSDT"
_IBKR_WATCHLIST_DEFAULT = "AAPL,MSFT,NVDA,AMD,TSLA,F,T,IBKR"


def _parse_symbol_list(raw: str) -> List[str]:
    return [str(s.strip()).upper().replace("/", "").replace("-", "") for s in raw.split(",") if s.strip()]


AUTO_TRADER.symbols = _parse_symbol_list(os.getenv("BINANCE_AUTO_WATCHLIST", _BINANCE_WATCHLIST_DEFAULT))

# IBKR icin bagimsiz, Binance'tan tamamen ayri calisan ikinci bir auto-trader ornegi.
# Eskiden tek bir global AUTO_TRADER/broker alani vardi ve varsayilan olarak "BINANCE"a
# ayarliydi - yani IBKR icin auto-trader hicbir zaman calismiyordu (kullanici broker'i
# manuel olarak "IBKR" yapip Binance'i durdurmadan ikisini ayni anda calistiramazdi).
# Bu yuzden "IBKR hala pozisyon acmadi" sikayeti tamamen dogruydu: IBKR tarafinda islem
# mantigi calisir durumda degildi. Simdi Binance ve IBKR es zamanli, birbirinden bagimsiz
# calisiyor.
IBKR_AUTO_TRADER = AutoTraderState()
IBKR_AUTO_TRADER.broker = "IBKR"
IBKR_AUTO_TRADER.symbol = os.getenv("IBKR_AUTO_SYMBOL", "AAPL")
IBKR_AUTO_TRADER.symbols = _parse_symbol_list(os.getenv("IBKR_AUTO_WATCHLIST", _IBKR_WATCHLIST_DEFAULT))
IBKR_AUTO_TRADER.market = "IBKR"
IBKR_AUTO_TRADER.asset_type = "STK"
IBKR_AUTO_TRADER.exchange = "SMART"
IBKR_AUTO_TRADER.currency = "USD"
IBKR_AUTO_TRADER.quantity = float(os.getenv("IBKR_AUTO_QUANTITY", "1"))
IBKR_AUTO_TRADER.min_confidence = int(os.getenv("IBKR_AUTO_MIN_CONFIDENCE", "60"))
IBKR_AUTO_TRADER.interval_sec = int(os.getenv("IBKR_AUTO_INTERVAL_SEC", "30"))
IBKR_AUTO_TRADER.mode = AUTO_TRADER.mode
IBKR_AUTO_TRADER.enabled = os.getenv("IBKR_AUTO_TRADER_ENABLED", "true").lower() == "true"
IBKR_AUTO_LOCK = threading.Lock()
IBKR_AUTO_HISTORY: List[Dict[str, Any]] = []

# Binance SPOT icin de Futures'tan tamamen bagimsiz ucuncu bir auto-trader ornegi.
# Futures kaldiracli/short calisirken, spot sadece "elde tutulan varligi al/sat"
# mantigiyla calisir: BUY -> USDT ile varlik satin alinir (pozisyon acilir),
# SELL -> sadece zaten sahip olunan miktar varsa satilir (short mumkun degil).
SPOT_AUTO_TRADER = AutoTraderState()
SPOT_AUTO_TRADER.broker = "BINANCE_SPOT"
SPOT_AUTO_TRADER.market = "SPOT"
SPOT_AUTO_TRADER.symbol = "ETHUSDT"
SPOT_AUTO_TRADER.symbols = _parse_symbol_list(os.getenv("BINANCE_SPOT_AUTO_WATCHLIST", _BINANCE_WATCHLIST_DEFAULT))
SPOT_AUTO_TRADER.min_confidence = int(os.getenv("BINANCE_SPOT_AUTO_MIN_CONFIDENCE", "67"))
SPOT_AUTO_TRADER.interval_sec = int(os.getenv("BINANCE_SPOT_AUTO_INTERVAL_SEC", "25"))
SPOT_AUTO_TRADER.max_daily_trades = int(os.getenv("BINANCE_SPOT_AUTO_MAX_DAILY_TRADES", "5"))
SPOT_AUTO_TRADER.mode = AUTO_TRADER.mode
SPOT_AUTO_TRADER.enabled = os.getenv("BINANCE_SPOT_AUTO_TRADER_ENABLED", "true").lower() == "true"
SPOT_AUTO_LOCK = threading.Lock()
SPOT_AUTO_HISTORY: List[Dict[str, Any]] = []
# Her sembol icin bosta bekleyen spot USDT bakiyesinin ne kadari kullanilsin
# (Futures'taki AUTO_TRADER_SIZE_PCT_* mantiginin spot karsiligi).
SPOT_AUTO_SIZE_PCT_BTC = float(os.getenv("BINANCE_SPOT_SIZE_PCT_BTC", "20.0")) / 100.0
SPOT_AUTO_SIZE_PCT_ETH = float(os.getenv("BINANCE_SPOT_SIZE_PCT_ETH", "15.0")) / 100.0
SPOT_AUTO_SIZE_PCT_DEFAULT = float(os.getenv("BINANCE_SPOT_SIZE_PCT_DEFAULT", "8.0")) / 100.0


# Mobil uygulamanin /ai-status ve /ai-control endpoint'lerinin bekledigi basit
# 3 durumlu (off/watch/auto) mod. AUTO_TRADER.enabled sadece acik/kapali bilgisini
# tasidigi icin "watch" (izleme, emir yok) durumunu ayrica saklamamiz gerekiyor.
AI_UI_MODE: Dict[str, str] = {"mode": "off"}
SIGNAL_QUEUE: List[Dict[str, Any]] = []
LEARNING_STATS: Dict[str, Dict[str, int]] = {
    "BUY": {"wins": 0, "losses": 0},
    "SELL": {"wins": 0, "losses": 0},
}
IBKR_RUNTIME: Dict[str, Any] = {
    "ib": None,
    "ibs": None,
    "connected": False,
    "last_ok": "",
    "last_error": "",
    "reconnect_count": 0,
    "failed_attempts": 0,
    "last_fail_time": 0,
    "circuit_breaker_open": False,
}
IBKR_LOCK = threading.RLock()  # RLock: ibkr_execute + ensure_ibkr_connection ayni thread'de ic ice kilit alabiliyor
KEEPALIVE_THREAD_STARTED = False
AUTO_THREAD_STARTED = False
IBKR_WORKER_THREAD_STARTED = False
# Tum IBKR (ib_insync) islemleri, kac tane paralel Flask/gunicorn thread'i olursa
# olsun, DAIMA bu TEK kuyruk uzerinden TEK bir adanmis worker thread'de calisir.
# ib_insync'in IB client'i, connect edildigi thread'in asyncio event loop'una
# baglidir; farkli thread'lerden dogrudan cagrilirsa (ozellikle gunicorn
# --threads arttirilinca) client-id celismesi ve tum servisin cokmesiyle
# sonuclanan ciddi kilitlenmeler/hatalar olusuyordu. Kuyruk + tek worker
# thread modeli bunu kokten cozer.
IBKR_TASK_QUEUE: "queue.Queue" = queue.Queue()

# Risk management state
DAILY_REALIZED_PNL = 0.0
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "-500.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "5"))
LAST_ORDER_TIME: Dict[str, float] = {}
MIN_ORDER_COOLDOWN_SEC = float(os.getenv("MIN_ORDER_COOLDOWN_SEC", "2.0"))
BINANCE_TAKE_PROFIT_PCT = float(os.getenv("BINANCE_TAKE_PROFIT_PCT", "5.0"))
BINANCE_STOP_LOSS_PCT = float(os.getenv("BINANCE_STOP_LOSS_PCT", "3.0"))
IBKR_TAKE_PROFIT_PCT = float(os.getenv("IBKR_TAKE_PROFIT_PCT", "6.0"))
IBKR_STOP_LOSS_PCT = float(os.getenv("IBKR_STOP_LOSS_PCT", "4.0"))

# Varlik bazli pozisyon boyutlandirma: her BUY/SELL sinyalinde sabit miktar yerine,
# bosta bekleyen (available) Binance futures USDT bakiyesinin belirli bir yuzdesi
# kadar pozisyon acilir. BTC icin %25, ETH icin %20, diger tum varliklar icin %10
# (hepsi Railway degiskeni ile ayarlanabilir).
AUTO_TRADER_SIZE_PCT_BTC = float(os.getenv("AUTO_TRADER_SIZE_PCT_BTC", "25.0")) / 100.0
AUTO_TRADER_SIZE_PCT_ETH = float(os.getenv("AUTO_TRADER_SIZE_PCT_ETH", "20.0")) / 100.0
AUTO_TRADER_SIZE_PCT_DEFAULT = float(os.getenv("AUTO_TRADER_SIZE_PCT_DEFAULT", "10.0")) / 100.0

# Sinyal gucune (confidence) gore kaldirac: kaldirac artik sabit varlik bazli
# degil, her islemin AI/sinyal guveninе gore kademeli belirlenir. Max kaldirac
# 3x ile sinirlandirilmistir (ayarlanabilir); cogu islem "orta-guclu" bandina
# (>= AUTO_TRADER_LEVERAGE_TIER_CONF) dustugu icin pratikte agirlikli olarak
# 3x kullanilir, zayif sinyallerde 2x'e duser.
AUTO_TRADER_LEVERAGE_MAX = max(1, int(os.getenv("AUTO_TRADER_LEVERAGE_MAX", "3")))
AUTO_TRADER_LEVERAGE_MIN = max(1, int(os.getenv("AUTO_TRADER_LEVERAGE_MIN", "2")))
AUTO_TRADER_LEVERAGE_TIER_CONF = float(os.getenv("AUTO_TRADER_LEVERAGE_TIER_CONF", "75"))


def asset_size_pct(symbol: str) -> float:
    """Sembolun baz varligina gore (BTC/ETH/diger) kullanilacak bakiye yuzdesini dondurur."""
    sym = str(symbol or "").upper()
    if sym.startswith("BTC"):
        return AUTO_TRADER_SIZE_PCT_BTC
    if sym.startswith("ETH"):
        return AUTO_TRADER_SIZE_PCT_ETH
    return AUTO_TRADER_SIZE_PCT_DEFAULT


def signal_leverage(confidence: float) -> int:
    """Sinyal guvenine (confidence, 0-100) gore kullanilacak kaldiraci dondurur.
    confidence >= AUTO_TRADER_LEVERAGE_TIER_CONF (varsayilan 75) ise max kaldirac (3x),
    aksi halde min kaldirac (2x) uygulanir. Max kaldirac AUTO_TRADER_LEVERAGE_MAX ile
    siniirlidir, hicbir zaman asilmaz."""
    if confidence >= AUTO_TRADER_LEVERAGE_TIER_CONF:
        return AUTO_TRADER_LEVERAGE_MAX
    return min(AUTO_TRADER_LEVERAGE_MIN, AUTO_TRADER_LEVERAGE_MAX)



def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def init_runtime_db() -> None:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_journal (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    status TEXT NOT NULL,
                    simulated INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    error_text TEXT NOT NULL,
                    request_id TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_trade_journal_request_id
                ON trade_journal(request_id)
                WHERE request_id IS NOT NULL
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auto_history (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    price REAL NOT NULL,
                    reason TEXT NOT NULL,
                    execution_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spot_positions (
                    symbol TEXT PRIMARY KEY,
                    quantity REAL NOT NULL,
                    avg_cost REAL NOT NULL,
                    opened_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS balance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    total_try REAL NOT NULL,
                    binance_try REAL NOT NULL,
                    ibkr_try REAL NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_balance_snapshots_ts ON balance_snapshots(ts)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS position_closures (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    realized_pnl_pct REAL NOT NULL,
                    close_reason TEXT NOT NULL,
                    detail TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()


def db_insert_trade_journal(
    broker: str,
    channel: str,
    symbol: str,
    side: str,
    quantity: float,
    status: str,
    simulated: bool,
    payload: Dict[str, Any],
    error_text: str = "",
    request_id: Optional[str] = None,
) -> str:
    row_id = str(uuid.uuid4())
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute(
                """
                INSERT INTO trade_journal(
                    id, created_at, broker, channel, symbol, side, quantity, status, simulated, payload_json, error_text, request_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row_id,
                    now_text(),
                    broker,
                    channel,
                    symbol,
                    side,
                    quantity,
                    status,
                    1 if simulated else 0,
                    json.dumps(payload, ensure_ascii=False),
                    error_text,
                    request_id,
                ),
            )
            conn.commit()
            return row_id
        finally:
            conn.close()


def db_recent_trade_journal(limit: int = 150) -> List[Dict[str, Any]]:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT id, created_at, broker, channel, symbol, side, quantity, status, simulated, payload_json, error_text, request_id
                FROM trade_journal
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        finally:
            conn.close()
    out: List[Dict[str, Any]] = []
    for r in rows:
        payload_json = r["payload_json"] or "{}"
        try:
            payload = json.loads(payload_json)
        except Exception:
            payload = {"raw": payload_json}
        out.append(
            {
                "id": r["id"],
                "created_at": r["created_at"],
                "broker": r["broker"],
                "channel": r["channel"],
                "symbol": r["symbol"],
                "side": r["side"],
                "quantity": safe_float(r["quantity"]),
                "status": r["status"],
                "simulated": bool(r["simulated"]),
                "payload": payload,
                "error": r["error_text"],
                "request_id": r["request_id"] or "",
            }
        )
    return out


def db_insert_auto_history(
    broker: str,
    symbol: str,
    action: str,
    confidence: int,
    price: float,
    reason: str,
    execution: Dict[str, Any],
) -> None:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute(
                """
                INSERT INTO auto_history(id, created_at, broker, symbol, action, confidence, price, reason, execution_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    now_text(),
                    str(broker),
                    str(symbol),
                    str(action),
                    int(confidence),
                    safe_float(price, 0),
                    str(reason),
                    json.dumps(execution, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()


def db_get_spot_position(symbol: str) -> Optional[Dict[str, Any]]:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT symbol, quantity, avg_cost, opened_at, updated_at FROM spot_positions WHERE symbol = ?",
                (symbol,),
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    return dict(row)


def db_upsert_spot_position(symbol: str, quantity: float, avg_cost: float, opened_at: Optional[str] = None) -> None:
    now = now_text()
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute(
                """
                INSERT INTO spot_positions(symbol, quantity, avg_cost, opened_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET quantity=excluded.quantity, avg_cost=excluded.avg_cost, updated_at=excluded.updated_at
                """,
                (symbol, quantity, avg_cost, opened_at or now, now),
            )
            conn.commit()
        finally:
            conn.close()


def db_delete_spot_position(symbol: str) -> None:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute("DELETE FROM spot_positions WHERE symbol = ?", (symbol,))
            conn.commit()
        finally:
            conn.close()


def db_list_spot_positions() -> List[Dict[str, Any]]:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT symbol, quantity, avg_cost, opened_at, updated_at FROM spot_positions").fetchall()
        finally:
            conn.close()
    return [dict(r) for r in rows]


_LAST_BALANCE_SNAPSHOT_TS = 0.0
_BALANCE_SNAPSHOT_MIN_INTERVAL_SEC = 600  # en fazla 10 dakikada bir yaz (DB'yi şişirmemek için)


def db_record_balance_snapshot(total_try: float, binance_try: float, ibkr_try: float) -> None:
    """Kişisel hesabın (Binance + IBKR toplamı) TRY cinsinden değerini periyodik
    olarak kaydeder. Bu geçmiş, 'Net Para Akışı' hesaplamasının piyasa geneli
    değil GERÇEKTEN kullanıcının kendi hesabındaki net değişimi göstermesini
    sağlar (bugün/bu hafta hesabım ne kadar arttı/azaldı)."""
    global _LAST_BALANCE_SNAPSHOT_TS
    now_epoch = time.time()
    if now_epoch - _LAST_BALANCE_SNAPSHOT_TS < _BALANCE_SNAPSHOT_MIN_INTERVAL_SEC:
        return
    if total_try <= 0:
        return
    _LAST_BALANCE_SNAPSHOT_TS = now_epoch
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            conn.execute(
                "INSERT INTO balance_snapshots (ts, created_at, total_try, binance_try, ibkr_try) VALUES (?, ?, ?, ?, ?)",
                (now_epoch, now_text(), total_try, binance_try, ibkr_try),
            )
            # 90 günden eski kayıtları temizle (DB büyümesin).
            conn.execute("DELETE FROM balance_snapshots WHERE ts < ?", (now_epoch - 90 * 86400,))
            conn.commit()
        finally:
            conn.close()


def db_closest_balance_snapshot(hours_ago: float) -> Optional[Dict[str, Any]]:
    """Belirtilen saat kadar once alinmis en yakin bakiye anlik goruntusunu
    dondurur (tam o zamanda kayit olmayabilecegi icin en yakinini bulur)."""
    target_ts = time.time() - hours_ago * 3600
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                SELECT ts, created_at, total_try, binance_try, ibkr_try
                FROM balance_snapshots
                ORDER BY ABS(ts - ?) ASC
                LIMIT 1
                """,
                (target_ts,),
            ).fetchone()
        finally:
            conn.close()
    return dict(row) if row else None


CLOSE_REASON_LABELS_TR = {
    "TAKE_PROFIT": "Kâr Al",
    "STOP_LOSS": "Zarar Kes",
    "MANUAL": "Manuel Kapatma",
    "AI_KARARI": "AI Kararı",
}

NOTIFY_EMAIL_ENABLED = os.environ.get("NOTIFY_EMAIL_ENABLED", "true").lower() not in ("false", "0", "")
NOTIFY_EMAIL_SENDER = os.environ.get("NOTIFY_EMAIL_SENDER", "")
NOTIFY_EMAIL_PASSWORD = os.environ.get("NOTIFY_EMAIL_PASSWORD", "")
NOTIFY_EMAIL_RECIPIENT = os.environ.get("NOTIFY_EMAIL_RECIPIENT", "")


def send_position_closure_email(
    broker: str,
    symbol: str,
    side: str,
    qty: float,
    entry_price: float,
    exit_price: float,
    realized_pnl: float,
    realized_pnl_pct: float,
    close_reason: str,
    detail: str,
) -> None:
    """Bir pozisyon kapandiginda kullaniciya mail atar; boylece son 100 kayitla
    sinirli AI gunlugunu takip etmek zorunda kalmadan (kacirma riski olmadan)
    kapanisi (kar mi zarar mi, neden) aninda gorur. Ayarlar eksikse veya SMTP
    basarisiz olursa sessizce gecilir - trading akisini asla bloklamaz/bozmaz."""
    if not NOTIFY_EMAIL_ENABLED:
        return
    if not (NOTIFY_EMAIL_SENDER and NOTIFY_EMAIL_PASSWORD and NOTIFY_EMAIL_RECIPIENT):
        return

    def _send():
        try:
            reason_label = CLOSE_REASON_LABELS_TR.get(str(close_reason).upper(), str(close_reason))
            is_profit = realized_pnl >= 0
            subject = (
                f"[DFinans] {symbol} pozisyonu kapandı - "
                f"{'KÂR' if is_profit else 'ZARAR'} ({reason_label})"
            )
            body = (
                f"Pozisyon kapandı.\n\n"
                f"Sembol: {symbol}\n"
                f"Borsa: {broker}\n"
                f"Yön: {side}\n"
                f"Miktar: {qty}\n"
                f"Giriş Fiyatı: {entry_price}\n"
                f"Çıkış Fiyatı: {exit_price}\n"
                f"Kapanma Nedeni: {reason_label}\n"
                f"Gerçekleşen K/Z: {'+' if is_profit else ''}{realized_pnl:.2f} "
                f"(%{realized_pnl_pct:.2f})\n"
                f"Detay: {detail}\n\n"
                f"Zaman: {now_text()}\n"
            )
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = NOTIFY_EMAIL_SENDER
            msg["To"] = NOTIFY_EMAIL_RECIPIENT

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.starttls()
                server.login(NOTIFY_EMAIL_SENDER, NOTIFY_EMAIL_PASSWORD)
                server.sendmail(NOTIFY_EMAIL_SENDER, [NOTIFY_EMAIL_RECIPIENT], msg.as_string())
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()


def db_record_position_closure(
    broker: str,
    symbol: str,
    side: str,
    qty: float,
    entry_price: float,
    exit_price: float,
    realized_pnl: float,
    realized_pnl_pct: float,
    close_reason: str,
    detail: str = "",
) -> None:
    """Bir pozisyon (kismen degil, kapanis emriyle) kapandiginda neden kapandigini
    (KAR_AL / ZARAR_KES / MANUEL / AI_KARARI) ve gerceklesen kar/zarari kalici olarak
    kaydeder. Kullanici 'IBKR'de AMD pozisyonu neden kapandi, kar mi zarar mi
    bilmiyorum' dedigi icin eklendi - onceden bu bilgi sadece auto_history'nin
    serbest metin 'reason' alaninda gomulu ve kolayca bulunamayan sekildeydi."""
    try:
        with DB_LOCK:
            conn = sqlite3.connect(RUNTIME_DB_PATH)
            try:
                conn.execute(
                    """
                    INSERT INTO position_closures
                        (id, created_at, broker, symbol, side, qty, entry_price, exit_price,
                         realized_pnl, realized_pnl_pct, close_reason, detail)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        now_text(),
                        str(broker).upper(),
                        str(symbol).upper(),
                        str(side).upper(),
                        float(qty),
                        float(entry_price),
                        float(exit_price),
                        float(realized_pnl),
                        float(realized_pnl_pct),
                        str(close_reason).upper(),
                        str(detail),
                    ),
                )
                conn.commit()
            finally:
                conn.close()
    except Exception:
        pass

    send_position_closure_email(
        broker=broker,
        symbol=symbol,
        side=side,
        qty=qty,
        entry_price=entry_price,
        exit_price=exit_price,
        realized_pnl=realized_pnl,
        realized_pnl_pct=realized_pnl_pct,
        close_reason=close_reason,
        detail=detail,
    )


def db_recent_position_closures(limit: int = 50) -> List[Dict[str, Any]]:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT created_at, broker, symbol, side, qty, entry_price, exit_price,
                       realized_pnl, realized_pnl_pct, close_reason, detail
                FROM position_closures
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 200)),),
            ).fetchall()
        finally:
            conn.close()
    return [dict(r) for r in rows]


def db_recent_auto_history(limit: int = 120) -> List[Dict[str, Any]]:
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT id, created_at, broker, symbol, action, confidence, price, reason, execution_json
                FROM auto_history
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 500)),),
            ).fetchall()
        finally:
            conn.close()
    out: List[Dict[str, Any]] = []
    for r in rows:
        exec_json = r["execution_json"] or "{}"
        try:
            execution = json.loads(exec_json)
        except Exception:
            execution = {"raw": exec_json}
        out.append(
            {
                "id": r["id"],
                "time": r["created_at"],
                "broker": r["broker"],
                "symbol": r["symbol"],
                "action": r["action"],
                "confidence": int(safe_float(r["confidence"], 0)),
                "price": safe_float(r["price"], 0),
                "reason": r["reason"],
                "execution": execution,
            }
        )
    return out


def _text_time_to_epoch(text: str) -> int:
    try:
        return int(datetime.strptime(text, "%Y-%m-%d %H:%M:%S").timestamp())
    except Exception:
        return int(time.time())


def build_ai_log_entries(limit: int = 100) -> List[Dict[str, Any]]:
    """iOS AITradeLogView.swift'in bekledigi RemoteAILog semasina (symbol, side,
    status, confidence, reason, market, created_at:epoch, extra) uygun kayitlar
    uretir. Eskiden bu route sadece gercek emir calistirmalarini (TRADE_LOG) donduruyordu
    ve auto-trader hicbir gercek emir acmadigi surece (ornegin guven esigi asilmadiginda)
    sonsuza dek bos kaliyordu - oysa dd AI her dongude bir karar (WAIT dahil) uretiyor ve
    bunlar auto_history tablosuna zaten kaydediliyor. Ayrica onceki surumde yanitta zorunlu
    "ok" alani hic yoktu; iOS tarafi bu alan olmadan JSON decode'u tamamen basarisiz
    sayiyordu (RemoteAILogResponse.ok non-optional Bool) - gercek veri gelse bile ekran
    hep bos kaliyordu."""
    entries: List[Dict[str, Any]] = []

    try:
        history_rows = db_recent_auto_history(limit)
    except Exception:
        history_rows = AUTO_HISTORY[:limit]

    for row in history_rows:
        action = str(row.get("action", "WAIT")).upper()
        execution = row.get("execution") or {}
        simulated = bool(execution.get("simulated", True)) if isinstance(execution, dict) else True
        err = str(execution.get("error", "") or "") if isinstance(execution, dict) else ""
        pnl_amount = safe_float(execution.get("pnl")) if isinstance(execution, dict) else 0.0
        if err:
            status = "error"
        elif action in ["BUY", "SELL"] and not simulated:
            status = "opened"
        elif action in ["BUY", "SELL"] and simulated:
            status = "waitingConfirmation"
        elif action == "TAKE_PROFIT":
            status = "closedProfit"
        elif action == "STOP_LOSS":
            status = "closedLoss"
        else:
            status = "scan"
        reason = str(row.get("reason", ""))
        if action in ("TAKE_PROFIT", "STOP_LOSS") and pnl_amount != 0.0:
            reason = f"{reason} (Gerçekleşen K/Z: {'+' if pnl_amount >= 0 else ''}{pnl_amount:.2f})"
        if "açık" in reason.lower() and "pozisyon" in reason.lower() and action == "WAIT":
            status = "protectedPosition"
        entries.append({
            "symbol": row.get("symbol", "-"),
            "side": action if action in ["BUY", "SELL"] else ("SELL" if status == "closedProfit" or status == "closedLoss" else "-"),
            "status": status,
            "confidence": int(safe_float(row.get("confidence"), 0)),
            "reason": reason or "-",
            "market": str(row.get("broker", "-")),
            "created_at": _text_time_to_epoch(str(row.get("time", now_text()))),
            "extra": {},
        })

    for row in TRADE_LOG[:limit]:
        order = row.get("order") or {}
        symbol = str(order.get("symbol", row.get("symbol", "-"))) if isinstance(order, dict) else "-"
        side = str(order.get("side", "-")) if isinstance(order, dict) else "-"
        status = "error" if row.get("error") else "opened"
        entries.append({
            "symbol": symbol,
            "side": side,
            "status": status,
            "confidence": int(safe_float(row.get("confidence"), 80)),
            "reason": str(row.get("message", row.get("reason", "Manuel/otomatik emir çalıştırıldı."))),
            "market": str(row.get("market", "-")),
            "created_at": _text_time_to_epoch(str(row.get("time", now_text()))),
            "extra": {},
        })

    entries.sort(key=lambda e: e["created_at"], reverse=True)
    return entries[:limit]


def request_id_seen(request_id: str) -> bool:
    if not request_id:
        return False
    with DB_LOCK:
        conn = sqlite3.connect(RUNTIME_DB_PATH)
        try:
            row = conn.execute(
                "SELECT 1 FROM trade_journal WHERE request_id = ? LIMIT 1",
                (request_id,),
            ).fetchone()
            return bool(row)
        finally:
            conn.close()


def unique_bases(bases: List[str]) -> List[str]:
    seen = set()
    out = []
    for base in bases:
        if base and base not in seen:
            seen.add(base)
            out.append(base.rstrip("/"))
    return out


def base_candidates(base: str) -> List[str]:
    if "fapi" in base:
        return unique_bases(FUTURES_BASES)
    return unique_bases(SPOT_BASES)


def short_binance_error(text: str) -> str:
    # Binance 451 / restricted location hatasını kullanıcı ekranına teknik JSON olarak taşımamak için sadeleştirir.
    if "restricted location" in text.lower() or "eligibility" in text.lower() or "451" in text:
        return "Binance verisi bölgesel erişim nedeniyle alınamadı. Farklı endpoint/VPS bölgesi denenmeli."
    return text


def _binance_proxy_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if BINANCE_PROXY_TOKEN:
        headers["X-Binance-Proxy-Token"] = BINANCE_PROXY_TOKEN
    return headers


def _binance_proxy_request(method: str, path: str, params: Optional[Dict[str, Any]] = None, json_body: Optional[Dict[str, Any]] = None, base_url: Optional[str] = None) -> Any:
    target_base = (base_url or BINANCE_PROXY_BASE_URL).rstrip("/")
    if not target_base:
        raise RuntimeError("Binance proxy base URL ayarlı değil.")
    url = f"{target_base}{path}"
    headers = _binance_proxy_headers()
    try:
        if method.upper() == "GET":
            r = requests.get(url, params=params or {}, headers=headers, timeout=BINANCE_PROXY_TIMEOUT)
        elif method.upper() == "POST":
            r = requests.post(url, params=params or {}, json=json_body or {}, headers=headers, timeout=BINANCE_PROXY_TIMEOUT)
        else:
            raise ValueError("Desteklenmeyen HTTP metodu")
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} - {short_binance_error(r.text)}")
        return r.json()
    except Exception as e:
        raise RuntimeError(f"Binance proxy hatası: {e}") from e


def _binance_proxy_portfolio_payload() -> Dict[str, Any]:
    # VPS'teki gerçek TRY donusumu /account-summary route'unda yapiliyor;
    # /portfolio route'u VPS backend'inde mevcut degil (404).
    data = _binance_proxy_request("GET", "/account-summary")
    if not isinstance(data, dict):
        raise RuntimeError("Proxy /account-summary beklenen JSON objesini döndürmedi.")
    return data


def _proxy_extract_positions_from_portfolio(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = payload.get("futures_positions", [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)]


def _proxy_extract_balances_from_portfolio(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = payload.get("spot_balances", [])
    if not isinstance(rows, list):
        return []
    return [x for x in rows if isinstance(x, dict)]


def _proxy_extract_positions_from_legacy_positions(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = payload.get("positions", [])
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for p in rows:
        if not isinstance(p, dict):
            continue
        amount = abs(safe_float(p.get("amount")))
        side = str(p.get("side", "-")).upper()
        if side not in {"LONG", "SHORT"}:
            side = "LONG" if safe_float(p.get("amount")) >= 0 else "SHORT"
        out.append({
            "id": f"BINANCE-FUTURES-{str(p.get('symbol', 'UNK')).upper()}",
            "broker": "Binance",
            "market": "Futures",
            "symbol": str(p.get("symbol", "")).upper(),
            "side": side,
            "size": amount,
            "entry_price": safe_float(p.get("entry")),
            "mark_price": safe_float(p.get("markPrice")),
            "pnl": safe_float(p.get("pnl")),
            "leverage": str(p.get("leverage", "")),
        })
    return out


def _proxy_extract_balances_from_legacy_portfolio(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = payload.get("data", {})
    if not isinstance(data, dict):
        return []
    spot_try = safe_float(data.get("spotTry"))
    futures_try = safe_float(data.get("futuresTry"))
    total_try = safe_float(data.get("binanceTry") or data.get("totalTry"))
    rows: List[Dict[str, Any]] = []
    if total_try > 0:
        rows.append({"asset": "BINANCE_TRY_TOTAL", "free": total_try, "locked": 0.0, "total": total_try})
    if spot_try > 0:
        rows.append({"asset": "SPOT_TRY_EQUIV", "free": spot_try, "locked": 0.0, "total": spot_try})
    if futures_try > 0:
        rows.append({"asset": "FUTURES_TRY_EQUIV", "free": futures_try, "locked": 0.0, "total": futures_try})
    return rows


def signed_request(method: str, base: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        raise RuntimeError("Binance API anahtarı eksik. Railway Variables içinde BINANCE_LIVE_API_KEY ve BINANCE_LIVE_SECRET_KEY girilmeli.")

    last_error = ""
    for try_base in base_candidates(base):
        params2 = dict(params or {})
        params2["timestamp"] = int(time.time() * 1000)
        query = urlencode(params2, doseq=True)
        signature = hmac.new(BINANCE_SECRET_KEY.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
        url = f"{try_base}{path}?{query}&signature={signature}"
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}

        try:
            if method.upper() == "GET":
                r = requests.get(url, headers=headers, timeout=SIGNED_HTTP_TIMEOUT, allow_redirects=False)
            elif method.upper() == "POST":
                r = requests.post(url, headers=headers, timeout=SIGNED_HTTP_TIMEOUT, allow_redirects=False)
            elif method.upper() == "DELETE":
                r = requests.delete(url, headers=headers, timeout=SIGNED_HTTP_TIMEOUT, allow_redirects=False)
            else:
                raise ValueError("Desteklenmeyen HTTP metodu")

            # Bazı numaralı mirror'lar (fapi1/fapi2/fapi3/api1/api2/api3) bu VPS IP'sinden
            # gelen POST/emir isteklerini 3xx ile www.binance.com'a yönlendirebiliyor.
            # allow_redirects=False ile bunu redirect olarak yakalayıp bozuk mirror
            # sayıp bir sonraki adaya geçiyoruz (aksi halde requests redirect'i otomatik
            # takip edip boş/HTML gövdeli bir 2xx üretiyor ve bu JSON parse hatasına yol açıyordu).
            if r.is_redirect or r.is_permanent_redirect or 300 <= r.status_code < 400:
                last_error = f"{r.status_code} - mirror redirect ({try_base})"
                continue

            if r.status_code < 400:
                return r.json()

            if r.status_code < 500:
                # Binance'tan gelen gerçek (4xx) JSON hata yanıtı otoritatif kabul edilir
                # (örn. yanlış miktar, yetersiz bakiye, imza hatası); bir sonraki mirror'un
                # daha az bilgilendirici bir hatasıyla ezilmemesi için hemen fırlatılır.
                raise RuntimeError(f"{r.status_code} - {short_binance_error(r.text)}")

            # 5xx sunucu hatası: geçici olabilir, bir sonraki mirror'u dene.
            last_error = f"{r.status_code} - {short_binance_error(r.text)}"
        except RuntimeError:
            raise
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"Binance hata: {last_error}")

def public_get(base: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    last_error = ""
    for try_base in base_candidates(base):
        try:
            r = requests.get(f"{try_base}{path}", params=params or {}, timeout=PUBLIC_HTTP_TIMEOUT)
            if r.status_code < 400:
                return r.json()
            last_error = f"{r.status_code} - {short_binance_error(r.text)}"
        except Exception as e:
            last_error = str(e)
    raise RuntimeError(f"Public veri hatası: {last_error}")

def get_price(symbol: str, market: str) -> float:
    base = FUTURES_BASE if market.upper() == "FUTURES" else SPOT_BASE
    data = public_get(base, "/fapi/v1/ticker/price" if market.upper() == "FUTURES" else "/api/v3/ticker/price", {"symbol": symbol})
    return safe_float(data.get("price"))


def get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = PUBLIC_HTTP_TIMEOUT) -> Dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 D-finans/1.0", "Accept": "application/json"}
    r = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def ensure_thread_event_loop() -> None:
    """
    Python 3.14 no longer auto-creates event loops in non-main threads.
    ib_insync expects an event loop in the current thread.
    """
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


def load_ib_insync():
    try:
        import ib_insync
    except ImportError as e:
        raise RuntimeError("IBKR entegrasyonu için ib-insync kurulmalı.") from e
    return ib_insync


def require_ibkr_enabled():
    if not IBKR_ENABLED:
        raise RuntimeError("IBKR devre dışı. Railway Variables içine IBKR_ENABLED=true eklenmeli.")


def _ibkr_disconnect_locked() -> None:
    ib = IBKR_RUNTIME.get("ib")
    if ib:
        try:
            ib.disconnect()
        except Exception:
            pass
    IBKR_RUNTIME["ib"] = None
    IBKR_RUNTIME["connected"] = False


def _ibkr_circuit_breaker_check() -> None:
    """Check if circuit breaker should be opened due to repeated failures."""
    failed = int(IBKR_RUNTIME.get("failed_attempts", 0))
    last_fail = float(IBKR_RUNTIME.get("last_fail_time", 0))
    now = time.time()
    
    # Circuit breaker: if >3 failures in last 60 seconds, open breaker for 30 seconds
    if failed >= 3 and (now - last_fail) < 60:
        IBKR_RUNTIME["circuit_breaker_open"] = True
        print(f"[IBKR] Circuit breaker OPEN after {failed} failures. Disabling orders for 30s.")
    elif (now - last_fail) > 90:
        # Reset after 90 seconds of no failures
        IBKR_RUNTIME["failed_attempts"] = 0
        IBKR_RUNTIME["circuit_breaker_open"] = False
        print("[IBKR] Circuit breaker reset.")


def ensure_ibkr_connection(force_reconnect: bool = False):
    ensure_thread_event_loop()
    require_ibkr_enabled()
    
    # Check circuit breaker
    _ibkr_circuit_breaker_check()
    if IBKR_RUNTIME.get("circuit_breaker_open"):
        raise RuntimeError("IBKR circuit breaker OPEN. Too many failures. Retry in 30 seconds.")
    
    with IBKR_LOCK:
        if force_reconnect:
            _ibkr_disconnect_locked()
        ib = IBKR_RUNTIME.get("ib")
        ibs = IBKR_RUNTIME.get("ibs")
        if ib and ib.isConnected() and not force_reconnect:
            return ib, ibs
        
        if not ibs:
            ibs = load_ib_insync()
            IBKR_RUNTIME["ibs"] = ibs
        
        # Exponential backoff: wait 0.5s, 1s, 2s, 4s, 8s based on reconnect count
        reconnect_count = int(IBKR_RUNTIME.get("reconnect_count", 0))
        backoff_sec = min(0.5 * (2 ** (reconnect_count % 5)), 10.0)
        if reconnect_count > 0:
            print(f"[IBKR] Reconnect attempt {reconnect_count+1}, backoff {backoff_sec:.1f}s")
            time.sleep(backoff_sec)
        
        try:
            ib = ibs.IB()
            ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=8)
            if not ib.isConnected():
                raise RuntimeError("IBKR bağlantısı kurulamadı.")
            
            IBKR_RUNTIME["ib"] = ib
            IBKR_RUNTIME["connected"] = True
            IBKR_RUNTIME["last_ok"] = now_text()
            IBKR_RUNTIME["last_error"] = ""
            IBKR_RUNTIME["reconnect_count"] = reconnect_count + 1
            IBKR_RUNTIME["failed_attempts"] = 0
            try:
                # Hesapta canli (real-time) piyasa verisi abonelugu yok
                # (Error 10089). Once canli veri deneyip, olmazsa gecikmeli
                # veriye (delayed, 15-20 dk gecikmeli) dusuyoruz. Bunu
                # default olarak 3 (delayed) ayarlamak, her sembolde canli
                # veri denemesinin bosuna 2.5sn beklemesini onler.
                ib.reqMarketDataType(3)
                print("[IBKR] Market data type set to DELAYED (3) - hesapta canli veri abonelugu yok.")
            except Exception as mdt_err:
                print(f"[IBKR] reqMarketDataType ayarlanamadi: {mdt_err}")
            print(f"[IBKR] Connected successfully at attempt {reconnect_count+1}")
            return ib, ibs
        except Exception as e:
            IBKR_RUNTIME["failed_attempts"] = int(IBKR_RUNTIME.get("failed_attempts", 0)) + 1
            IBKR_RUNTIME["last_fail_time"] = time.time()
            IBKR_RUNTIME["connected"] = False
            IBKR_RUNTIME["last_error"] = str(e)
            # circuit breaker acilinca bu gercek hata bir sonraki denemede
            # breaker mesaji tarafindan ezilebiliyor; asil nedeni ayri sakla.
            IBKR_RUNTIME["last_real_error"] = f"{type(e).__name__}: {e}"
            IBKR_RUNTIME["last_real_error_time"] = now_text()
            _ibkr_disconnect_locked()
            raise


def _ibkr_execute_in_worker_thread(action):
    """GERCEK IBKR (ib_insync) cagrisini yapar. SADECE tek adanmis IBKR worker
    thread'i icinden cagrilmalidir - baska hicbir yerden dogrudan cagirma."""
    ensure_thread_event_loop()
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            ib, ibs = ensure_ibkr_connection(force_reconnect=(attempt == 1))
            # ONEMLI: Gecersiz sembol / abonelik eksikligi gibi "is mantigi"
            # hatalari (contract dogrulanamadi, canli fiyat yok, vb.) BAGLANTI
            # hatasi degildir - bunlar icin tum IBKR oturumunu disconnect+
            # reconnect etmek (eskiden burada oluyordu) mobil uygulama onlarca
            # farkli/gecersiz sembol sorguladiginda saniyeler suren reconnect
            # firtinasina yol aciyordu. Sadece GERCEKTEN baglanti kopmussa
            # (ib.isConnected() False) yeniden baglaniyoruz; aksi halde hatayi
            # oldugu gibi yukari firlatip mevcut baglantiyi koruyoruz.
            try:
                result = action(ib, ibs)
                IBKR_RUNTIME["connected"] = bool(ib.isConnected())
                IBKR_RUNTIME["last_ok"] = now_text()
                IBKR_RUNTIME["last_error"] = ""
                return result
            except Exception as action_err:
                still_connected = False
                try:
                    still_connected = bool(ib.isConnected())
                except Exception:
                    still_connected = False
                IBKR_RUNTIME["connected"] = still_connected
                IBKR_RUNTIME["last_error"] = str(action_err)
                if still_connected:
                    # Baglanti saglam; bu sadece is mantigi hatasi (ör. sembol
                    # bulunamadi, veri aboneligi yok). Reconnect'e GEREK YOK.
                    raise RuntimeError(str(action_err)) from None
                # Baglanti gercekten kopmus - disconnect edip bir sonraki
                # denemede yeniden baglanmayi dene.
                raise
        except Exception as e:
            last_error = e
            still_connected = False
            ib_ref = IBKR_RUNTIME.get("ib")
            if ib_ref is not None:
                try:
                    still_connected = bool(ib_ref.isConnected())
                except Exception:
                    still_connected = False
            if not still_connected:
                IBKR_RUNTIME["connected"] = False
                IBKR_RUNTIME["last_error"] = str(e)
                _ibkr_disconnect_locked()
                time.sleep(0.7)
            else:
                # Baglanti hala ayakta ve hata sadece is mantigi hatasiysa,
                # gereksiz ikinci denemeyi (force_reconnect) atlayip direkt cik.
                raise RuntimeError(f"IBKR işlem hatası: {e}") from None
    raise RuntimeError(f"IBKR işlem hatası: {last_error}")


def _ibkr_worker_thread_main():
    """Tum ib_insync IBKR islemlerinin calistigi TEK adanmis thread. Boylece
    IB client'i her zaman AYNI thread'in AYNI asyncio event loop'una bagli
    kalir; kac tane gunicorn/Flask thread'i paralel istek yaparsa yapsin,
    hepsi bu kuyruk uzerinden sıraya girer ve hicbir zaman ib_insync
    nesnesine birden fazla thread'den dogrudan dokunulmaz. Bu, farkli
    thread'lerin IBKR baglantisina cakismasindan kaynaklanan
    'client id already in use' / tum servisin cokmesi gibi hatalari kokten
    onler."""
    ensure_thread_event_loop()
    while True:
        job = IBKR_TASK_QUEUE.get()
        if job is None:
            continue
        action, result_holder, done_event = job
        try:
            result_holder["result"] = _ibkr_execute_in_worker_thread(action)
        except Exception as e:
            result_holder["error"] = e
        finally:
            done_event.set()


def ibkr_execute(action, timeout: float = 25.0):
    """Herhangi bir thread'den cagrilabilir (Flask request thread'i, keepalive
    thread'i, auto-trader thread'i). Gercek islemi kuyruga koyup TEK IBKR
    worker thread'inin islemesini bekler; boylece cok sayida paralel istek
    gelse bile IB client'ina her zaman ayni thread'den erisilir."""
    done_event = threading.Event()
    result_holder: Dict[str, Any] = {}
    IBKR_TASK_QUEUE.put((action, result_holder, done_event))
    if not done_event.wait(timeout=timeout):
        raise RuntimeError("IBKR şu anda meşgul, lütfen birkaç saniye sonra tekrar deneyin.")
    if "error" in result_holder:
        raise result_holder["error"]
    return result_holder.get("result")


def normalize_symbol(symbol: str) -> str:
    return str(symbol).upper().replace("/", "").replace("-", "").strip()


def build_ibkr_contract(ibs, symbol: str, asset_type: str, exchange: str, currency: str):
    sym = normalize_symbol(symbol)
    kind = str(asset_type or "STK").upper()
    cur = str(currency or "USD").upper()
    ex = str(exchange or "SMART").upper()

    if kind == "STK":
        return ibs.Stock(sym, ex, cur)
    if kind == "CRYPTO":
        if len(sym) < 6:
            raise RuntimeError("CRYPTO sembolü BTCUSD formatında olmalı.")
        base = sym[:-3]
        quote = sym[-3:]
        return ibs.Contract(secType="CRYPTO", symbol=base, exchange=ex or "PAXOS", currency=quote)
    if kind in ["FOREX", "FX", "CASH"]:
        if len(sym) != 6:
            raise RuntimeError("FOREX sembolü EURUSD formatında olmalı.")
        base = sym[:3]
        quote = sym[3:]
        return ibs.Forex(f"{base}{quote}", exchange=ex or "IDEALPRO")
    raise RuntimeError("asset_type desteklenmiyor. STK, CRYPTO veya FOREX kullanılmalı.")


_IBKR_SNAPSHOT_CACHE: Dict[str, Any] = {}
_IBKR_SNAPSHOT_CACHE_TTL_SEC = 2.0

# --- Toplu (batched) fiyat sorgulama ---
# Mobil uygulama ayni anda (Piyasalar ekrani, Islem merkezi, Ekonomi Radari vb.)
# 5-10 farkli sembol icin fiyat istiyor. IBKR erisimi tek adanmis worker thread
# uzerinden serilestirildigi icin (bkz. ibkr_execute), her sembolu ayri ayri
# istemek N sembol x 2.5sn = cok yavas bir toplam sure demek ve istemci
# tarafinda zaman asimina (timeout) yol aciyordu. Bunun yerine kisa bir
# "toplama penceresi" (150ms) icinde gelen tum istekler tek bir IBKR
# round-trip'inde (tek reqMktData turu + tek sleep) toplanip cevaplanir.
_IBKR_BATCH_LOCK = threading.Lock()
_IBKR_PENDING_BATCH: List[Dict[str, Any]] = []
_IBKR_BATCH_OWNER_ACTIVE = False
_IBKR_BATCH_DEBOUNCE_SEC = 0.15
_IBKR_BATCH_MAX_WAIT_SEC = 20.0


def _clean_float(v: Any) -> float:
    f = safe_float(v)
    return f if f == f and f not in (float("inf"), float("-inf")) else 0.0


def _build_snapshot_from_ticker(ticker, symbol: str, asset_type: str, exchange: str, currency: str) -> Dict[str, Any]:
    price = _clean_float(ticker.marketPrice())
    last_price = _clean_float(getattr(ticker, "last", 0))
    close_price = _clean_float(getattr(ticker, "close", 0))
    if price <= 0:
        price = last_price if last_price > 0 else close_price
    if price <= 0:
        raise RuntimeError("IBKR canlı fiyat alınamadı.")
    prev = close_price if close_price > 0 else price
    change_24h = ((price - prev) / prev) * 100.0 if prev > 0 else 0.0
    # Ikinci, bagimsiz sinyal: emir defteri (bid/ask) buyuklugu dengesizligi.
    bid_size = safe_float(getattr(ticker, "bidSize", 0))
    ask_size = safe_float(getattr(ticker, "askSize", 0))
    order_flow_signal = "NEUTRAL"
    if bid_size > 0 or ask_size > 0:
        total_size = bid_size + ask_size
        if total_size > 0:
            bid_ratio = bid_size / total_size
            if bid_ratio > 0.58:
                order_flow_signal = "BUY"
            elif bid_ratio < 0.42:
                order_flow_signal = "SELL"
    return {
        "symbol": normalize_symbol(symbol),
        "asset_type": str(asset_type or "STK").upper(),
        "exchange": exchange,
        "currency": currency,
        "data_source": "ibkr",
        "price": round(price, 6),
        "change_24h": round(change_24h, 4),
        "prev_close": round(prev, 6),
        "bid_size": bid_size,
        "ask_size": ask_size,
        "order_flow_signal": order_flow_signal,
        "last_update": now_text(),
    }


def _process_ibkr_price_batch(batch_items: List[Dict[str, Any]]) -> None:
    """Tek bir IBKR round-trip'inde birden fazla sembolu birlikte sorgular ve
    sonuclari her istemcinin kendi threading.Event'ine dagitir."""
    def _run(ib, ibs):
        try:
            ib.reqMarketDataType(3)
        except Exception:
            pass
        # Ayni contract'i (symbol/asset_type/exchange/currency) birden fazla
        # istemci istemis olabilir - IBKR'a sadece bir kez sormak yeterli.
        unique_contracts: Dict[str, Any] = {}
        tickers: Dict[str, Any] = {}
        for item in batch_items:
            key = item["cache_key"]
            if key in unique_contracts:
                continue
            try:
                contract = build_ibkr_contract(ibs, item["symbol"], item["asset_type"], item["exchange"], item["currency"])
                qualified = ib.qualifyContracts(contract)
                if not qualified:
                    raise RuntimeError("IBKR contract doğrulanamadı.")
                unique_contracts[key] = qualified[0]
                tickers[key] = ib.reqMktData(qualified[0], "", True, False)
            except Exception as e:
                item["error"] = str(e)
        if tickers:
            # Onceden 2.5sn bekleniyordu; delayed (type 3) veri genelde 1-1.2sn
            # icinde populate oluyor, gereksiz beklemeyi kisaltmak toplam
            # gecikmeyi (cache TTL + bu bekleme) azaltir.
            ib.sleep(1.2)
        for item in batch_items:
            key = item["cache_key"]
            if item.get("error"):
                continue
            ticker = tickers.get(key)
            if ticker is None:
                item["error"] = "IBKR contract doğrulanamadı."
                continue
            try:
                item["result"] = _build_snapshot_from_ticker(
                    ticker, item["symbol"], item["asset_type"], item["exchange"], item["currency"]
                )
            except Exception as e:
                item["error"] = str(e)
        return None

    try:
        ibkr_execute(_run, timeout=30.0)
    except Exception as e:
        # ibkr_execute'un kendisi (kuyruk/baglanti) patlarsa, hicbir item'in
        # sonucu/hatasi set edilmemis olabilir - hepsine bu hatayi yaz.
        for item in batch_items:
            if not item.get("error") and item.get("result") is None:
                item["error"] = str(e)
    finally:
        now = time.time()
        for item in batch_items:
            if item.get("result") is not None:
                _IBKR_SNAPSHOT_CACHE[item["cache_key"]] = (now, item["result"])
            item["event"].set()


def ibkr_market_snapshot(symbol: str, asset_type: str, exchange: str, currency: str) -> Dict[str, Any]:
    # Mobil uygulama ayni sembolu birden fazla ekrandan (Piyasalar, Islem, Ekonomi
    # Radari vb.) kisa arayla tekrar tekrar sorguluyor. Her istek ~2.5sn IBKR
    # bekleme + paylasilan IBKR_LOCK gerektirdigi icin, kisa bir TTL cache
    # gereksiz tekrar sorgulari (ve IBKR uzerindeki yuku) buyuk olcude azaltir.
    cache_key = f"{normalize_symbol(symbol)}|{asset_type}|{exchange}|{currency}"
    cached = _IBKR_SNAPSHOT_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _IBKR_SNAPSHOT_CACHE_TTL_SEC:
        return cached[1]

    item = {
        "cache_key": cache_key,
        "symbol": symbol,
        "asset_type": asset_type,
        "exchange": exchange,
        "currency": currency,
        "event": threading.Event(),
        "result": None,
        "error": None,
    }

    global _IBKR_BATCH_OWNER_ACTIVE
    is_owner = False
    with _IBKR_BATCH_LOCK:
        _IBKR_PENDING_BATCH.append(item)
        if not _IBKR_BATCH_OWNER_ACTIVE:
            _IBKR_BATCH_OWNER_ACTIVE = True
            is_owner = True

    if is_owner:
        # Kisa bir sure bekleyerek ayni anda gelen diger istekleri de bu
        # tura dahil et (debounce). Bu sirada baska thread'ler kendi
        # item'larini _IBKR_PENDING_BATCH'e ekleyebilir.
        time.sleep(_IBKR_BATCH_DEBOUNCE_SEC)
        with _IBKR_BATCH_LOCK:
            batch_items = _IBKR_PENDING_BATCH.copy()
            _IBKR_PENDING_BATCH.clear()
            _IBKR_BATCH_OWNER_ACTIVE = False
        _process_ibkr_price_batch(batch_items)
    else:
        if not item["event"].wait(timeout=_IBKR_BATCH_MAX_WAIT_SEC):
            raise RuntimeError("IBKR fiyat isteği zaman aşımına uğradı.")

    if item.get("error"):
        raise RuntimeError(f"IBKR işlem hatası: {item['error']}")
    return item["result"]


def ibkr_positions_snapshot() -> List[Dict[str, Any]]:
    def _run(ib, _):
        rows = []
        # ib.positions() sadece pozisyon miktari/maliyetini dondurur; mark_price
        # ve pnl hep 0 kaliyordu. ib.portfolio() IBKR'in kendi hesapladigi
        # marketPrice/marketValue/unrealizedPNL degerlerini de icerir - ekstra
        # reqMktData cagrisi gerektirmeden dogru fiyat ve PnL saglar.
        portfolio_items = ib.portfolio()
        portfolio_by_key = {
            (item.contract.secType, item.contract.symbol, item.account): item
            for item in portfolio_items
        }
        for pos in ib.positions():
            if IBKR_ACCOUNT and pos.account != IBKR_ACCOUNT:
                continue
            qty = safe_float(pos.position)
            if qty == 0:
                continue
            avg_cost = safe_float(pos.avgCost)
            item = portfolio_by_key.get((pos.contract.secType, pos.contract.symbol, pos.account))
            mark_price = safe_float(getattr(item, "marketPrice", 0.0)) if item else 0.0
            pnl = safe_float(getattr(item, "unrealizedPNL", 0.0)) if item else 0.0
            if mark_price <= 0 and item is None:
                # portfolio() bu pozisyonu icermiyorsa (nadir) canli fiyati
                # dogrudan reqMktData ile cekmeyi dene.
                try:
                    contract = pos.contract
                    ib.qualifyContracts(contract)
                    ticker = ib.reqMktData(contract, "", True, False)
                    ib.sleep(1.5)
                    mp = safe_float(ticker.marketPrice())
                    if mp == mp and mp > 0:
                        mark_price = mp
                        pnl = (mark_price - avg_cost) * qty
                except Exception:
                    pass
            rows.append({
                "id": f"IBKR-{pos.contract.secType}-{pos.contract.symbol}",
                "broker": "IBKR",
                "market": "IBKR",
                "account": pos.account,
                "asset_type": pos.contract.secType,
                "symbol": pos.contract.symbol,
                "exchange": pos.contract.exchange,
                "currency": pos.contract.currency,
                "side": "LONG" if qty > 0 else "SHORT",
                "size": abs(qty),
                "entry_price": avg_cost,
                "mark_price": round(mark_price, 6),
                "pnl": round(pnl, 4),
                "leverage": "",
                # iOS uygulamasi (IBKRService.swift) bu alan adlarini bekliyor:
                "position": qty,
                "avgCost": avg_cost,
                "secType": pos.contract.secType,
                "name": pos.contract.symbol,
            })
        return rows
    return ibkr_execute(_run)


def ibkr_account_summary_snapshot() -> List[Dict[str, Any]]:
    """IBKR hesap ozet degerlerini (NetLiquidation, CashBalance, ExchangeRate vb.)
    tag/currency/value satirlari olarak dondurur. Mobil uygulama /account-summary
    endpoint'inden bu formati (data: [{tag, currency, value, account}]) bekliyor."""
    def _run(ib, _):
        rows = []
        # accountValues() sadece reqAccountUpdates ile abone olunan TEK (birincil)
        # hesabi dondurur; birden fazla IBKR hesabi (ör. canli + demo) varsa
        # accountSummary(group='All') hepsini kapsar - bu yuzden o kullaniliyor.
        values = ib.accountSummary(IBKR_ACCOUNT or "")
        if not values:
            values = ib.accountValues(IBKR_ACCOUNT or "")
        for v in values:
            if IBKR_ACCOUNT and v.account != IBKR_ACCOUNT:
                continue
            rows.append({
                "tag": v.tag,
                "currency": v.currency,
                "value": v.value,
                "account": v.account,
            })
        return rows
    return ibkr_execute(_run)


def get_ibkr_available_funds() -> float:
    """IBKR hesabindaki kullanilabilir alim gucunu (AvailableFunds) USD olarak dondurur.
    Auto-trader IBKR icin sabit miktarli (ör. 1 hisse) emir gonderdiginde, hesaptaki
    diger pozisyonlarin (NVDA/AMD/IBKR) marjini yuzunden 'Available Funds insufficient
    to cover margin requirement' hatasiyla emir iptal ediliyordu - emir hic tutmuyordu.
    Bu fonksiyon otomatik pozisyon boyutlandirmasinda kullanilir."""
    def _fetch():
        try:
            rows = ibkr_account_summary_snapshot()
        except Exception:
            return 0.0
        for r in rows:
            if str(r.get("tag", "")) == "AvailableFunds":
                return safe_float(r.get("value"))
        return 0.0
    return _cache_get_or_fetch("ibkr_available_funds", 20, _fetch)


def ibkr_place_market_order(
    symbol: str,
    side: str,
    quantity: float,
    asset_type: str,
    exchange: str,
    currency: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    def _run(ib, ibs):
        if quantity <= 0:
            raise RuntimeError("Miktar 0'dan büyük olmalı.")
        order_side = str(side or "").upper()
        if order_side not in ["BUY", "SELL"]:
            raise RuntimeError("side BUY veya SELL olmalı.")

        contract = build_ibkr_contract(ibs, symbol, asset_type, exchange, currency)
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError("IBKR contract doğrulanamadı.")
        order = ibs.MarketOrder(order_side, quantity)
        order.tif = "DAY"
        order.outsideRth = True
        if IBKR_ACCOUNT:
            order.account = IBKR_ACCOUNT
        trade = ib.placeOrder(qualified[0], order)
        for _ in range(40):
            status = str(getattr(trade.orderStatus, "status", ""))
            if status in ibs.OrderStatus.DoneStates:
                break
            ib.sleep(0.25)

        log_messages = []
        try:
            for entry in (trade.log or []):
                msg = str(getattr(entry, "message", "") or "")
                if msg:
                    log_messages.append(msg)
        except Exception:
            pass

        result = {
            "broker": "IBKR",
            "simulated": False,
            "symbol": normalize_symbol(symbol),
            "asset_type": str(asset_type or "STK").upper(),
            "side": order_side,
            "quantity": quantity,
            "order_id": getattr(trade.order, "orderId", 0),
            "status": getattr(trade.orderStatus, "status", ""),
            "filled": safe_float(getattr(trade.orderStatus, "filled", 0)),
            "remaining": safe_float(getattr(trade.orderStatus, "remaining", 0)),
            "avg_fill_price": safe_float(getattr(trade.orderStatus, "avgFillPrice", 0)),
            "why_held": str(getattr(trade.orderStatus, "whyHeld", "") or ""),
            "log": log_messages[-5:],
            "last_update": now_text(),
        }
        db_insert_trade_journal(
            broker="IBKR",
            channel="manual",
            symbol=normalize_symbol(symbol),
            side=order_side,
            quantity=quantity,
            status=str(result.get("status") or "SENT"),
            simulated=False,
            payload=result,
            request_id=request_id,
        )
        return result
    return ibkr_execute(_run)


def ibkr_ping() -> bool:
    def _run(ib, _):
        ib.reqCurrentTime()
        return True
    return bool(ibkr_execute(_run))


# ============================================================
# HARICI PIYASA SINYALLERI (Funding Rate + Fear & Greed Index)
# Auto-trader confidence hesaplamasina ek "makro/duygu" filtresi
# olarak katkida bulunur. Herhangi bir kaynak basarisiz olursa
# sessizce norotr (bias=0) doner; auto-trader hicbir zaman bu
# yuzden calismayi durdurmaz (fail-open).
# ============================================================
FUNDING_RATE_EXTREME = float(os.getenv("FUNDING_RATE_EXTREME_PCT", "0.05")) / 100.0  # %0.05 varsayilan
FEAR_GREED_EXTREME_LOW = int(os.getenv("FEAR_GREED_EXTREME_LOW", "25"))
FEAR_GREED_EXTREME_HIGH = int(os.getenv("FEAR_GREED_EXTREME_HIGH", "75"))
EXTERNAL_SIGNALS_ENABLED = os.getenv("EXTERNAL_SIGNALS_ENABLED", "true").lower() == "true"

_external_signal_cache: Dict[str, Dict[str, Any]] = {}
_external_signal_lock = threading.Lock()


def _cache_get_or_fetch(key: str, ttl_seconds: int, fetch_fn):
    with _external_signal_lock:
        entry = _external_signal_cache.get(key)
        if entry and time.time() < entry.get("expires_at", 0):
            return entry.get("data")
    try:
        data = fetch_fn()
    except Exception as e:
        data = {"error": str(e)}
    with _external_signal_lock:
        _external_signal_cache[key] = {"data": data, "expires_at": time.time() + ttl_seconds}
    return data


def _invalidate_cache(key: str) -> None:
    with _external_signal_lock:
        _external_signal_cache.pop(key, None)


def get_whale_positioning(symbol: str) -> Dict[str, Any]:
    """Binance Futures 'top trader' (buyuk hesap) long/short pozisyon orani.
    Whale Alert/Etherscan gibi zincir-ustu (on-chain) servisler API anahtari
    gerektirdigi icin, borsa-ici gercek buyuk hesap pozisyonlama verisini
    (anahtar gerektirmez, herkese acik) kullaniyoruz. Asiri tek yonlu yigilma
    (long veya short) tarihsel olarak ters yonde (contrarian) sinyal tasir."""
    def _fetch():
        base = FUTURES_BASE
        data = public_get(base, "/futures/data/topLongShortPositionRatio", {"symbol": symbol, "period": "1h", "limit": 2})
        if not isinstance(data, list) or not data:
            raise RuntimeError("Top trader pozisyon verisi bos döndü.")
        row = data[-1]
        ratio = safe_float(row.get("longShortRatio"))
        long_acc = safe_float(row.get("longAccount")) * 100
        short_acc = safe_float(row.get("shortAccount")) * 100
        return {
            "symbol": symbol,
            "long_short_ratio": round(ratio, 3),
            "long_account_pct": round(long_acc, 1),
            "short_account_pct": round(short_acc, 1),
            "time": now_text(),
        }
    return _cache_get_or_fetch(f"whale_pos:{symbol}", 900, _fetch)


WHALE_RATIO_EXTREME_HIGH = float(os.getenv("WHALE_RATIO_EXTREME_HIGH", "2.5"))
WHALE_RATIO_EXTREME_LOW = float(os.getenv("WHALE_RATIO_EXTREME_LOW", "0.5"))


def get_geopolitical_risk_signal() -> Dict[str, Any]:
    """GDELT Project (ucretsiz, anahtar gerekmez) uzerinden savas/jeopolitik gerginlik
    haberlerinin hacim ve ton (tone) ortalamasini olcer. Cok negatif ton + yuksek hacim
    'risk-off' (guvenli limana kacis) egilimini gucllendirir; bu genelde kriptoyu de
    olumsuz etkiler (bkz. makro RISK_OFF rejimi ile ayni mantik)."""
    def _fetch():
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query": "(war OR invasion OR conflict OR sanctions)",
                "mode": "timelinetone",
                "format": "json",
                "timespan": "2d",
            },
            timeout=10,
            headers={"User-Agent": "dfinans-live-backend/1.0"},
        )
        r.raise_for_status()
        js = r.json()
        series = (js.get("timeline") or [{}])[0].get("data", [])
        if not series:
            raise RuntimeError("GDELT verisi bos döndü.")
        avg_tone = sum(safe_float(pt.get("value")) for pt in series) / len(series)
        level = "YUKSEK_GERGINLIK" if avg_tone <= -4 else ("DUSUK_GERGINLIK" if avg_tone >= -1 else "NORMAL")
        return {"avg_tone": round(avg_tone, 2), "level": level, "time": now_text()}
    return _cache_get_or_fetch("geopolitical_risk", 7200, _fetch)


def get_regulatory_activity_signal(keywords: str = "bitcoin OR cryptocurrency OR digital asset") -> Dict[str, Any]:
    """SEC EDGAR tam metin arama API'si (ucretsiz, anahtar gerekmez, sadece User-Agent
    kimligi istiyor) uzerinden son 24 saatte kripto ile ilgili 8-K/kurumsal dosyalama
    hacmini onceki gunlerle karsilastirir. Ani bir sicrama, piyasayi etkileyebilecek
    onemli bir duzenleyici/kurumsal aciklama olabilecegini isaret eder (yon belirsiz,
    bu yuzden yalnizca temkin/oynaklik uyarisi olarak kullanilir, yonlu bias vermez)."""
    def _fetch():
        headers = {"User-Agent": "dfinans-live-backend research contact@dfinans.example"}
        today = datetime.now()
        def count_for_range(start, end):
            r = requests.get(
                "https://efts.sec.gov/LATEST/search-index",
                params={
                    "q": keywords,
                    "forms": "8-K",
                    "dateRange": "custom",
                    "startdt": start.strftime("%Y-%m-%d"),
                    "enddt": end.strftime("%Y-%m-%d"),
                },
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            js = r.json()
            return int(((js.get("hits") or {}).get("total") or {}).get("value", 0))

        today_count = count_for_range(today - timedelta(days=1), today)
        baseline_count = count_for_range(today - timedelta(days=8), today - timedelta(days=1))
        baseline_daily_avg = max(1.0, baseline_count / 7.0)
        spike_ratio = today_count / baseline_daily_avg
        spike = spike_ratio >= 2.5 and today_count >= 5
        return {
            "filings_last_24h": today_count,
            "baseline_daily_avg": round(baseline_daily_avg, 1),
            "spike_ratio": round(spike_ratio, 2),
            "spike_detected": spike,
            "time": now_text(),
        }
    return _cache_get_or_fetch("sec_regulatory_activity", 10800, _fetch)


NEWS_POSITIVE_KEYWORDS = [
    "surge", "rally", "jump", "soar", "record high", "all-time high", "approve", "approval",
    "bullish", "adopt", "adoption", "gain", "breakout", "inflow", "etf launch", "upgrade",
    "partnership", "buy the dip", "recovery", "rebound",
]
NEWS_NEGATIVE_KEYWORDS = [
    "crash", "plunge", "hack", "hacked", "exploit", "ban", "banned", "lawsuit", "sues", "sec sues",
    "bearish", "dump", "liquidation", "liquidated", "fraud", "collapse", "bankrupt", "bankruptcy",
    "outflow", "delist", "scam", "investigation", "fine", "penalty", "sell-off", "selloff",
]


def get_news_sentiment_signal() -> Dict[str, Any]:
    """CoinDesk RSS besleme (ucretsiz, anahtar gerekmez) uzerinden son basliklarda basit
    anahtar kelime tabanli sentiment skoru hesaplar. CryptoPanic gibi servisler API anahtari
    gerektirdigi icin bu anahtarsiz alternatif kullanildi. Net sentiment pozitifse haber akisi
    BUY'i, negatifse SELL'i destekler (contrarian degil, dogrudan yon takibi)."""
    def _fetch():
        import xml.etree.ElementTree as ET
        r = requests.get(
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (dfinans-live-backend)"},
        )
        r.raise_for_status()
        root = ET.fromstring(r.content)
        titles = [item.findtext("title", "") for item in root.findall(".//item")][:20]
        if not titles:
            raise RuntimeError("RSS verisi bos döndü.")
        pos = neg = 0
        for t in titles:
            low = t.lower()
            pos += sum(1 for k in NEWS_POSITIVE_KEYWORDS if k in low)
            neg += sum(1 for k in NEWS_NEGATIVE_KEYWORDS if k in low)
        total = pos + neg
        net_score = (pos - neg) / total if total > 0 else 0.0
        return {
            "headlines_scanned": len(titles),
            "positive_hits": pos,
            "negative_hits": neg,
            "net_sentiment": round(net_score, 2),
            "time": now_text(),
        }
    return _cache_get_or_fetch("news_sentiment", 1800, _fetch)


def get_google_trends_signal(keyword: str = "bitcoin") -> Dict[str, Any]:
    """Google Trends (pytrends, resmi olmayan/gayri-resmi kutuphane) uzerinden ani arama
    ilgisi artisini tespit eder. Bu servis resmi API olmadigi ve sunucu ortamlarinda siklikla
    hiz siniri/engellemeye takildigi icin TAMAMEN best-effort'tur; basarisiz olursa sessizce
    norotr doner ve auto-trader'i hicbir sekilde etkilemez (fail-open)."""
    def _fetch():
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=360, timeout=(5, 10))
        pytrends.build_payload([keyword], timeframe="now 7-d")
        df = pytrends.interest_over_time()
        if df is None or df.empty:
            raise RuntimeError("Google Trends verisi bos döndü.")
        recent_avg = df[keyword].iloc[-6:-1].mean() if len(df) >= 6 else df[keyword].mean()
        latest = df[keyword].iloc[-1]
        spike_ratio = float(latest / recent_avg) if recent_avg > 0 else 1.0
        return {
            "keyword": keyword,
            "latest_interest": int(latest),
            "recent_avg_interest": round(float(recent_avg), 1),
            "spike_ratio": round(spike_ratio, 2),
            "spike_detected": spike_ratio >= 1.8,
            "time": now_text(),
        }
    return _cache_get_or_fetch(f"google_trends:{keyword}", 3600, _fetch)


def get_funding_rate(symbol: str) -> Dict[str, Any]:
    """Binance Futures fonlama orani (premiumIndex). Pozitif -> long'lar short'lara odeme yapiyor
    (piyasa asiri iyimser/kalabalik long); negatif -> tam tersi (asiri kotumser/kalabalik short).
    Asiri degerler genelde kisa vadeli TERS (contrarian) sinyal tasir."""
    def _fetch():
        base = FUTURES_BASE
        data = public_get(base, "/fapi/v1/premiumIndex", {"symbol": symbol})
        if isinstance(data, list):
            data = data[0] if data else {}
        rate = safe_float(data.get("lastFundingRate"))
        return {"symbol": symbol, "funding_rate": rate, "funding_rate_pct": round(rate * 100, 4), "time": now_text()}
    return _cache_get_or_fetch(f"funding:{symbol}", 300, _fetch)


def get_fear_greed_index() -> Dict[str, Any]:
    """alternative.me Crypto Fear & Greed Index (ucretsiz, anahtar gerekmez).
    0-25: Aşırı Korku (genelde dip bolgesi/contrarian AL), 75-100: Aşırı Açgözlülük (genelde tepe/contrarian SAT)."""
    def _fetch():
        r = requests.get("https://api.alternative.me/fng/?limit=1", timeout=8)
        r.raise_for_status()
        js = r.json()
        row = (js.get("data") or [{}])[0]
        value = int(safe_float(row.get("value")))
        classification = str(row.get("value_classification", ""))
        return {"value": value, "classification": classification, "time": now_text()}
    return _cache_get_or_fetch("fear_greed", 1800, _fetch)


def get_external_signal_bias(symbol: str, action: str) -> Dict[str, Any]:
    """Funding rate + Fear&Greed Index'i birlestirip verilen islem yonune (BUY/SELL)
    confidence puanina eklenecek/cikarilacak bir bias ve aciklama uretir."""
    if not EXTERNAL_SIGNALS_ENABLED or action not in ("BUY", "SELL"):
        return {"bias": 0, "notes": []}

    bias = 0
    notes: List[str] = []

    fr = get_funding_rate(symbol)
    if not fr.get("error"):
        rate = safe_float(fr.get("funding_rate"))
        if rate >= FUNDING_RATE_EXTREME:
            # Asiri pozitif funding: piyasa kalabalik LONG -> yukselise (BUY) karsi temkinli ol,
            # dususe (SELL) hafif destek ver (contrarian).
            if action == "BUY":
                bias -= 6
                notes.append(f"Funding rate aşırı pozitif (%{fr['funding_rate_pct']:.3f}): piyasa kalabalık LONG, yeni alım riskli.")
            else:
                bias += 4
                notes.append(f"Funding rate aşırı pozitif (%{fr['funding_rate_pct']:.3f}): kalabalık long tasfiyesi SELL sinyalini destekliyor.")
        elif rate <= -FUNDING_RATE_EXTREME:
            if action == "SELL":
                bias -= 6
                notes.append(f"Funding rate aşırı negatif (%{fr['funding_rate_pct']:.3f}): piyasa kalabalık SHORT, yeni satış riskli.")
            else:
                bias += 4
                notes.append(f"Funding rate aşırı negatif (%{fr['funding_rate_pct']:.3f}): kalabalık short tasfiyesi BUY sinyalini destekliyor.")

    fg = get_fear_greed_index()
    if not fg.get("error"):
        value = int(fg.get("value", 50))
        if value <= FEAR_GREED_EXTREME_LOW:
            if action == "BUY":
                bias += 4
                notes.append(f"Fear & Greed Index aşırı korku ({value}): tarihsel olarak dip bölgesi, BUY'ı destekler.")
            else:
                bias -= 4
                notes.append(f"Fear & Greed Index aşırı korku ({value}): panik satışına katılmak riskli olabilir.")
        elif value >= FEAR_GREED_EXTREME_HIGH:
            if action == "SELL":
                bias += 4
                notes.append(f"Fear & Greed Index aşırı açgözlülük ({value}): tarihsel olarak tepe bölgesi, SELL'i destekler.")
            else:
                bias -= 4
                notes.append(f"Fear & Greed Index aşırı açgözlülük ({value}): FOMO ile alım riskli olabilir.")

    macro = get_macro_regime()
    if not macro.get("error"):
        regime = macro.get("regime")
        if regime == "RISK_ON":
            if action == "BUY":
                bias += 5
                notes.append(f"Makro rejim RISK-ON (SP500 5g %{macro['sp500_5d_pct']:+.1f}, DXY %{macro['dxy_5d_pct']:+.1f}): BUY'ı destekler.")
            else:
                bias -= 5
                notes.append(f"Makro rejim RISK-ON: borsa güçlü, short açmak tarihsel olarak zayıf performans gösterir.")
        elif regime == "RISK_OFF":
            if action == "SELL":
                bias += 5
                notes.append(f"Makro rejim RISK-OFF (SP500 5g %{macro['sp500_5d_pct']:+.1f}, DXY %{macro['dxy_5d_pct']:+.1f}): SELL'i destekler.")
            else:
                bias -= 5
                notes.append(f"Makro rejim RISK-OFF: borsa/dolar baskısı var, yeni alım riskli olabilir.")

    whale = get_whale_positioning(symbol)
    if not whale.get("error"):
        ratio = safe_float(whale.get("long_short_ratio"))
        if ratio >= WHALE_RATIO_EXTREME_HIGH:
            if action == "BUY":
                bias -= 5
                notes.append(f"Büyük hesaplar aşırı LONG yığılmış (oran {ratio:.2f}): yeni alım riskli, tasfiye riski var.")
            else:
                bias += 3
                notes.append(f"Büyük hesaplar aşırı LONG yığılmış (oran {ratio:.2f}): olası long tasfiyesi SELL'i destekler.")
        elif ratio > 0 and ratio <= WHALE_RATIO_EXTREME_LOW:
            if action == "SELL":
                bias -= 5
                notes.append(f"Büyük hesaplar aşırı SHORT yığılmış (oran {ratio:.2f}): yeni satış riskli, short squeeze riski var.")
            else:
                bias += 3
                notes.append(f"Büyük hesaplar aşırı SHORT yığılmış (oran {ratio:.2f}): olası short squeeze BUY'ı destekler.")

    geo = get_geopolitical_risk_signal()
    if not geo.get("error"):
        level = geo.get("level")
        if level == "YUKSEK_GERGINLIK":
            if action == "BUY":
                bias -= 4
                notes.append(f"Jeopolitik gerginlik yüksek (GDELT ton {geo['avg_tone']:.1f}): risk-off ortamı, alım riskli olabilir.")
            else:
                bias += 2
                notes.append(f"Jeopolitik gerginlik yüksek (GDELT ton {geo['avg_tone']:.1f}): risk-off ortamı SELL'i hafif destekler.")

    reg = get_regulatory_activity_signal()
    if not reg.get("error") and reg.get("spike_detected"):
        bias -= 3
        notes.append(f"Kripto ile ilgili SEC 8-K dosyalama hacminde sıçrama var (son 24s: {reg['filings_last_24h']}, ort: {reg['baseline_daily_avg']}): yön belirsiz, temkinli olunmalı.")

    news = get_news_sentiment_signal()
    if not news.get("error"):
        net = safe_float(news.get("net_sentiment"))
        if net >= 0.4:
            if action == "BUY":
                bias += 3
                notes.append(f"Haber akışı net pozitif (skor {net:+.2f}): BUY'ı destekler.")
            else:
                bias -= 2
                notes.append(f"Haber akışı net pozitif (skor {net:+.2f}): SELL için olumsuz.")
        elif net <= -0.4:
            if action == "SELL":
                bias += 3
                notes.append(f"Haber akışı net negatif (skor {net:+.2f}): SELL'i destekler.")
            else:
                bias -= 2
                notes.append(f"Haber akışı net negatif (skor {net:+.2f}): BUY için olumsuz.")

    trends = get_google_trends_signal()
    if not trends.get("error") and trends.get("spike_detected"):
        # Yon belirsiz (ani ilgi artisi hem FOMO/rally hem panik/crash haberinden kaynaklanabilir);
        # sadece "dikkat, oynaklik artabilir" seklinde hafif bir temkin sinyali ekler.
        bias -= 1
        notes.append(f"Google Trends'te '{trends['keyword']}' aramalarında ani artış (x{trends['spike_ratio']:.1f}): olası yüksek oynaklık, dikkatli olunmalı.")

    return {"bias": max(-16, min(16, bias)), "notes": notes}


def get_macro_regime() -> Dict[str, Any]:
    """SP500 ve Dolar Endeksi'nin son 5 islem gunu momentumuna gore 'risk rejimi' belirler.
    Tarihsel analize gore (bkz. 5 yillik senaryo calismasi):
      - Borsa YUKARI + Dolar ASAGI/notr  -> RISK_ON  (BTC ort. +1.20%/gun)
      - Borsa ASAGI  + Dolar YUKARI      -> RISK_OFF (BTC ort. -1.13%/gun)
      - Digerleri -> NOTR
    yfinance Yahoo Finance'tan veri cektigi icin agir/yavas olabilir; bu yuzden sonuc
    uzun sureli (4 saat) cache'lenir ve hata durumunda sessizce NOTR'e duser (fail-open)."""
    def _fetch():
        import yfinance as yf
        data = yf.download(["^GSPC", "DX-Y.NYB"], period="15d", interval="1d", progress=False, auto_adjust=True, threads=True)
        close = data["Close"].dropna()
        if len(close) < 6:
            raise RuntimeError("Yetersiz makro veri")
        sp500_5d = (close["^GSPC"].iloc[-1] / close["^GSPC"].iloc[-6] - 1.0) * 100.0
        dxy_5d = (close["DX-Y.NYB"].iloc[-1] / close["DX-Y.NYB"].iloc[-6] - 1.0) * 100.0
        if sp500_5d > 0 and dxy_5d <= 0:
            regime = "RISK_ON"
        elif sp500_5d < 0 and dxy_5d > 0:
            regime = "RISK_OFF"
        else:
            regime = "NEUTRAL"
        return {
            "sp500_5d_pct": round(float(sp500_5d), 2),
            "dxy_5d_pct": round(float(dxy_5d), 2),
            "regime": regime,
            "time": now_text(),
        }
    return _cache_get_or_fetch("macro_regime", 14400, _fetch)


def get_macro_risk_bias(symbol: str, action: str) -> Dict[str, Any]:
    """Balon/asiri degerleme, bilanco/nakit akis sagligi, short/long pozisyonlanma
    ve manipulasyon taramasi, ve sektorler arasi senaryo analizini (hepsi
    /valuation-bubble-analysis'te de gosterilen ayni veriler) AI karar mekanizmasina
    baglar - boylece bu analizler sadece ekranda gorunmekle kalmaz, otomatik
    alim-satim kararlarini da etkiler. Agir olan tum alt fonksiyonlar zaten
    6-12 saat cache'li oldugu icin burada ek maliyet yaratmaz."""
    if action not in ("BUY", "SELL"):
        return {"bias": 0, "notes": []}

    bias = 0
    notes: List[str] = []

    try:
        valuation = get_valuation_bubble_analysis()
        if valuation.get("crash_risk_level") == "YÜKSEK" and action == "BUY":
            bias -= 8
            notes.append(f"Genel piyasa çöküş/düzeltme riski YÜKSEK ({valuation.get('summary', '')}): yeni alım riskli.")
        elif valuation.get("crash_risk_level") == "YÜKSEK" and action == "SELL":
            bias += 3
            notes.append("Genel piyasa çöküş/düzeltme riski YÜKSEK: SELL'i hafif destekler.")

        asset_key = None
        base_symbol = symbol.replace("USDT", "").replace("USD", "").upper()
        if base_symbol == "BTC":
            asset_key = "BTC"
        for a in valuation.get("assets", []):
            if a.get("key") == asset_key and action == "BUY" and a.get("overheat_score", 0) >= 3:
                bias -= 5
                notes.append(f"{a.get('name')} istatistiksel olarak aşırı ısınmış ({a.get('status')}): alım riski artıyor.")
    except Exception:
        pass

    try:
        book_val = get_fundamental_valuation_analysis()
        for a in book_val.get("assets", []):
            if a.get("symbol") == symbol and "PAHALI" in str(a.get("status", "")) and action == "BUY":
                bias -= 4
                notes.append(f"{symbol} defter değerine göre pahalı (P/B {a.get('price_to_book')}): alım riski artıyor.")
    except Exception:
        pass

    try:
        fin = get_financial_statement_analysis()
        for a in fin.get("assets", []):
            if a.get("symbol") == symbol and a.get("status") == "FİNANSAL RİSK YÜKSEK" and action == "BUY":
                bias -= 5
                notes.append(f"{symbol} bilanço/nakit akışı zayıf (Altman Z: {a.get('altman_z_score')}): alım riski artıyor.")
    except Exception:
        pass

    try:
        positioning = get_market_positioning_and_manipulation_analysis()
        for a in positioning.get("crypto_positioning", []) + positioning.get("stock_positioning", []):
            if a.get("symbol") == symbol and a.get("status") != "NORMAL":
                bias -= 4
                flag_text = "; ".join(a.get("flags", [])[:1])
                notes.append(f"{symbol} için pozisyonlanma/manipülasyon uyarısı: {flag_text}")
    except Exception:
        pass

    try:
        scenarios = get_sector_scenario_analysis()
        for s in scenarios.get("scenarios", []):
            if s.get("status") != "AKTİF":
                continue
            for affected in s.get("affected_sectors", []):
                sector_text = str(affected.get("sector", ""))
                if base_symbol not in sector_text.upper() and symbol not in sector_text.upper():
                    continue
                impact = affected.get("impact")
                if impact == "OLUMLU" and action == "BUY":
                    bias += 3
                    notes.append(f"Aktif senaryo '{s.get('title')}': {sector_text} için OLUMLU, BUY'ı destekler.")
                elif impact == "OLUMSUZ" and action == "SELL":
                    bias += 3
                    notes.append(f"Aktif senaryo '{s.get('title')}': {sector_text} için OLUMSUZ, SELL'i destekler.")
                elif impact == "OLUMSUZ" and action == "BUY":
                    bias -= 3
                    notes.append(f"Aktif senaryo '{s.get('title')}': {sector_text} için OLUMSUZ, alım riski artıyor.")
                elif impact == "OLUMLU" and action == "SELL":
                    bias -= 3
                    notes.append(f"Aktif senaryo '{s.get('title')}': {sector_text} için OLUMLU, satış riski artıyor.")
    except Exception:
        pass

    return {"bias": max(-16, min(16, bias)), "notes": notes}



    """SP500 ve Dolar Endeksi'nin son 5 islem gunu momentumuna gore 'risk rejimi' belirler.
    Tarihsel analize gore (bkz. 5 yillik senaryo calismasi):
      - Borsa YUKARI + Dolar ASAGI/notr  -> RISK_ON  (BTC ort. +1.20%/gun)
      - Borsa ASAGI  + Dolar YUKARI      -> RISK_OFF (BTC ort. -1.13%/gun)
      - Digerleri -> NOTR
    yfinance Yahoo Finance'tan veri cektigi icin agir/yavas olabilir; bu yuzden sonuc
    uzun sureli (4 saat) cache'lenir ve hata durumunda sessizce NOTR'e duser (fail-open)."""
    def _fetch():
        import yfinance as yf
        data = yf.download(["^GSPC", "DX-Y.NYB"], period="15d", interval="1d", progress=False, auto_adjust=True, threads=True)
        close = data["Close"].dropna()
        if len(close) < 6:
            raise RuntimeError("Yetersiz makro veri")
        sp500_5d = (close["^GSPC"].iloc[-1] / close["^GSPC"].iloc[-6] - 1.0) * 100.0
        dxy_5d = (close["DX-Y.NYB"].iloc[-1] / close["DX-Y.NYB"].iloc[-6] - 1.0) * 100.0
        if sp500_5d > 0 and dxy_5d <= 0:
            regime = "RISK_ON"
        elif sp500_5d < 0 and dxy_5d > 0:
            regime = "RISK_OFF"
        else:
            regime = "NEUTRAL"
        return {
            "sp500_5d_pct": round(float(sp500_5d), 2),
            "dxy_5d_pct": round(float(dxy_5d), 2),
            "regime": regime,
            "time": now_text(),
        }
    return _cache_get_or_fetch("macro_regime", 14400, _fetch)


_VALUATION_ASSETS: Dict[str, tuple] = {
    "SPX": ("^GSPC", "S&P 500 (ABD Borsası)"),
    "NASDAQ": ("^IXIC", "Nasdaq (Teknoloji Ağırlıklı)"),
    "GOLD": ("GC=F", "Altın"),
    "XLK": ("XLK", "Teknoloji Sektörü"),
    "XLF": ("XLF", "Finans Sektörü"),
    "XLE": ("XLE", "Enerji Sektörü"),
    "XLV": ("XLV", "Sağlık Sektörü"),
    "XLY": ("XLY", "Tüketici (İsteğe Bağlı) Sektörü"),
    "XLP": ("XLP", "Gıda/Temel Tüketim Sektörü"),
    "ITA": ("ITA", "Savunma Sanayi Sektörü"),
    "SMH": ("SMH", "Yarı İletken (Çip) Sektörü"),
    "BTC": ("BTC-USD", "Bitcoin"),
}


def get_valuation_bubble_analysis() -> Dict[str, Any]:
    """ABD borsalari, altin ve ana sektorlerin son 1 yillik fiyat verisinden
    istatistiksel 'asiri degerleme / balon' analizi uretir: 1 yillik getiri,
    200 gunluk ortalamadan sapma, kendi 1 yillik ortalamasina gore z-skoru ve
    yillik volatilite kullanilarak her varlik icin bir 'isinma skoru' hesaplanir.
    VIX + Fear&Greed endeksiyle birlikte genel 'piyasa cokusu/duzeltme riski'
    seviyesi (DUSUK/ORTA/YUKSEK) belirlenir. Yatirim tavsiyesi degil, istatistiksel
    bir gosterge niteligindedir - agir yfinance cagrisi oldugu icin 6 saat cache'lenir."""
    def _fetch():
        import yfinance as yf

        tickers = [t for t, _ in _VALUATION_ASSETS.values()]
        data = yf.download(tickers, period="1y", interval="1d", progress=False, auto_adjust=True, threads=True)
        close = data["Close"] if "Close" in data else data
        results: List[Dict[str, Any]] = []
        overheat_count = 0

        for key, (ticker, name) in _VALUATION_ASSETS.items():
            try:
                series = close[ticker].dropna() if ticker in close else close.dropna()
                if len(series) < 60:
                    continue
                current = float(series.iloc[-1])
                year_ago = float(series.iloc[0])
                change_1y_pct = (current / year_ago - 1.0) * 100.0 if year_ago else 0.0
                high_1y = float(series.max())
                dist_from_high_pct = (current / high_1y - 1.0) * 100.0 if high_1y else 0.0
                ma200 = float(series.tail(200).mean())
                dist_from_ma200_pct = (current / ma200 - 1.0) * 100.0 if ma200 else 0.0
                mean_price = float(series.mean())
                std_price = float(series.std())
                z_score = (current - mean_price) / std_price if std_price > 0 else 0.0
                returns = series.pct_change().dropna()
                ann_vol_pct = float(returns.std() * (252 ** 0.5) * 100.0) if len(returns) > 5 else 0.0
                last_month_change_pct = (
                    (float(series.iloc[-1]) / float(series.iloc[-21]) - 1.0) * 100.0 if len(series) > 21 else 0.0
                )

                score = 0
                reasons: List[str] = []
                if change_1y_pct > 40:
                    score += 2
                    reasons.append(f"1 yılda %{change_1y_pct:.0f} yükseliş (aşırı hızlı)")
                elif change_1y_pct > 20:
                    score += 1
                    reasons.append(f"1 yılda %{change_1y_pct:.0f} yükseliş (güçlü)")
                if dist_from_ma200_pct > 20:
                    score += 2
                    reasons.append(f"200 günlük ortalamanın %{dist_from_ma200_pct:.0f} üzerinde (aşırı uzamış)")
                elif dist_from_ma200_pct > 10:
                    score += 1
                if z_score > 2:
                    score += 2
                    reasons.append(f"1 yıllık ortalamanın {z_score:.1f} standart sapma üzerinde (istatistiksel olarak aşırı)")
                elif z_score > 1.2:
                    score += 1
                if dist_from_high_pct > -3:
                    score += 1
                    reasons.append("1 yılın zirvesine çok yakın")

                if score >= 5:
                    status = "BALON RİSKİ YÜKSEK"
                elif score >= 3:
                    status = "AŞIRI DEĞERLİ / ISINMIŞ"
                elif score <= 0 and change_1y_pct < 0:
                    status = "UCUZ / BASKI ALTINDA"
                    reasons.append(f"1 yılda %{change_1y_pct:.0f} (negatif)")
                else:
                    status = "NORMAL"

                if score >= 3:
                    overheat_count += 1

                results.append({
                    "key": key,
                    "name": name,
                    "change_1y_pct": round(change_1y_pct, 2),
                    "distance_from_1y_high_pct": round(dist_from_high_pct, 2),
                    "distance_from_ma200_pct": round(dist_from_ma200_pct, 2),
                    "z_score": round(z_score, 2),
                    "annualized_volatility_pct": round(ann_vol_pct, 2),
                    "last_month_change_pct": round(last_month_change_pct, 2),
                    "overheat_score": score,
                    "status": status,
                    "reasons": reasons,
                })
            except Exception:
                continue

        vix_val = 0.0
        try:
            vix_data = try_yahoo_ticker("VIX")
            vix_val = safe_float((vix_data or {}).get("price"))
        except Exception:
            pass

        fg_val = 50.0
        try:
            fg = get_fear_greed_index()
            fg_val = safe_float(fg.get("value")) if isinstance(fg, dict) and fg.get("value") is not None else 50.0
        except Exception:
            pass

        crash_risk_score = 0
        crash_reasons: List[str] = []
        if overheat_count >= 4:
            crash_risk_score += 2
            crash_reasons.append(f"{overheat_count} varlık/sektör aşırı ısınmış görünüyor - geniş tabanlı balon riski")
        elif overheat_count >= 2:
            crash_risk_score += 1
            crash_reasons.append(f"{overheat_count} varlık/sektör aşırı ısınmış görünüyor")
        if 0 < vix_val < 14:
            crash_risk_score += 1
            crash_reasons.append(f"VIX çok düşük ({vix_val:.1f}) - piyasa aşırı rahat, sürpriz şoklara karşı savunmasız")
        if fg_val >= 75:
            crash_risk_score += 1
            crash_reasons.append(f"Fear&Greed endeksi 'Aşırı Açgözlülük' bölgesinde ({fg_val:.0f})")

        if crash_risk_score >= 3:
            crash_risk_level = "YÜKSEK"
            crash_summary = "Piyasada geniş tabanlı aşırı değerleme belirtileri var; sert bir düzeltme riski normalden yüksek."
        elif crash_risk_score >= 1:
            crash_risk_level = "ORTA"
            crash_summary = "Bazı varlıklarda ısınma belirtileri var ama henüz sistemik bir çöküş sinyali yok."
        else:
            crash_risk_level = "DÜŞÜK"
            crash_summary = "Şu an için geniş tabanlı bir balon/çöküş riski görünmüyor."

        return {
            "assets": results,
            "overheat_count": overheat_count,
            "vix": round(vix_val, 2) if vix_val else None,
            "fear_greed_index": round(fg_val, 1) if fg_val else None,
            "crash_risk_level": crash_risk_level,
            "crash_risk_score": crash_risk_score,
            "crash_risk_reasons": crash_reasons,
            "summary": crash_summary,
            "note": "Bu analiz istatistiksel bir yaklaşımdır (fiyat/ortalama sapması, volatilite, momentum); kesin bir öngörü değildir, yatırım tavsiyesi yerine geçmez.",
            "time": now_text(),
        }

    return _cache_get_or_fetch("valuation_bubble_analysis", 21600, _fetch)


def get_macro_dashboard_raw() -> Dict[str, Any]:
    """VIX/Nasdaq/S&P500/DXY/Altin/Petrol icin Yahoo Finance'tan canli fiyat
    ceker (2 dakika cache). iOS uygulamasindaki Piyasalar ekranindaki makro
    panel /dd-ai-dashboard endpoint'inden bu veriyi bekliyordu ama bu route
    hic yoktu - panel sonsuza dek 'veri bekleniyor' placeholder'inda kaliyordu."""
    def _fetch():
        out = {}
        for key in ["VIX", "NASDAQ", "SP500", "DXY", "GOLD", "OIL"]:
            try:
                t = try_yahoo_ticker(key)
            except Exception:
                t = None
            out[key] = t
        return out
    return _cache_get_or_fetch("macro_dashboard_raw", 120, _fetch)


def get_fundamental_valuation_analysis() -> Dict[str, Any]:
    """Hisse senetleri icin defter degeri (book value) bazli temel degerleme
    analizi: Piyasa Fiyati / Defter Degeri orani (P/B) hesaplanir. P/B ne kadar
    yuksekse hisse, sirketin net oz kaynagina (varlik - borc) gore o kadar
    'pahali' fiyatlanmis demektir - buyume beklentisi yuksek teknoloji hisselerinde
    normal olabilir ama asiri yuksekse (>15) balon/asiri iyimserlik isareti sayilir.
    IBKR watchlist'indeki hisseler + birkac buyuk sirket taranir. yfinance .info
    cagrisi agir oldugu icin 6 saat cache'lenir, hata durumunda sessizce atlanir."""
    def _fetch():
        import yfinance as yf

        symbols = sorted(set(_parse_symbol_list(_IBKR_WATCHLIST_DEFAULT)) | {
            "AAPL", "MSFT", "NVDA", "AMD", "TSLA", "F", "T", "GOOGL", "AMZN", "META",
        })
        results: List[Dict[str, Any]] = []
        for sym in symbols:
            try:
                info = yf.Ticker(sym).info or {}
                pb = safe_float(info.get("priceToBook"))
                if pb <= 0:
                    continue
                book_value = safe_float(info.get("bookValue"))
                price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
                pe = safe_float(info.get("trailingPE"))
                name = str(info.get("shortName") or sym)

                if pb > 15:
                    status = "DEFTER DEĞERİNE GÖRE AŞIRI PAHALI"
                elif pb > 8:
                    status = "DEFTER DEĞERİNE GÖRE PAHALI"
                elif 0 < pb < 1:
                    status = "DEFTER DEĞERİNİN ALTINDA (UCUZ OLABİLİR)"
                else:
                    status = "NORMAL"

                results.append({
                    "symbol": sym,
                    "name": name,
                    "price_to_book": round(pb, 2),
                    "book_value_per_share": round(book_value, 2) if book_value else None,
                    "price": round(price, 2) if price else None,
                    "pe_ratio": round(pe, 2) if pe else None,
                    "status": status,
                })
            except Exception:
                continue

        overpriced = [r for r in results if "PAHALI" in r["status"]]
        return {
            "assets": results,
            "overpriced_count": len(overpriced),
            "overpriced_symbols": [r["symbol"] for r in overpriced],
            "note": (
                "P/B (Piyasa Fiyatı/Defter Değeri) oranı 8'in üzeri pahalı, 15'in üzeri aşırı "
                "pahalı kabul edilir; sektöre göre değişebileceğinden kesin ölçü değildir."
            ),
            "time": now_text(),
        }

    return _cache_get_or_fetch("fundamental_valuation", 21600, _fetch)


def _statement_row(df, candidates: List[str]) -> Optional[List[float]]:
    """yfinance bilanco/nakit akis DataFrame'inden verilen olasi satir adlarindan
    ilk bulunani sutun sirasiyla (en yeniden en eskiye) liste olarak dondurur."""
    if df is None or df.empty:
        return None
    for name in candidates:
        if name in df.index:
            row = df.loc[name]
            try:
                return [float(v) for v in row.tolist() if v is not None and str(v) != "nan"]
            except Exception:
                continue
    return None


def get_financial_statement_analysis() -> Dict[str, Any]:
    """Hisse senetleri icin profesyonel seviyede bilanco + gelir tablosu + nakit
    akis tablosu analizi uretir:
      - Borc/Oz Kaynak, Cari Oran (likidite)
      - Serbest Nakit Akisi (FCF) seviyesi ve yillik trendi, Operasyonel Nakit Akisi
      - ROE (Oz Kaynak Karliligi), ROA (Aktif Karliligi), Net Kar Marji
      - Yillik Gelir Buyumesi (YoY), Faiz Karsilama Orani (EBIT/Faiz Gideri)
      - Altman Z-Skoru (klasik iflas riski modeli - profesyonel kredi analistlerinin
        kullandigi 5 degiskenli formul): Z = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
        (A=Isletme Sermayesi/Toplam Aktif, B=Dagitilmamis Kar/Toplam Aktif,
         C=FVOK/Toplam Aktif, D=Piyasa Degeri/Toplam Borc, E=Satislar/Toplam Aktif)
        Z > 2.99: Güvenli bölge, 1.81-2.99: Gri bölge, < 1.81: İflas riski bölgesi.
    Yuksek borc/oz kaynak orani, negatif/azalan FCF, dusuk cari oran, dusuk/negatif
    ROE-ROA ve dusuk Altman Z-skoru finansal risk isaretleri olarak raporlanir.
    yfinance'in yillik bilanco/gelir tablosu/nakit akis verileri kullanilir (agir
    cagri - 12 saat cache'lenir, sirket bazinda hata olursa o sirket sessizce atlanir)."""
    def _fetch():
        import yfinance as yf

        symbols = sorted(set(_parse_symbol_list(_IBKR_WATCHLIST_DEFAULT)) | {
            "AAPL", "MSFT", "NVDA", "AMD", "TSLA", "F", "T", "GOOGL", "AMZN", "META",
        })
        results: List[Dict[str, Any]] = []
        for sym in symbols:
            try:
                tk = yf.Ticker(sym)
                bs = tk.balance_sheet
                cf = tk.cashflow
                inc = tk.financials
                info = tk.info or {}

                total_debt = _statement_row(bs, ["Total Debt"])
                equity = _statement_row(bs, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"])
                current_assets = _statement_row(bs, ["Current Assets", "Total Current Assets"])
                current_liabilities = _statement_row(bs, ["Current Liabilities", "Total Current Liabilities"])
                total_assets = _statement_row(bs, ["Total Assets"])
                total_liabilities = _statement_row(bs, ["Total Liabilities Net Minority Interest", "Total Liab"])
                retained_earnings = _statement_row(bs, ["Retained Earnings"])

                op_cf = _statement_row(cf, ["Operating Cash Flow", "Total Cash From Operating Activities"])
                free_cf = _statement_row(cf, ["Free Cash Flow"])
                capex = _statement_row(cf, ["Capital Expenditure", "Capital Expenditures"])

                revenue = _statement_row(inc, ["Total Revenue"])
                net_income = _statement_row(inc, ["Net Income"])
                ebit = _statement_row(inc, ["EBIT", "Operating Income"])
                interest_expense = _statement_row(inc, ["Interest Expense"])

                if free_cf is None and op_cf and capex:
                    free_cf = [o + c for o, c in zip(op_cf, capex)]  # capex negatif gelir, toplanir

                if not equity or equity[0] == 0:
                    continue

                debt_to_equity = round((total_debt[0] / equity[0]), 2) if total_debt and equity[0] else None
                current_ratio = (
                    round(current_assets[0] / current_liabilities[0], 2)
                    if current_assets and current_liabilities and current_liabilities[0]
                    else None
                )
                fcf_latest = round(free_cf[0], 0) if free_cf else None
                fcf_trend = None
                if free_cf and len(free_cf) > 1 and free_cf[1] != 0:
                    fcf_trend = round(((free_cf[0] - free_cf[1]) / abs(free_cf[1])) * 100.0, 1)
                op_cf_latest = round(op_cf[0], 0) if op_cf else None

                roe_pct = round((net_income[0] / equity[0]) * 100.0, 2) if net_income and equity[0] else None
                roa_pct = (
                    round((net_income[0] / total_assets[0]) * 100.0, 2)
                    if net_income and total_assets and total_assets[0]
                    else None
                )
                net_margin_pct = (
                    round((net_income[0] / revenue[0]) * 100.0, 2) if net_income and revenue and revenue[0] else None
                )
                revenue_growth_pct = None
                if revenue and len(revenue) > 1 and revenue[1] != 0:
                    revenue_growth_pct = round(((revenue[0] - revenue[1]) / abs(revenue[1])) * 100.0, 1)
                interest_coverage = None
                if ebit and interest_expense and interest_expense[0]:
                    interest_coverage = round(ebit[0] / abs(interest_expense[0]), 2)

                # Altman Z-Skoru (imalat/genel sirketler icin klasik formul)
                altman_z = None
                market_cap = safe_float(info.get("marketCap"))
                if total_assets and total_assets[0] and current_assets and current_liabilities and total_liabilities:
                    working_capital = current_assets[0] - current_liabilities[0]
                    a = working_capital / total_assets[0]
                    b = (retained_earnings[0] / total_assets[0]) if retained_earnings else 0.0
                    c = (ebit[0] / total_assets[0]) if ebit else 0.0
                    d = (market_cap / total_liabilities[0]) if market_cap and total_liabilities[0] else 0.0
                    e = (revenue[0] / total_assets[0]) if revenue else 0.0
                    altman_z = round(1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e, 2)

                risk_flags: List[str] = []
                if debt_to_equity is not None and debt_to_equity > 2:
                    risk_flags.append(f"Borç/Öz Kaynak oranı yüksek ({debt_to_equity})")
                if current_ratio is not None and current_ratio < 1:
                    risk_flags.append(f"Cari oran 1'in altında ({current_ratio}) - kısa vadeli likidite riski")
                if fcf_latest is not None and fcf_latest < 0:
                    risk_flags.append("Serbest nakit akışı negatif (nakit yakıyor)")
                if fcf_trend is not None and fcf_trend < -20:
                    risk_flags.append(f"Serbest nakit akışı yıllık bazda %{abs(fcf_trend):.0f} geriledi")
                if op_cf_latest is not None and op_cf_latest < 0:
                    risk_flags.append("Operasyonel nakit akışı negatif")
                if roe_pct is not None and roe_pct < 0:
                    risk_flags.append(f"ROE (öz kaynak karlılığı) negatif (%{roe_pct})")
                if net_margin_pct is not None and net_margin_pct < 0:
                    risk_flags.append(f"Net kâr marjı negatif (%{net_margin_pct})")
                if revenue_growth_pct is not None and revenue_growth_pct < -10:
                    risk_flags.append(f"Gelir yıllık bazda %{abs(revenue_growth_pct):.0f} geriledi")
                if interest_coverage is not None and interest_coverage < 2:
                    risk_flags.append(f"Faiz karşılama oranı düşük ({interest_coverage}) - borç servisinde risk")
                if altman_z is not None and altman_z < 1.81:
                    risk_flags.append(f"Altman Z-Skoru iflas riski bölgesinde ({altman_z})")
                elif altman_z is not None and altman_z < 2.99:
                    risk_flags.append(f"Altman Z-Skoru gri bölgede ({altman_z})")

                high_risk_flag_count = sum(
                    1 for f in risk_flags if "iflas" in f or "negatif" in f or "yüksek" in f
                )
                if high_risk_flag_count >= 2 or (altman_z is not None and altman_z < 1.81):
                    status = "FİNANSAL RİSK YÜKSEK"
                elif len(risk_flags) >= 1:
                    status = "DİKKAT"
                else:
                    status = "SAĞLIKLI"

                results.append({
                    "symbol": sym,
                    "debt_to_equity": debt_to_equity,
                    "current_ratio": current_ratio,
                    "free_cash_flow": fcf_latest,
                    "free_cash_flow_yoy_change_pct": fcf_trend,
                    "operating_cash_flow": op_cf_latest,
                    "roe_pct": roe_pct,
                    "roa_pct": roa_pct,
                    "net_margin_pct": net_margin_pct,
                    "revenue_growth_yoy_pct": revenue_growth_pct,
                    "interest_coverage": interest_coverage,
                    "altman_z_score": altman_z,
                    "status": status,
                    "risk_flags": risk_flags,
                })
            except Exception:
                continue

        risky = [r for r in results if r["status"] != "SAĞLIKLI"]
        return {
            "assets": results,
            "risky_count": len(risky),
            "risky_symbols": [r["symbol"] for r in risky],
            "note": (
                "Profesyonel kredi/eşitlik analizi ölçütleri kullanılmıştır: Borç/Öz Kaynak > 2, "
                "Cari Oran < 1, negatif FCF/ROE/Net Marj, Faiz Karşılama < 2 ve Altman Z-Skoru < 1.81 "
                "(iflas riski bölgesi) risk göstergesi kabul edilir; sektöre göre değişebileceğinden "
                "kesin ölçü değildir, yatırım tavsiyesi yerine geçmez."
            ),
            "time": now_text(),
        }

    return _cache_get_or_fetch("financial_statement_analysis", 43200, _fetch)


def get_klines_volume_stats(symbol: str, market: str = "FUTURES", limit: int = 30) -> Optional[Dict[str, Any]]:
    """Son N gunluk mum verisinden ortalama hacim ve son gunun hacim orani ile
    fiyat/hacim uyumsuzlugunu hesaplar. Ani hacim patlamasi (ort. hacmin 3 kati+)
    ama fiyat neredeyse yerinde sayiyorsa (ör. wash-trading/yapay hacim) veya
    tam tersi cok dusuk hacimle sert fiyat hareketi (ince likidite/manipulasyon
    kolayligi) varsa bunu tespit etmek icin kullanilir."""
    try:
        base = FUTURES_BASE if market.upper() == "FUTURES" else SPOT_BASE
        path = "/fapi/v1/klines" if market.upper() == "FUTURES" else "/api/v3/klines"
        data = public_get(base, path, {"symbol": symbol, "interval": "1d", "limit": limit})
        if not isinstance(data, list) or len(data) < 5:
            return None
        volumes = [safe_float(row[5]) for row in data]
        closes = [safe_float(row[4]) for row in data]
        last_volume = volumes[-1]
        prior_volumes = volumes[:-1]
        avg_volume = (sum(prior_volumes) / len(prior_volumes)) if prior_volumes else 0.0
        volume_ratio = (last_volume / avg_volume) if avg_volume > 0 else 0.0
        last_price_change_pct = ((closes[-1] / closes[-2] - 1.0) * 100.0) if len(closes) > 1 and closes[-2] else 0.0
        return {
            "volume_ratio_vs_avg": round(volume_ratio, 2),
            "last_day_change_pct": round(last_price_change_pct, 2),
        }
    except Exception:
        return None


def get_market_positioning_and_manipulation_analysis() -> Dict[str, Any]:
    """Kripto icin: buyuk hesap (whale) long/short orani + fonlama orani (funding
    rate) asiriliklarini ve hacim/fiyat uyumsuzluguna dayali olasi manipulasyon
    (pump&dump, ani hacim patlamasi, asiri kaldiracli tek yonlu yigilma - short
    squeeze/long squeeze riski) isaretlerini tarar.
    Hisse senetleri icin: kisa pozisyon orani (short interest / float), kapanma
    gunu sayisi (short ratio/days-to-cover - yuksekse short squeeze potansiyeli),
    kurumsal ve icerden (insider) sahiplik oranlarini raporlar (yuksek kurumsal
    sahiplik = 'akilli para' ilgisi, dusuk = spekulatif/perakende agirlikli).
    Kripto tarafi 5 dakika, hisse tarafi (yfinance) 6 saat cache'lenir."""
    def _fetch_crypto():
        crypto_symbols = sorted(set(_parse_symbol_list(_BINANCE_WATCHLIST_DEFAULT)) | {"BTCUSDT", "ETHUSDT"})
        results: List[Dict[str, Any]] = []
        for sym in crypto_symbols:
            try:
                whale = get_whale_positioning(sym)
                funding = get_funding_rate(sym)
                vol_stats = get_klines_volume_stats(sym, "FUTURES")
                ratio = safe_float(whale.get("long_short_ratio", 1.0))
                funding_pct = safe_float(funding.get("funding_rate_pct"))

                flags: List[str] = []
                if ratio >= 2.5:
                    flags.append(f"Büyük hesaplar aşırı long tarafında yığılmış (oran {ratio:.2f}) - long squeeze riski")
                elif 0 < ratio <= 0.4:
                    flags.append(f"Büyük hesaplar aşırı short tarafında yığılmış (oran {ratio:.2f}) - short squeeze riski")
                if funding_pct >= 0.05:
                    flags.append(f"Fonlama oranı aşırı pozitif (%{funding_pct:.3f}/8s) - kalabalık long, aşırı ısınma riski")
                elif funding_pct <= -0.05:
                    flags.append(f"Fonlama oranı aşırı negatif (%{funding_pct:.3f}/8s) - kalabalık short, sert yukarı sıçrama riski")
                if vol_stats:
                    vr = vol_stats.get("volume_ratio_vs_avg", 0)
                    chg = abs(vol_stats.get("last_day_change_pct", 0))
                    if vr >= 3.0 and chg < 1.5:
                        flags.append(
                            f"Hacim ortalamanın {vr:.1f} katına fırladı ama fiyat neredeyse yerinde saydı "
                            f"(%{chg:.1f}) - yapay/wash-trading hacmi şüphesi"
                        )
                    elif vr < 0.3 and chg >= 4.0:
                        flags.append(
                            f"Çok düşük hacimle (ort.'nın %{vr*100:.0f}'i) sert fiyat hareketi (%{chg:.1f}) "
                            "- ince likidite, manipülasyona açık"
                        )

                status = "MANİPÜLASYON RİSKİ / AŞIRI POZİSYONLANMA" if flags else "NORMAL"
                results.append({
                    "symbol": sym,
                    "long_short_ratio": ratio,
                    "long_account_pct": whale.get("long_account_pct"),
                    "short_account_pct": whale.get("short_account_pct"),
                    "funding_rate_pct": funding_pct,
                    "volume_ratio_vs_avg": vol_stats.get("volume_ratio_vs_avg") if vol_stats else None,
                    "last_day_change_pct": vol_stats.get("last_day_change_pct") if vol_stats else None,
                    "status": status,
                    "flags": flags,
                })
            except Exception:
                continue
        return results

    def _fetch_stocks():
        import yfinance as yf

        symbols = sorted(set(_parse_symbol_list(_IBKR_WATCHLIST_DEFAULT)) | {
            "AAPL", "MSFT", "NVDA", "AMD", "TSLA", "F", "T", "GOOGL", "AMZN", "META",
        })
        results: List[Dict[str, Any]] = []
        for sym in symbols:
            try:
                info = yf.Ticker(sym).info or {}
                short_pct_float = safe_float(info.get("shortPercentOfFloat")) * 100.0
                short_ratio_days = safe_float(info.get("shortRatio"))
                institutional_pct = safe_float(info.get("heldPercentInstitutions")) * 100.0
                insider_pct = safe_float(info.get("heldPercentInsiders")) * 100.0
                if short_pct_float <= 0 and institutional_pct <= 0:
                    continue

                flags: List[str] = []
                if short_pct_float >= 20:
                    flags.append(f"Halka açık payın %{short_pct_float:.1f}'i açığa satılmış - aşırı short yığılması")
                if short_ratio_days >= 8:
                    flags.append(f"Kısa pozisyonları kapatmak {short_ratio_days:.1f} gün sürer - short squeeze potansiyeli yüksek")
                if institutional_pct > 0 and institutional_pct < 20:
                    flags.append(f"Kurumsal sahiplik düşük (%{institutional_pct:.1f}) - spekülatif/perakende ağırlıklı hareket riski")

                status = "AŞIRI SHORT POZİSYONLANMA / SQUEEZE RİSKİ" if (short_pct_float >= 20 or short_ratio_days >= 8) else "NORMAL"
                results.append({
                    "symbol": sym,
                    "short_percent_of_float_pct": round(short_pct_float, 2),
                    "short_ratio_days_to_cover": round(short_ratio_days, 2) if short_ratio_days else None,
                    "institutional_ownership_pct": round(institutional_pct, 2) if institutional_pct else None,
                    "insider_ownership_pct": round(insider_pct, 2) if insider_pct else None,
                    "status": status,
                    "flags": flags,
                })
            except Exception:
                continue
        return results

    def _fetch():
        crypto = _fetch_crypto()
        stocks = _cache_get_or_fetch("stock_positioning_raw", 21600, _fetch_stocks)
        alerts = [r for r in crypto if r["status"] != "NORMAL"] + [r for r in stocks if r["status"] != "NORMAL"]
        return {
            "crypto_positioning": crypto,
            "stock_positioning": stocks,
            "alert_count": len(alerts),
            "alert_symbols": [a["symbol"] for a in alerts],
            "note": (
                "Bu analiz kesin manipülasyon kanıtı değildir; aşırı pozisyonlanma, yüksek short "
                "interest ve hacim/fiyat uyumsuzluğu gibi istatistiksel uyarı işaretlerini gösterir. "
                "Squeeze riskleri her iki yönde de sert ve ani fiyat hareketlerine yol açabilir."
            ),
            "time": now_text(),
        }

    return _cache_get_or_fetch("market_positioning_manipulation", 300, _fetch)


_SECTOR_SCENARIO_PLAYBOOK: List[Dict[str, Any]] = [
    {
        "id": "chip_shortage",
        "title": "Yarı İletken (Çip) Arz Sıkıntısı",
        "trigger_key": "SMH",
        "trigger_direction": "up",
        "trigger_threshold": 8.0,
        "narrative": (
            "Yarı iletken sektöründe arz sıkıntısı/talep patlaması olduğunda: (1) Çip ÜRETİCİLERİ "
            "(NVDA, AMD, TSM gibi) fiyatlama gücü kazanır, marjları genişler -> OLUMLU. "
            "(2) Çip KULLANAN teknoloji donanım/otomotiv üreticileri girdi maliyeti artışı ve üretim "
            "gecikmesi yaşar, kâr marjı baskılanır -> OLUMSUZ. (3) Otomotiv sektörü üretim durmalarına "
            "kadar gidebilecek şekilde en çok etkilenen taraftır. (4) Orta vadede yüksek kâr, rakiplerin "
            "yatırımını (yeni fabrika/kapasite) teşvik eder ve sıkıntı 12-24 ay içinde hafifler."
        ),
        "affected": [
            {"sector": "Yarı iletken üreticileri (SMH, NVDA, AMD)", "impact": "OLUMLU", "reason": "Fiyatlama gücü ve marj genişlemesi"},
            {"sector": "Teknoloji donanım/tüketici elektroniği", "impact": "OLUMSUZ", "reason": "Girdi maliyeti artışı, üretim gecikmesi"},
            {"sector": "Otomotiv", "impact": "OLUMSUZ", "reason": "Çipsiz üretim durabilir"},
        ],
    },
    {
        "id": "war_geopolitical",
        "title": "Savaş / Jeopolitik Kriz",
        "trigger_key": "XLE",
        "trigger_direction": "up",
        "trigger_threshold": 8.0,
        "narrative": (
            "Savaş veya büyük jeopolitik kriz durumunda tipik zincirleme etki: (1) Enerji fiyatları "
            "(petrol/doğalgaz) sıçrar -> enerji sektörü OLUMLU. (2) Savunma sanayi siparişleri artar -> "
            "OLUMLU. (3) Gıda/tarım tedarik zinciri kesintiye uğrarsa (özellikle tahıl/gübre ihracatçısı "
            "bölgeler etkilenirse) gıda fiyatları yükselir, gıda sektörü kârlılığı karışık (maliyet artışı "
            "vs fiyatlama gücü). (4) Altın güvenli liman talebiyle yükselir -> OLUMLU. (5) Havayolları/"
            "turizm yakıt maliyeti + talep düşüşüyle OLUMSUZ etkilenir. (6) Genel borsa risk-off modda "
            "baskı altında kalır, VIX yükselir."
        ),
        "affected": [
            {"sector": "Enerji (XLE)", "impact": "OLUMLU", "reason": "Petrol/doğalgaz fiyat şoku"},
            {"sector": "Savunma Sanayi (ITA)", "impact": "OLUMLU", "reason": "Askeri harcama artışı"},
            {"sector": "Altın", "impact": "OLUMLU", "reason": "Güvenli liman talebi"},
            {"sector": "Gıda/Temel Tüketim (XLP)", "impact": "KARIŞIK", "reason": "Maliyet artışı vs fiyatlama gücü"},
            {"sector": "Havayolları/Turizm", "impact": "OLUMSUZ", "reason": "Yakıt maliyeti ve talep düşüşü"},
            {"sector": "Genel Borsa (SPX)", "impact": "OLUMSUZ", "reason": "Risk-off, VIX yükselişi"},
        ],
    },
    {
        "id": "rate_hike",
        "title": "Faiz Artışı / Sıkı Para Politikası",
        "trigger_key": "XLF",
        "trigger_direction": "up",
        "trigger_threshold": 6.0,
        "narrative": (
            "Merkez bankaları faiz artırdığında: (1) Teknoloji/büyüme hisseleri iskonto oranı artışıyla "
            "OLUMSUZ etkilenir (gelecekteki nakit akışları bugüne daha düşük değerle iner). (2) Bankacılık/"
            "finans sektörü net faiz marjı avantajıyla kısa vadede OLUMLU olabilir. (3) Emlak/REIT kredi "
            "maliyeti artışıyla OLUMSUZ. (4) Altın, faizli enstrümanlara karşı fırsat maliyeti arttığı için "
            "baskı altında kalır. (5) Dolar (DXY) genelde güçlenir."
        ),
        "affected": [
            {"sector": "Teknoloji (XLK)", "impact": "OLUMSUZ", "reason": "İskonto oranı artışı, büyüme hisseleri baskılanır"},
            {"sector": "Finans (XLF)", "impact": "OLUMLU", "reason": "Net faiz marjı genişlemesi"},
            {"sector": "Emlak/REIT", "impact": "OLUMSUZ", "reason": "Kredi maliyeti artışı"},
            {"sector": "Altın", "impact": "OLUMSUZ", "reason": "Fırsat maliyeti artışı"},
        ],
    },
    {
        "id": "dollar_strength",
        "title": "Dolar Endeksi (DXY) Güçlenmesi",
        "trigger_key": "DXY",
        "trigger_direction": "up",
        "trigger_threshold": 2.0,
        "narrative": (
            "Dolar güçlendiğinde: (1) Emtia (altın, petrol - dolar bazlı fiyatlanır) baskı altında kalır. "
            "(2) Gelişen piyasalar ve gelişen piyasa para birimleri (TRY dahil) OLUMSUZ etkilenir, dış borç "
            "servisi ağırlaşır. (3) ABD çok uluslu şirketlerinin (Apple, Microsoft gibi) yurt dışı geliri "
            "kur çevirisinde küçülür -> hafif OLUMSUZ. (4) Kripto paralar genelde dolar likiditesi daraldığı "
            "için baskı altında kalır."
        ),
        "affected": [
            {"sector": "Altın/Emtia", "impact": "OLUMSUZ", "reason": "Dolar bazlı fiyatlama baskısı"},
            {"sector": "Gelişen Piyasalar / TRY", "impact": "OLUMSUZ", "reason": "Dış borç servisi ağırlaşır"},
            {"sector": "ABD Çok Uluslu Şirketleri", "impact": "HAFİF OLUMSUZ", "reason": "Kur çevirisi kaybı"},
            {"sector": "Kripto (BTC)", "impact": "OLUMSUZ", "reason": "Dolar likiditesi daralması"},
        ],
    },
    {
        "id": "energy_crash",
        "title": "Enerji Fiyatlarında Sert Düşüş",
        "trigger_key": "XLE",
        "trigger_direction": "down",
        "trigger_threshold": -8.0,
        "narrative": (
            "Petrol/enerji fiyatları sert düştüğünde: (1) Enerji sektörü kârlılığı daralır -> OLUMSUZ. "
            "(2) Havayolları/nakliye/lojistik girdi maliyeti düştüğü için OLUMLU. (3) Tüketici harcanabilir "
            "geliri artar -> perakende/tüketici sektörü hafif OLUMLU. (4) Enflasyon baskısı azalır, bu da "
            "merkez bankalarının gevşeme ihtimalini artırır -> teknoloji/büyüme hisseleri OLUMLU etkilenebilir."
        ),
        "affected": [
            {"sector": "Enerji (XLE)", "impact": "OLUMSUZ", "reason": "Kârlılık daralması"},
            {"sector": "Havayolları/Nakliye", "impact": "OLUMLU", "reason": "Yakıt maliyeti düşüşü"},
            {"sector": "Teknoloji (XLK)", "impact": "OLUMLU", "reason": "Enflasyon baskısı azalması, gevşeme ihtimali"},
        ],
    },
    {
        "id": "ai_investment_boom",
        "title": "Yapay Zeka (AI) Yatırım Patlaması",
        "trigger_key": "SMH",
        "trigger_direction": "up",
        "trigger_threshold": 18.0,
        "narrative": (
            "Yapay zeka altyapısına dev yatırımlar hızlandığında: (1) Yarı iletken/çip üreticileri "
            "(NVDA, AMD, TSM) talep patlamasıyla OLUMLU etkilenir. (2) Bulut/hiper-ölçek teknoloji "
            "şirketleri (veri merkezi yatırımı yapanlar) hem yatırımcı ilgisi hem uzun vadeli verimlilik "
            "kazancıyla OLUMLU. (3) Veri merkezlerinin devasa elektrik tüketimi enerji/elektrik "
            "üreticilerine (özellikle nükleer ve doğalgaz) ek talep getirir -> OLUMLU. (4) Kısa vadede "
            "aşırı sermaye harcaması (capex) nedeniyle bu şirketlerin serbest nakit akışı baskılanabilir "
            "-> KARIŞIK. (5) Balon riski: değerlemeler hızla gerçek kazanç büyümesinin önüne geçerse "
            "sert bir düzeltme riski oluşur."
        ),
        "affected": [
            {"sector": "Yarı iletken (SMH, NVDA)", "impact": "OLUMLU", "reason": "Talep patlaması"},
            {"sector": "Bulut/Büyük Teknoloji", "impact": "OLUMLU", "reason": "Uzun vadeli verimlilik, yatırımcı ilgisi"},
            {"sector": "Enerji/Elektrik Üretimi", "impact": "OLUMLU", "reason": "Veri merkezi elektrik talebi"},
            {"sector": "Genel Teknoloji Değerlemesi", "impact": "KARIŞIK", "reason": "Aşırı capex, balon riski"},
        ],
    },
    {
        "id": "recession_yield_curve",
        "title": "Resesyon Riski / Getiri Eğrisi Tersine Dönmesi",
        "trigger_key": "XLF",
        "trigger_direction": "down",
        "trigger_threshold": -8.0,
        "narrative": (
            "Resesyon sinyalleri güçlendiğinde (getiri eğrisi tersine döndüğünde veya finans "
            "sektörü sert düştüğünde): (1) Döngüsel sektörler (finans, tüketici isteğe bağlı, "
            "sanayi) kredi büyümesi yavaşlaması ve tüketici harcamalarının azalmasıyla OLUMSUZ "
            "etkilenir. (2) Savunmacı sektörler (sağlık, gıda/temel tüketim, kamu hizmetleri) "
            "talebin daha istikrarlı olması nedeniyle görece OLUMLU/dayanıklı kalır. (3) Devlet "
            "tahvilleri faiz indirimi beklentisiyle değer kazanır. (4) Altın güvenli liman "
            "talebiyle OLUMLU olabilir."
        ),
        "affected": [
            {"sector": "Finans (XLF)", "impact": "OLUMSUZ", "reason": "Kredi büyümesi yavaşlaması"},
            {"sector": "Tüketici İsteğe Bağlı (XLY)", "impact": "OLUMSUZ", "reason": "Harcama daralması"},
            {"sector": "Sağlık (XLV) / Gıda (XLP)", "impact": "OLUMLU", "reason": "Savunmacı, istikrarlı talep"},
            {"sector": "Altın", "impact": "OLUMLU", "reason": "Güvenli liman talebi"},
        ],
    },
    {
        "id": "agri_supply_shock",
        "title": "Kuraklık / Tarımsal Arz Şoku",
        "trigger_key": "XLP",
        "trigger_direction": "up",
        "trigger_threshold": 9.0,
        "narrative": (
            "Büyük tarım bölgelerinde kuraklık/kötü hasat veya ihracat kısıtlaması olduğunda: "
            "(1) Gıda fiyatları küresel çapta yükselir; gıda ÜRETİCİLERİ (marka gücü olanlar) "
            "fiyat artışını tüketiciye yansıtabiliyorsa OLUMLU, yansıtamıyorsa (rekabetin yoğun "
            "olduğu segmentler) OLUMSUZ -> KARIŞIK. (2) Tarım girdisi/gübre üreticileri talep "
            "artışıyla OLUMLU. (3) Perakende/restoran zincirleri girdi maliyeti artışıyla OLUMSUZ. "
            "(4) Gelişmekte olan, gıda ithalatına bağımlı ülkelerde enflasyon baskısı ve sosyal "
            "huzursuzluk riski artar."
        ),
        "affected": [
            {"sector": "Gıda/Temel Tüketim (XLP)", "impact": "KARIŞIK", "reason": "Fiyat yansıtma gücüne bağlı"},
            {"sector": "Tarım Girdisi/Gübre Üreticileri", "impact": "OLUMLU", "reason": "Talep artışı"},
            {"sector": "Perakende/Restoran", "impact": "OLUMSUZ", "reason": "Girdi maliyeti artışı"},
        ],
    },
    {
        "id": "crypto_regulation_crackdown",
        "title": "Kripto Para Düzenleme Sıkılaştırması",
        "trigger_key": "BTC",
        "trigger_direction": "down",
        "trigger_threshold": -18.0,
        "narrative": (
            "Büyük ekonomilerde kripto para düzenlemesi sertleştiğinde (borsa yasakları, "
            "vergi/KYC sıkılaştırması gibi): (1) Kripto piyasası (BTC, ETH ve altcoinler) "
            "likidite çekilmesi ve kurumsal tereddütle OLUMSUZ etkilenir, volatilite artar. "
            "(2) Geleneksel finans/borsa altyapısı şirketleri (düzenlenmiş borsalar, saklama "
            "hizmetleri) uzun vadede kurumsal güven artışıyla OLUMLU olabilir. (3) Madencilik "
            "şirketleri düzenleme + fiyat düşüşü kombinasyonuyla OLUMSUZ etkilenir."
        ),
        "affected": [
            {"sector": "Kripto (BTC/ETH/Altcoin)", "impact": "OLUMSUZ", "reason": "Likidite çekilmesi, kurumsal tereddüt"},
            {"sector": "Düzenlenmiş Borsa/Saklama Hizmetleri", "impact": "OLUMLU", "reason": "Uzun vadeli kurumsal güven"},
            {"sector": "Kripto Madenciliği", "impact": "OLUMSUZ", "reason": "Düzenleme + fiyat düşüşü"},
        ],
    },
    {
        "id": "pandemic_lockdown",
        "title": "Pandemi / Küresel Karantina Riski",
        "trigger_key": "XLV",
        "trigger_direction": "up",
        "trigger_threshold": 12.0,
        "narrative": (
            "Küresel bir salgın/karantina senaryosunda: (1) Sağlık/ilaç ve biyoteknoloji "
            "sektörü aşı/tedavi talebiyle OLUMLU etkilenir. (2) E-ticaret, bulut/uzaktan çalışma "
            "teknolojileri ve kargo/lojistik talep patlamasıyla OLUMLU. (3) Havayolları, turizm, "
            "perakende mağazacılık, restoran/eğlence sektörü talep çöküşüyle sert OLUMSUZ etkilenir. "
            "(4) Enerji talebi (ulaşımın durmasıyla) düşer -> OLUMSUZ. (5) Merkez bankaları genelde "
            "agresif parasal genişlemeye gider, bu da orta vadede risk varlıklarını (borsa, kripto) "
            "destekler."
        ),
        "affected": [
            {"sector": "Sağlık/İlaç (XLV)", "impact": "OLUMLU", "reason": "Aşı/tedavi talebi"},
            {"sector": "E-ticaret/Bulut Teknoloji", "impact": "OLUMLU", "reason": "Uzaktan çalışma/alışveriş talebi"},
            {"sector": "Havayolları/Turizm/Perakende", "impact": "OLUMSUZ", "reason": "Talep çöküşü"},
            {"sector": "Enerji (XLE)", "impact": "OLUMSUZ", "reason": "Ulaşım talebi düşüşü"},
        ],
    },
]


# Kullanicinin serbest metin senaryo sorusunu (dd AI analizi) yukaridaki playbook
# senaryolariyla eslestirmek icin anahtar kelime haritasi.
_SCENARIO_KEYWORDS: Dict[str, List[str]] = {
    "chip_shortage": ["çip", "cip", "yarı iletken", "yari iletken", "semiconductor", "nvidia", "amd", "tsm"],
    "war_geopolitical": ["savaş", "savas", "jeopolitik", "çatışma", "catisma", "kriz", "gerginlik", "işgal", "isgal"],
    "rate_hike": ["faiz", "fed", "merkez bankası", "merkez bankasi", "sıkı para", "siki para", "powell"],
    "dollar_strength": ["dolar", "dxy", "dolar endeksi"],
    "energy_crash": ["petrol", "enerji", "opec", "brent", "wti", "doğalgaz", "dogalgaz"],
    "ai_investment_boom": ["yapay zeka", "ai yatırım", "ai yatirim", "nvidia", "veri merkezi", "gpu"],
    "recession_yield_curve": ["resesyon", "durgunluk", "getiri eğrisi", "getiri egrisi", "tahvil", "işsizlik", "issizlik"],
    "agri_supply_shock": ["tarım", "tarim", "gıda", "gida", "buğday", "bugday", "kuraklık", "kuraklik", "hasat"],
    "crypto_regulation_crackdown": ["kripto regülasyon", "kripto regulasyon", "sec", "yasak", "düzenleme", "duzenleme", "kripto yasağı", "kripto yasagi"],
    "pandemic_lockdown": ["pandemi", "salgın", "salgin", "karantina", "lockdown", "virüs", "virus"],
}


def analyze_user_scenario(scenario_text: str) -> Dict[str, Any]:
    """Kullanicinin dd AI analizi ekranina yazdigi serbest metin senaryoyu
    (ornegin 'Fed faiz indirirse BTC, altin ve Nasdaq nasil etkilenir?') analiz
    eder. Onceden sabit/hardcoded bir metin donduruluyordu; artik metindeki
    anahtar kelimeler _SECTOR_SCENARIO_PLAYBOOK ile eslestirilip, eslesen
    senaryolarin GERCEK guncel piyasa verisiyle hesaplanmis AKTIF/IZLENIYOR
    durumu ve anlatimi kullanilarak, ayrica genel makro arka planla (VIX,
    coküş riski, Korku/Acgozluluk endeksi) birlikte kisisellestirilmis bir
    Turkce yanit uretilir."""
    text_lower = (scenario_text or "").lower()

    matched_ids: List[str] = []
    for scenario_id, keywords in _SCENARIO_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched_ids.append(scenario_id)

    try:
        sector_data = get_sector_scenario_analysis()
        scenarios_by_id = {s["id"]: s for s in sector_data.get("scenarios", [])}
    except Exception:
        scenarios_by_id = {}

    try:
        valuation = get_valuation_bubble_analysis()
    except Exception:
        valuation = {}

    crash_level = valuation.get("crash_risk_level", "BİLİNMİYOR")
    vix = safe_float(valuation.get("vix"))
    fear_greed = safe_float(valuation.get("fear_greed_index"))
    overheat_count = valuation.get("overheat_count", 0)

    macro_backdrop = (
        f"Güncel makro arka plan: VIX {vix:.1f}, Korku/Açgözlülük Endeksi {fear_greed:.0f}, "
        f"genel çöküş riski '{crash_level}', {overheat_count} varlık/sektörde aşırı ısınma belirtisi var."
    )

    matched_blocks: List[str] = []
    for sid in matched_ids:
        s = scenarios_by_id.get(sid)
        if not s:
            continue
        sector_lines = "\n".join(
            f"   - {a['sector']}: {a['impact']} ({a['reason']})" for a in s.get("affected_sectors", [])
        )
        matched_blocks.append(
            f"📌 {s['title']} [{s['status']}]\n{s['narrative']}\n{sector_lines}"
        )

    if matched_blocks:
        result_text = (
            "dd Senaryo Analizi (sorunuzla ilişkili gerçek zamanlı senaryolar bulundu):\n\n"
            + "\n\n".join(matched_blocks)
            + "\n\n"
            + macro_backdrop
            + "\n\nSonuç: Yukarıdaki senaryo(lar) şu an piyasada ölçülen gerçek veriye göre "
            + ("AKTİF durumda - yani fiilen yaşanıyor olabilir." if any(scenarios_by_id.get(i, {}).get("status") == "AKTİF" for i in matched_ids) else "henüz tetiklenmemiş, izleniyor.")
            + " İşlem açmadan önce güven skoru, kaldıraç ve hedge ihtiyacını ayrıca değerlendirin."
        )
    else:
        result_text = (
            "dd Senaryo Analizi (girdiğiniz metinde tanımlı bir senaryo şablonuyla doğrudan eşleşme bulunamadı, "
            "genel güncel piyasa verisiyle değerlendirme yapıldı):\n\n"
            + macro_backdrop
            + "\n\nGenel değerlendirme:\n"
            + ("• Risk-off/temkinli ortam: VIX yüksek, kaldıraç ve pozisyon büyüklüğü azaltılmalı.\n" if vix > 22 else "• Risk ortamı görece sakin (VIX normal seviyede).\n")
            + ("• Aşırı ısınma/balon riski geniş tabanlı, yeni pozisyonlarda temkinli olunmalı.\n" if overheat_count >= 4 else "")
            + "• Senaryonuzu daha spesifik anahtar kelimelerle (faiz, savaş, dolar, petrol, çip, resesyon, kripto regülasyon, pandemi, yapay zeka, tarım/gıda) yazarsanız ilgili gerçek zamanlı sektör etkisini de gösterebilirim."
        )

    return {
        "ok": True,
        "scenario_text": scenario_text,
        "matched_scenarios": matched_ids,
        "result_text": result_text,
        "crash_risk_level": crash_level,
        "vix": vix,
        "fear_greed_index": fear_greed,
        "time": now_text(),
    }


def get_sector_scenario_analysis() -> Dict[str, Any]:
    """Sektorler arasi neden-sonuc senaryo motoru: onceden tanimlanmis (yari
    iletken arz sikintisi, savas/jeopolitik kriz, faiz artisi, dolar guclenmesi,
    enerji cokusu gibi) senaryolarin gercek sektor ETF verisiyle (son 1 aylik
    degisim - get_valuation_bubble_analysis) su an 'AKTIF' mi yoksa sadece
    'IZLENIYOR' (henuz tetiklenmemis, bilgi amacli) durumda mi oldugunu belirler
    ve her senaryo icin hangi sektorun nasil etkilenecegini (OLUMLU/OLUMSUZ/KARISIK)
    Turkce anlatimla dondurur."""
    def _fetch():
        try:
            valuation = get_valuation_bubble_analysis()
            assets_by_key = {a["key"]: a for a in valuation.get("assets", [])}
        except Exception:
            assets_by_key = {}

        dxy_change_1m = 0.0
        try:
            dxy_ticker = try_yahoo_ticker("DXY")
            dxy_change_1m = safe_float((dxy_ticker or {}).get("change_24h"))
        except Exception:
            pass

        scenarios_out: List[Dict[str, Any]] = []
        for scenario in _SECTOR_SCENARIO_PLAYBOOK:
            trigger_key = scenario["trigger_key"]
            if trigger_key == "DXY":
                measured_change = dxy_change_1m
            else:
                asset = assets_by_key.get(trigger_key)
                measured_change = safe_float(asset.get("last_month_change_pct")) if asset else 0.0

            threshold = scenario["trigger_threshold"]
            direction = scenario["trigger_direction"]
            is_active = (measured_change >= threshold) if direction == "up" else (measured_change <= threshold)

            scenarios_out.append({
                "id": scenario["id"],
                "title": scenario["title"],
                "status": "AKTİF" if is_active else "İZLENİYOR",
                "trigger_sector": trigger_key,
                "measured_change_pct": round(measured_change, 2),
                "trigger_threshold_pct": threshold,
                "narrative": scenario["narrative"],
                "affected_sectors": scenario["affected"],
            })

        active_scenarios = [s for s in scenarios_out if s["status"] == "AKTİF"]
        return {
            "scenarios": scenarios_out,
            "active_count": len(active_scenarios),
            "active_scenario_titles": [s["title"] for s in active_scenarios],
            "note": (
                "Bu senaryolar tarihsel/ekonomik ilişkilere dayanan genel çerçevelerdir; kesin "
                "öngörü değildir. 'AKTİF' etiketi, ilgili sektörün son 1 aylık gerçek hareketinin "
                "senaryo eşiğini geçtiğini gösterir - yani senaryo şu an piyasada fiilen yaşanıyor "
                "olabilir. 'İZLENİYOR' etiketi henüz tetiklenmediği ama bilgi amaçlı takip edildiği anlamına gelir."
            ),
            "time": now_text(),
        }

    return _cache_get_or_fetch("sector_scenario_analysis", 21600, _fetch)


def get_daily_investment_advice() -> Dict[str, Any]:
    """'Bugün neye yatırım yapmalı / dikkat etmeli' - günlük kısa yatırım notu.
    Tüm profesyonel analiz motorlarının (balon/çöküş riski, defter değeri,
    bilanço/nakit akış sağlığı, short/long pozisyonlanma-manipülasyon, sektör
    senaryoları) özetini periyodik olarak (günde 1 kez, gün içinde değişmez)
    tarayıp kısa, aksiyona dönük bir Türkçe not üretir."""

    def _fetch() -> Dict[str, Any]:
        try:
            valuation = get_valuation_bubble_analysis()
        except Exception:
            valuation = {}
        try:
            book_value = get_fundamental_valuation_analysis()
        except Exception:
            book_value = {"overpriced_count": 0, "overpriced_symbols": []}
        try:
            financials = get_financial_statement_analysis()
        except Exception:
            financials = {"risky_count": 0, "risky_symbols": []}
        try:
            positioning = get_market_positioning_and_manipulation_analysis()
        except Exception:
            positioning = {"alert_count": 0, "alert_symbols": []}
        try:
            sector = get_sector_scenario_analysis()
        except Exception:
            sector = {"active_count": 0, "active_scenario_titles": []}

        crash_level = valuation.get("crash_risk_level", "BİLİNMİYOR")
        overheat_count = valuation.get("overheat_count", 0)
        assets = valuation.get("assets", [])
        cheapest = sorted(
            [a for a in assets if safe_float(a.get("z_score")) < -0.3],
            key=lambda a: safe_float(a.get("z_score")),
        )
        hottest = sorted(
            [a for a in assets if safe_float(a.get("overheat_score")) >= 2],
            key=lambda a: -safe_float(a.get("overheat_score")),
        )

        notes: List[str] = []

        if crash_level == "YÜKSEK":
            notes.append("⚠️ Genel piyasa çöküş riski YÜKSEK görünüyor - yeni pozisyonlarda kaldıraç ve boyut küçültülmeli, nakit payı artırılabilir.")
        elif crash_level == "ORTA":
            notes.append("🟡 Genel piyasa çöküş riski ORTA seviyede - temkinli iyimserlik uygun, sıkı stop-loss kullanılmalı.")
        else:
            notes.append("🟢 Genel piyasa çöküş riski şu an DÜŞÜK - fırsat taraması için görece uygun bir ortam.")

        if hottest:
            top = hottest[0]
            notes.append(f"🔥 En çok ısınmış varlık: {top.get('name')} ({top.get('status')}) - yeni alım için acele edilmemeli, kâr realizasyonu düşünülebilir.")

        if cheapest:
            top = cheapest[0]
            notes.append(f"💡 Görece ucuz/soğuk kalmış varlık: {top.get('name')} (z-skor {safe_float(top.get('z_score')):+.2f}) - araştırma için aday olabilir.")

        if book_value.get("overpriced_count", 0) > 0:
            syms = ", ".join(book_value.get("overpriced_symbols", [])[:5])
            notes.append(f"📊 Defter değerine göre pahalı hisseler: {syms} - yeni pozisyon açmadan önce büyüme gerekçesi sorgulanmalı.")

        if financials.get("risky_count", 0) > 0:
            syms = ", ".join(financials.get("risky_symbols", [])[:5])
            notes.append(f"📉 Bilanço/nakit akışında risk bayrağı olan şirketler: {syms} - pozisyon büyüklüğü sınırlı tutulmalı.")

        if positioning.get("alert_count", 0) > 0:
            syms = ", ".join(positioning.get("alert_symbols", [])[:5])
            notes.append(f"🚨 Manipülasyon/olağandışı pozisyonlanma uyarısı olan semboller: {syms} - işlem öncesi ekstra dikkat.")

        active_titles = sector.get("active_scenario_titles", [])
        if active_titles:
            notes.append(f"🌐 Şu an aktif sektör senaryosu: {', '.join(active_titles)} - ilgili sektörlerdeki pozisyonlar gözden geçirilmeli.")

        if overheat_count >= 5:
            notes.append("📌 Geniş tabanlı ısınma var (5+ varlık/sektör) - portföy genelinde risk azaltma düşünülebilir.")

        summary = " ".join(notes[:3]) if notes else "Bugün için özel bir uyarı yok, standart risk yönetimiyle devam edilebilir."

        return {
            "ok": True,
            "date": now_text().split(" ")[0],
            "crash_risk_level": crash_level,
            "summary": summary,
            "notes": notes,
            "disclaimer": "Bu bir yatırım tavsiyesi değildir; istatistiksel/kural tabanlı bir özet niteliğindedir. Kendi araştırmanızı yapın.",
            "time": now_text(),
        }

    return _cache_get_or_fetch("daily_investment_advice", 86400, _fetch)


def build_dd_ai_dashboard() -> Dict[str, Any]:
    macro_raw = get_macro_dashboard_raw()
    regime_info = get_macro_regime()

    def _fmt(key: str, prefix: str = "", decimals: int = 2) -> str:
        t = macro_raw.get(key)
        if not t or safe_float(t.get("price")) <= 0:
            return "-"
        val = safe_float(t.get("price"))
        return f"{prefix}{val:,.{decimals}f}"

    vix_val = safe_float((macro_raw.get("VIX") or {}).get("price"))
    regime = regime_info.get("regime", "NEUTRAL") if isinstance(regime_info, dict) else "NEUTRAL"

    if vix_val > 0:
        if vix_val >= 25:
            risk_appetite = "Düşük (Korku)"
        elif vix_val <= 15:
            risk_appetite = "Yüksek (Rahat)"
        else:
            risk_appetite = "Normal"
    else:
        risk_appetite = "-"

    general_mode = {"RISK_ON": "Risk İştahı Açık", "RISK_OFF": "Risk Kaçışı", "NEUTRAL": "Normal"}.get(regime, "Normal")
    ai_confidence = 50
    if regime == "RISK_ON":
        ai_confidence = 65
    elif regime == "RISK_OFF":
        ai_confidence = 35

    institutional_scores: Dict[str, Any] = {}
    for sym in ["BTCUSDT", "ETHUSDT"]:
        try:
            whale = get_whale_positioning(sym)
            ratio = safe_float(whale.get("long_short_ratio", 1.0)) if isinstance(whale, dict) else 1.0
            score = max(0, min(100, int(round((ratio / (ratio + 1.0)) * 100.0)))) if ratio > 0 else 50
            trend = "LONG ağırlıklı" if ratio > 1.1 else ("SHORT ağırlıklı" if ratio < 0.9 else "Dengeli")
            institutional_scores[sym.replace("USDT", "")] = {"score": score, "trend": trend}
        except Exception:
            institutional_scores[sym.replace("USDT", "")] = {"score": 50, "trend": "Veri bekleniyor"}

    learning_rates: Dict[str, Any] = {}
    for side in ["BUY", "SELL"]:
        stats = LEARNING_STATS.get(side, {"wins": 0, "losses": 0})
        total = int(stats.get("wins", 0)) + int(stats.get("losses", 0))
        win_rate = (int(stats.get("wins", 0)) / total) if total > 0 else 0.5
        learning_rates[side] = {"win_rate": round(win_rate, 4)}

    last_decision = {"symbol": "-", "action": "-", "confidence": 0, "reason": "Backend verisi bekleniyor."}
    try:
        sig = calculate_ai_signal("ETHUSDT", "FUTURES")
        last_decision = {
            "symbol": "ETHUSDT",
            "action": str(sig.get("signal", "WAIT")),
            "confidence": int(safe_float(sig.get("confidence", 0))),
            "reason": "; ".join(sig.get("reasons", [])) or "Belirgin bir sinyal yok, izleniyor.",
        }
    except Exception:
        pass

    return {
        "updated_at": now_text(),
        "ai_confidence": ai_confidence,
        "market_regime": general_mode,
        "macro": {
            "vix": _fmt("VIX"),
            "nasdaq": _fmt("NASDAQ", decimals=0),
            "sp500": _fmt("SP500", decimals=0),
            "dxy": _fmt("DXY"),
            "gold": _fmt("GOLD", prefix="$"),
            "oil": _fmt("OIL", prefix="$"),
        },
        "market_mood": {
            "general_mode": general_mode,
            "risk_appetite": risk_appetite,
            "institutional_flow": "Kurumsal veri: BTC/ETH top-trader pozisyonlama.",
            "bubble_risk": "Yüksek" if vix_val > 0 and vix_val < 13 else "Normal",
        },
        "institutional_scores": institutional_scores,
        "learning_rates": learning_rates,
        "last_decision": last_decision,
    }


def build_market_flow_risk() -> Dict[str, Any]:
    macro_raw = get_macro_dashboard_raw()
    regime_info = get_macro_regime()
    regime = regime_info.get("regime", "NEUTRAL") if isinstance(regime_info, dict) else "NEUTRAL"
    vix_val = safe_float((macro_raw.get("VIX") or {}).get("price"))
    risk_score = 50
    if regime == "RISK_ON":
        risk_score = 30
    elif regime == "RISK_OFF":
        risk_score = 75
    if vix_val >= 25:
        risk_score = max(risk_score, 70)

    def _flow_item(key: str, unit: str = "M$") -> Dict[str, Any]:
        t = macro_raw.get(key)
        if not t:
            return {"value": f"0 {unit}", "raw": 0.0, "status": "-"}
        change = safe_float(t.get("change_24h"))
        volume = safe_float(t.get("quote_volume"))
        raw_m = round(volume / 1_000_000.0, 2) if volume > 0 else round(change * 10.0, 2)
        status = "Giriş" if change >= 0 else "Çıkış"
        sign = "+" if raw_m >= 0 else ""
        return {"value": f"{sign}{raw_m} {unit}", "raw": raw_m, "status": status}

    crypto_change = 0.0
    try:
        eth_snap = get_market_snapshot("ETHUSDT", "FUTURES")
        crypto_change = safe_float(eth_snap.get("change_24h"))
    except Exception:
        pass

    warning = "Piyasa normal seyrediyor."
    if regime == "RISK_OFF":
        warning = "Risk-off rejim: dolar güçlü, borsalar zayıf. Temkinli olun."
    elif regime == "RISK_ON":
        warning = "Risk-on rejim: risk iştahı yüksek."

    return {
        "ok": True,
        "updated_at": now_text(),
        "market_state": regime,
        "risk_score": int(risk_score),
        "warning": warning,
        "net_flows": {
            "crypto": {
                "value": f"{'+' if crypto_change >= 0 else ''}{round(crypto_change * 12, 1)} M$",
                "raw": round(crypto_change * 12, 1),
                "status": "Giriş" if crypto_change >= 0 else "Çıkış",
            },
            "stocks": _flow_item("SP500"),
            "commodities": _flow_item("GOLD"),
            "fx_bonds": _flow_item("DXY"),
        },
    }


def learning_bias(signal: str) -> int:
    side = signal.upper()
    if side not in ["BUY", "SELL"]:
        return 0
    stats = LEARNING_STATS.get(side, {"wins": 0, "losses": 0})
    total = int(stats["wins"]) + int(stats["losses"])
    if total < 5:
        return 0
    win_rate = stats["wins"] / total
    if win_rate >= 0.62:
        return 5
    if win_rate <= 0.42:
        return -6
    return 0


def queue_signal_for_learning(symbol: str, signal: str, price: float, window_sec: int) -> None:
    if signal not in ["BUY", "SELL"] or price <= 0:
        return
    SIGNAL_QUEUE.insert(
        0,
        {
            "symbol": normalize_symbol(symbol),
            "signal": signal,
            "entry_price": price,
            "entry_epoch": time.time(),
            "evaluate_after": max(60, window_sec),
        },
    )
    del SIGNAL_QUEUE[300:]


def resolve_learning(symbol: str, current_price: float) -> None:
    if current_price <= 0:
        return
    now_epoch = time.time()
    resolved: List[int] = []
    symbol2 = normalize_symbol(symbol)
    for idx, row in enumerate(SIGNAL_QUEUE):
        if row.get("symbol") != symbol2:
            continue
        if now_epoch - safe_float(row.get("entry_epoch")) < safe_float(row.get("evaluate_after"), 300):
            continue
        signal = str(row.get("signal", "WAIT")).upper()
        entry_price = safe_float(row.get("entry_price"))
        if entry_price <= 0 or signal not in ["BUY", "SELL"]:
            resolved.append(idx)
            continue
        success = (current_price > entry_price) if signal == "BUY" else (current_price < entry_price)
        key = "wins" if success else "losses"
        LEARNING_STATS.setdefault(signal, {"wins": 0, "losses": 0})[key] += 1
        resolved.append(idx)
    for idx in reversed(resolved):
        SIGNAL_QUEUE.pop(idx)


# ---------------------------------------------------------------------------
# Korelasyon / Lag / Hedge Motoru
# ---------------------------------------------------------------------------
# Watchlist'teki (Binance + IBKR) tum semboller icin fiyat gecmisi tutulur.
# Birbiriyle guclu korele olan iki varlikta biri hareket edip digeri henuz
# etmediyse ("lag"), henuz hareket etmeyen tarafta o yonde (veya negatif
# korelasyonda ters yonde) bir sinyal onerisi uretilir. Bu ayni zamanda
# "Piyasalar arasi analiz" ekraninin veri kaynagi olarak da kullanilir.
_CORR_PRICE_HISTORY: Dict[str, List[Tuple[float, float]]] = {}
_CORR_HISTORY_LOCK = threading.Lock()
_CORR_MAX_POINTS = 200
_CORR_MIN_POINTS = 12
_CORR_STRONG_THRESHOLD = 0.6
_CORR_LAG_MOVE_PCT = 1.2  # hareket eden varligin en az bu kadar (%) degismis olmasi gerekir
_CORR_FOLLOW_TOLERANCE_PCT = 0.4  # takip eden varlik bu kadardan az hareket ettiyse "henuz gelmedi" sayilir


def record_correlation_price(symbol: str, price: float) -> None:
    """Her sinyal degerlendirmesinde (Binance + IBKR) cagirilir; sembolun
    fiyat gecmisine bir nokta ekler. Korelasyon hesaplamasi bu geçmişe dayanir."""
    if price <= 0:
        return
    sym = normalize_symbol(symbol)
    now_epoch = time.time()
    with _CORR_HISTORY_LOCK:
        series = _CORR_PRICE_HISTORY.setdefault(sym, [])
        if series and now_epoch - series[-1][0] < 5:
            # Ayni 5 saniyelik pencerede tekrar tekrar eklenmesin (asiri sik ornekleme).
            return
        series.append((now_epoch, price))
        if len(series) > _CORR_MAX_POINTS:
            del series[: len(series) - _CORR_MAX_POINTS]


def _returns_series(points: List[Tuple[float, float]]) -> List[float]:
    rets: List[float] = []
    for i in range(1, len(points)):
        prev = points[i - 1][1]
        cur = points[i][1]
        if prev > 0:
            rets.append((cur - prev) / prev)
    return rets


def _pearson_corr(a: List[float], b: List[float]) -> Optional[float]:
    n = min(len(a), len(b))
    if n < _CORR_MIN_POINTS:
        return None
    a = a[-n:]
    b = b[-n:]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((x - mean_b) ** 2 for x in b)
    denom = math.sqrt(var_a * var_b)
    if denom <= 0:
        return None
    return max(-1.0, min(1.0, cov / denom))


def compute_correlation_matrix(symbols: List[str]) -> List[Dict[str, Any]]:
    """Watchlist'teki tum sembol ciftleri icin korelasyon katsayisini hesaplar."""
    syms = [normalize_symbol(s) for s in symbols]
    with _CORR_HISTORY_LOCK:
        snapshot = {s: list(_CORR_PRICE_HISTORY.get(s, [])) for s in syms}
    returns = {s: _returns_series(snapshot[s]) for s in syms}
    rows: List[Dict[str, Any]] = []
    for i in range(len(syms)):
        for j in range(i + 1, len(syms)):
            s1, s2 = syms[i], syms[j]
            corr = _pearson_corr(returns.get(s1, []), returns.get(s2, []))
            if corr is None:
                continue
            rows.append({
                "pair": f"{s1} ↔ {s2}",
                "symbol_a": s1,
                "symbol_b": s2,
                "correlation": round(corr, 3),
                "strength": (
                    "Güçlü pozitif" if corr >= _CORR_STRONG_THRESHOLD else
                    "Güçlü negatif" if corr <= -_CORR_STRONG_THRESHOLD else
                    "Zayıf/nötr"
                ),
                "sample_size": min(len(returns.get(s1, [])), len(returns.get(s2, []))),
            })
    rows.sort(key=lambda r: abs(r["correlation"]), reverse=True)
    return rows


_CROSS_ASSET_PAIR_DEFS: List[Tuple[str, str, str, str]] = [
    # (title, subtitle, yahoo_key_a, yahoo_key_b)
    ("BTC ↔ Nasdaq", "Kripto ile teknoloji risk iştahı", "BTCUSDT", "NASDAQ"),
    ("BTC ↔ DXY", "Dolar gücü ve kripto baskısı", "BTCUSDT", "DXY"),
    ("BTC ↔ Altın", "Riskten korunma karşılaştırması", "BTCUSDT", "GOLD"),
    ("ETH ↔ BTC", "Kripto içi göreli güç", "ETHUSDT", "BTCUSDT"),
    ("Petrol ↔ ABD 10Y Tahvil", "Enerji fiyatı ve makro baskı", "OIL", "US10Y"),
]


def _yfinance_daily_returns(yahoo_symbol: str, days: int = 90) -> List[float]:
    import yfinance as yf
    hist = yf.Ticker(yahoo_symbol).history(period=f"{days}d", interval="1d")
    if hist is None or hist.empty or "Close" not in hist:
        return []
    closes = [float(c) for c in hist["Close"].tolist() if c and c == c]
    rets: List[float] = []
    for i in range(1, len(closes)):
        prev = closes[i - 1]
        if prev > 0:
            rets.append((closes[i] - prev) / prev)
    return rets


def get_cross_asset_correlations() -> Dict[str, Any]:
    """iOS 'Piyasalar Arası Analiz' kartındaki BTC↔Nasdaq, BTC↔DXY, BTC↔Altın,
    ETH↔BTC, Petrol↔ABD 10Y Tahvil ilişkilerini gerçek 90 günlük Yahoo Finance
    günlük getiri verisiyle hesaplar (önceden bunlar sabit/hardcoded değerlerdi)."""

    def _fetch() -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        cache_returns: Dict[str, List[float]] = {}
        for title, subtitle, key_a, key_b in _CROSS_ASSET_PAIR_DEFS:
            try:
                for k in (key_a, key_b):
                    if k not in cache_returns:
                        yahoo_symbol = YAHOO_MAP.get(k, k)
                        cache_returns[k] = _yfinance_daily_returns(yahoo_symbol)
                corr = _pearson_corr(cache_returns.get(key_a, []), cache_returns.get(key_b, []))
                if corr is None:
                    results.append({
                        "title": title, "subtitle": subtitle,
                        "correlation": None, "status": "Bekleniyor",
                    })
                    continue
                strength = (
                    "Güçlü pozitif" if corr >= 0.6 else
                    "Güçlü negatif" if corr <= -0.6 else
                    "Zayıf/nötr"
                )
                results.append({
                    "title": title,
                    "subtitle": subtitle,
                    "correlation": round(corr, 3),
                    "status": strength,
                })
            except Exception as exc:
                results.append({
                    "title": title, "subtitle": subtitle,
                    "correlation": None, "status": "Bekleniyor", "error": str(exc),
                })
        return {"ok": True, "pairs": results, "time": now_text()}

    return _cache_get_or_fetch("cross_asset_correlations", 21600, _fetch)


def get_correlation_pair_signal(symbol: str, all_watchlist_symbols: List[str]) -> Dict[str, Any]:
    """Verilen sembol icin en guclu korele oldugu es (peer) varligi bulur;
    peer belirgin hareket ettiyse ama bu sembol henuz takip etmediyse bir
    "lag" sinyali (BUY/SELL) ve gerekce metni dondurur. Sinyal yoksa
    action=WAIT, bias=0 doner."""
    sym = normalize_symbol(symbol)
    peers = [normalize_symbol(s) for s in all_watchlist_symbols if normalize_symbol(s) != sym]
    with _CORR_HISTORY_LOCK:
        sym_points = list(_CORR_PRICE_HISTORY.get(sym, []))
        peer_points = {p: list(_CORR_PRICE_HISTORY.get(p, [])) for p in peers}
    sym_returns = _returns_series(sym_points)
    if len(sym_returns) < _CORR_MIN_POINTS or len(sym_points) < 2:
        return {"action": "WAIT", "bias": 0, "note": ""}

    def _recent_move_pct(points: List[Tuple[float, float]], lookback: int = 6) -> float:
        if len(points) < 2:
            return 0.0
        window = points[-lookback:] if len(points) >= lookback else points
        first_price = window[0][1]
        last_price = window[-1][1]
        if first_price <= 0:
            return 0.0
        return (last_price - first_price) / first_price * 100.0

    sym_move = _recent_move_pct(sym_points)
    best_peer = None
    best_corr = 0.0
    for peer in peers:
        pts = peer_points.get(peer, [])
        peer_returns = _returns_series(pts)
        corr = _pearson_corr(sym_returns, peer_returns)
        if corr is None:
            continue
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_peer = peer

    if best_peer is None or abs(best_corr) < _CORR_STRONG_THRESHOLD:
        return {"action": "WAIT", "bias": 0, "note": ""}

    peer_move = _recent_move_pct(peer_points.get(best_peer, []))
    if abs(peer_move) < _CORR_LAG_MOVE_PCT:
        return {"action": "WAIT", "bias": 0, "note": ""}
    if abs(sym_move) > _CORR_FOLLOW_TOLERANCE_PCT:
        # Sembol zaten hareket etmis, "henuz gelmedi" durumu yok - lag sinyali gecersiz.
        return {"action": "WAIT", "bias": 0, "note": ""}

    if best_corr >= _CORR_STRONG_THRESHOLD:
        # Pozitif korelasyon: peer yukari gittiyse bu da yukari gitmeli (henuz gitmedi -> BUY),
        # peer asagi gittiyse bu da asagi gitmeli (henuz gitmedi -> SELL).
        action = "BUY" if peer_move > 0 else "SELL"
        note = (
            f"Korelasyon sinyali: {best_peer} son periyotta %{peer_move:.2f} hareket etti, "
            f"{sym} (korelasyon {best_corr:.2f}) henüz takip etmedi -> {action} bekleniyor (lag)."
        )
    else:
        # Negatif korelasyon (hedge cifti): peer yukari gittiyse bu asagi gitmeli (SELL),
        # peer asagi gittiyse bu yukari gitmeli (BUY).
        action = "SELL" if peer_move > 0 else "BUY"
        note = (
            f"Ters korelasyon (hedge) sinyali: {best_peer} son periyotta %{peer_move:.2f} hareket etti, "
            f"{sym} (korelasyon {best_corr:.2f}) ters yönde tepki vermesi bekleniyor -> {action}."
        )
    bias = 8 if abs(best_corr) >= 0.8 else 5
    return {"action": action, "bias": bias, "note": note, "peer": best_peer, "peer_move_pct": round(peer_move, 3), "correlation": round(best_corr, 3)}


def auto_trader_cycle(state=None, lock=None, history=None) -> None:
    if state is None:
        state = AUTO_TRADER
    if lock is None:
        lock = AUTO_LOCK
    if history is None:
        history = AUTO_HISTORY

    with lock:
        if not state.enabled:
            return
        broker = state.broker.upper()
        symbols = list(state.symbols) if state.symbols else [normalize_symbol(state.symbol)]
        market = state.market.upper()
        base_qty = max(0.0, state.quantity)
        min_conf = state.min_confidence
        mode = state.mode
        asset_type = state.asset_type
        exchange = state.exchange
        currency = state.currency
        eval_window = state.evaluation_window_sec
        max_daily = state.max_daily_trades
        day_key = datetime.now().strftime("%Y-%m-%d")
        if not state.last_update.startswith(day_key):
            state.daily_trade_count = 0

    if broker == "BINANCE":
        tp_execution = enforce_binance_take_profit(channel="auto_take_profit")
        if tp_execution:
            with lock:
                fallback_symbol = symbols[0] if symbols else normalize_symbol(state.symbol)
                trigger_label = "STOP_LOSS" if tp_execution.get("trigger") == "stop_loss_roi_pct" else "TAKE_PROFIT"
                state.last_action = trigger_label
                state.last_confidence = 100
                target_pct = tp_execution.get("target_pct", BINANCE_TAKE_PROFIT_PCT)
                state.last_reason = (
                    f"{tp_execution.get('symbol', fallback_symbol)} için %"
                    f"{abs(safe_float(target_pct)):.2f} {'zarar-kes' if trigger_label == 'STOP_LOSS' else 'kâr hedefi'} tetiklendi."
                )
                state.last_price = 0.0
                state.last_update = now_text()
                state.last_error = str(tp_execution.get("error", "") or "")
                state.updated_at_epoch = time.time()
                history.insert(
                    0,
                    {
                        "time": state.last_update,
                        "broker": broker,
                        "symbol": tp_execution.get("symbol", fallback_symbol),
                        "action": trigger_label,
                        "confidence": 100,
                        "price": 0.0,
                        "reason": state.last_reason,
                        "execution": tp_execution,
                    },
                )
                del history[300:]
                db_insert_auto_history(
                    broker=broker,
                    symbol=str(tp_execution.get("symbol", fallback_symbol)),
                    action=trigger_label,
                    confidence=100,
                    price=0.0,
                    reason=state.last_reason,
                    execution=tp_execution,
                )
            return

    if broker == "IBKR":
        ibkr_tp_execution = enforce_ibkr_take_profit_stop_loss(channel="auto_take_profit")
        if ibkr_tp_execution:
            with lock:
                fallback_symbol = symbols[0] if symbols else normalize_symbol(state.symbol)
                trigger_label = "STOP_LOSS" if ibkr_tp_execution.get("trigger") == "stop_loss_roi_pct" else "TAKE_PROFIT"
                state.last_action = trigger_label
                state.last_confidence = 100
                target_pct = ibkr_tp_execution.get("target_pct", IBKR_TAKE_PROFIT_PCT)
                state.last_reason = (
                    f"{ibkr_tp_execution.get('symbol', fallback_symbol)} için %"
                    f"{abs(safe_float(target_pct)):.2f} {'zarar-kes' if trigger_label == 'STOP_LOSS' else 'kâr hedefi'} tetiklendi."
                )
                state.last_price = 0.0
                state.last_update = now_text()
                state.last_error = str(ibkr_tp_execution.get("error", "") or "")
                state.updated_at_epoch = time.time()
                history.insert(
                    0,
                    {
                        "time": state.last_update,
                        "broker": broker,
                        "symbol": ibkr_tp_execution.get("symbol", fallback_symbol),
                        "action": trigger_label,
                        "confidence": 100,
                        "price": 0.0,
                        "reason": state.last_reason,
                        "execution": ibkr_tp_execution,
                    },
                )
                del history[300:]
                db_insert_auto_history(
                    broker=broker,
                    symbol=str(ibkr_tp_execution.get("symbol", fallback_symbol)),
                    action=trigger_label,
                    confidence=100,
                    price=0.0,
                    reason=state.last_reason,
                    execution=ibkr_tp_execution,
                )
            return

    if broker == "BINANCE_SPOT":
        spot_tp_execution = enforce_spot_take_profit_stop_loss(channel="auto_take_profit")
        if spot_tp_execution:
            with lock:
                fallback_symbol = symbols[0] if symbols else normalize_symbol(state.symbol)
                trigger_label = "STOP_LOSS" if spot_tp_execution.get("trigger") == "stop_loss_roi_pct" else "TAKE_PROFIT"
                state.last_action = trigger_label
                state.last_confidence = 100
                target_pct = spot_tp_execution.get("target_pct", BINANCE_TAKE_PROFIT_PCT)
                state.last_reason = (
                    f"{spot_tp_execution.get('symbol', fallback_symbol)} için %"
                    f"{abs(safe_float(target_pct)):.2f} {'zarar-kes' if trigger_label == 'STOP_LOSS' else 'kâr hedefi'} tetiklendi (Spot)."
                )
                state.last_price = 0.0
                state.last_update = now_text()
                state.last_error = str(spot_tp_execution.get("error", "") or "")
                state.updated_at_epoch = time.time()
                history.insert(
                    0,
                    {
                        "time": state.last_update,
                        "broker": broker,
                        "symbol": spot_tp_execution.get("symbol", fallback_symbol),
                        "action": trigger_label,
                        "confidence": 100,
                        "price": 0.0,
                        "reason": state.last_reason,
                        "execution": spot_tp_execution,
                    },
                )
                del history[300:]
                db_insert_auto_history(
                    broker=broker,
                    symbol=str(spot_tp_execution.get("symbol", fallback_symbol)),
                    action=trigger_label,
                    confidence=100,
                    price=0.0,
                    reason=state.last_reason,
                    execution=spot_tp_execution,
                )
            return

    # Cok sembollu tarama: watchlist'teki HER sembol icin ayri sinyal uretilir ve
    # uygun olanlarda ayri ayri islem acilir. Gunluk islem limiti (max_daily_trades)
    # tum semboller arasinda PAYLASILIR (tek bir hesap risk butcesi gibi calisir).
    for symbol in symbols:
        _auto_trader_run_symbol(
            state, lock, history, broker, symbol, market, base_qty, min_conf,
            mode, asset_type, exchange, currency, eval_window, max_daily,
        )


def _auto_trader_run_symbol(
    state, lock, history, broker, symbol, market, qty, min_conf,
    mode, asset_type, exchange, currency, eval_window, max_daily,
) -> None:
    action = "WAIT"
    confidence = 50
    reason = "Koşullar bekleniyor."
    price = 0.0
    execution: Dict[str, Any] = {"simulated": True, "message": "Emir yok"}

    if broker == "IBKR":
        # IBKR icin iki bagimsiz sinyal kullanilir: (1) fiyat momentumu (change_24h),
        # (2) emir defteri bid/ask boyut dengesi (order_flow_signal). Ikisi ayni yonde
        # BUY/SELL derse islem acilir; biri WAIT/NEUTRAL ise digeri tek basina yeterlidir
        # (boylece tek sinyal her zaman zorunlu tutulmaz, "hic islem acmiyor" sorunu onlenir),
        # ama ikisi ZIT yon gosterirse (biri BUY biri SELL) islem acilmaz - celiskili sinyal.
        snap = ibkr_market_snapshot(symbol, asset_type, exchange, currency)
        price = safe_float(snap.get("price"))
        change = safe_float(snap.get("change_24h"))
        order_flow = str(snap.get("order_flow_signal", "NEUTRAL")).upper()

        momentum_signal = "WAIT"
        if change > 0.6:
            momentum_signal = "BUY"
        elif change < -0.6:
            momentum_signal = "SELL"

        if momentum_signal in ["BUY", "SELL"] and order_flow in ["BUY", "SELL"] and momentum_signal != order_flow:
            action = "WAIT"
            confidence = 50
            reason = (
                f"IBKR sinyalleri çelişiyor: momentum {momentum_signal} (24s değişim %{change:.2f}), "
                f"emir akışı {order_flow} -> işlem açılmadı."
            )
        else:
            action = momentum_signal if momentum_signal in ["BUY", "SELL"] else (order_flow if order_flow in ["BUY", "SELL"] else "WAIT")
            confidence = min(90, int(55 + abs(change) * 11))
            if momentum_signal in ["BUY", "SELL"] and order_flow == momentum_signal:
                confidence = min(95, confidence + 10)
                reason = (
                    f"IBKR çift teyit: momentum {momentum_signal} (24s değişim %{change:.2f}) "
                    f"ve emir akışı da {order_flow} yönünde."
                )
            elif momentum_signal in ["BUY", "SELL"]:
                reason = f"IBKR momentum sinyali: 24s değişim %{change:.2f} ({momentum_signal}), emir akışı nötr."
            elif order_flow in ["BUY", "SELL"]:
                reason = f"IBKR emir akışı sinyali: bid/ask dengesi {order_flow} yönünde, momentum nötr."
            else:
                reason = f"IBKR: net sinyal yok (24s değişim %{change:.2f})."
    else:
        ai = calculate_ai_signal(symbol, market)
        action = str(ai.get("signal", "WAIT")).upper()
        confidence = int(ai.get("confidence", 50))
        price = safe_float(ai.get("price"))
        reason = str(ai.get("reason", ""))

    # Korelasyon/lag/hedge motoru: fiyat gecmisine kaydet ve bu sembol icin
    # en guclu korele oldugu esin (peer) henuz takip edilmemis hareketi var mi bak.
    if price > 0:
        record_correlation_price(symbol, price)
    corr_signal = get_correlation_pair_signal(symbol, state.symbols or [symbol])
    if corr_signal["action"] in ["BUY", "SELL"]:
        if action == "WAIT":
            # Baska sinyal yokken, guclu bir korelasyon/lag firsati tek basina islem acabilir.
            action = corr_signal["action"]
            confidence = 58 + corr_signal["bias"]
            reason = corr_signal["note"]
        elif action == corr_signal["action"]:
            confidence = min(95, confidence + corr_signal["bias"])
            reason = (reason + " " + corr_signal["note"]).strip()
        # action mevcut sinyalle ters yondeyse mevcut (dogrudan) sinyale mudahale etmiyoruz.

    if action in ["BUY", "SELL"]:
        confidence = max(0, min(95, confidence + learning_bias(action)))
        # Dis sinyaller (SEC dosyalama sicramasi, haber sentiment'i, Fear&Greed, makro
        # rejim, jeopolitik risk) artik IBKR (hisse) icin de uygulaniyor - bunlar zaten
        # var olan genel/makro gostergeler. Funding rate ve whale long/short orani gibi
        # sadece Binance Futures'a ozgu olanlar IBKR sembolleri icin otomatik "error"
        # donup sessizce atlanir, IBKR'a zarar vermez.
        ext = get_external_signal_bias(symbol, action)
        if ext["bias"] != 0:
            confidence = max(0, min(95, confidence + ext["bias"]))
        if ext["notes"]:
            reason = (reason + " " + " ".join(ext["notes"])).strip()

        # Balon/asiri degerleme, bilanco sagligi, short/long pozisyonlanma-manipulasyon
        # ve sektorler arasi aktif senaryo analizini de karar mekanizmasina dahil et.
        macro_risk = get_macro_risk_bias(symbol, action)
        if macro_risk["bias"] != 0:
            confidence = max(0, min(95, confidence + macro_risk["bias"]))
        if macro_risk["notes"]:
            reason = (reason + " " + " ".join(macro_risk["notes"])).strip()
    resolve_learning(symbol, price)

    with lock:
        allow_trade = (
            action in ["BUY", "SELL"]
            and confidence >= min_conf
            and state.daily_trade_count < max_daily
            and qty > 0
        )
        do_live = mode == "live" and ((broker == "IBKR" and IBKR_LIVE_TRADING) or (broker != "IBKR" and LIVE_TRADING))
        if allow_trade:
            if broker == "BINANCE_SPOT":
                # Spot'ta short mumkun degil: SELL sadece zaten sahip oldugumuz
                # (kendi izledigimiz spot_positions tablosundaki) pozisyon varsa
                # yapilir; BUY ise zaten acik pozisyon varken tekrar alim yapmaz
                # (ust uste ortalama yerine tek pozisyon takip edilir).
                existing_position = db_get_spot_position(symbol)
                spot_skip_reason = ""
                if action == "SELL":
                    if not existing_position or safe_float(existing_position.get("quantity")) <= 0:
                        spot_skip_reason = "Spot'ta short mümkün değil ve elde pozisyon yok, SELL sinyali atlandı."
                        qty = 0
                    else:
                        qty = safe_float(existing_position.get("quantity"))
                else:
                    if existing_position and safe_float(existing_position.get("quantity")) > 0:
                        spot_skip_reason = "Zaten açık spot pozisyon var, üst üste alım yapılmadı."
                        qty = 0
                    elif price > 0:
                        available_usdt = get_spot_available_usdt()
                        if available_usdt > 0:
                            pct = spot_auto_trader_size_pct(symbol)
                            sized_qty = round((available_usdt * pct) / price, 6)
                            min_notional = 11.0  # Binance spot min ~10 USD + güvenlik payı
                            if sized_qty * price < min_notional:
                                sized_qty = round(math.ceil((min_notional / price) * 1_000_000) / 1_000_000, 6)
                            qty = sized_qty
                            reason = (
                                reason
                                + f" (Spot pozisyon büyüklüğü: bakiye {available_usdt:.2f} USDT'nin %{pct * 100:.0f}'i -> {sized_qty:.6f} {symbol}.)"
                            ).strip()
                        else:
                            spot_skip_reason = "Spot USDT bakiyesi alınamadı, alım yapılmadı."
                            qty = 0
                if spot_skip_reason:
                    execution = {
                        "simulated": True,
                        "broker": "BINANCE_SPOT",
                        "symbol": symbol,
                        "side": action,
                        "quantity": 0,
                        "message": spot_skip_reason,
                        "time": now_text(),
                    }
                elif qty > 0:
                    if do_live:
                        execution = place_spot_order(symbol, action, qty)
                        if not execution.get("error"):
                            if action == "BUY":
                                db_upsert_spot_position(symbol, qty, price)
                            else:
                                db_delete_spot_position(symbol)
                    else:
                        execution = {
                            "simulated": True,
                            "broker": "BINANCE_SPOT",
                            "symbol": symbol,
                            "side": action,
                            "quantity": qty,
                            "message": "Paper mode: Spot gerçek emir kapalı.",
                            "time": now_text(),
                        }
            elif broker == "IBKR":
                if do_live:
                    # Sabit miktarli (ör. 1 hisse) emir, hesaptaki diger pozisyonlarin
                    # kullandigi marj yuzunden 'Available Funds insufficient' hatasiyla
                    # iptal edilebiliyordu (gercek IBKR hatasi: Error 201 Order rejected -
                    # margin requirement). Emir gondermeden once kullanilabilir fonu kontrol
                    # edip, gerekirse miktari guvenli bir seviyeye (kullanilabilir fonun
                    # %80'i) dusuruyoruz. IBKR kesirli (fractional) hisse alimini destekledigi
                    # icin miktari tam sayiya yuvarlamiyoruz.
                    if action == "BUY" and price > 0:
                        available_funds = get_ibkr_available_funds()
                        needed = qty * price
                        safe_budget = available_funds * 0.8
                        if available_funds > 0 and needed > safe_budget:
                            affordable_qty = round(safe_budget / price, 4)
                            min_fractional_qty = 0.01
                            if affordable_qty < min_fractional_qty:
                                execution = {
                                    "simulated": False,
                                    "broker": "IBKR",
                                    "symbol": symbol,
                                    "side": action,
                                    "quantity": 0,
                                    "error": (
                                        f"Yetersiz alım gücü: kullanılabilir fon {available_funds:.2f} USD, "
                                        f"minimum kesirli hisse tutarını bile karşılamıyor. Emir gönderilmedi."
                                    ),
                                    "time": now_text(),
                                }
                                qty = 0
                            else:
                                reason = (
                                    reason
                                    + f" (Miktar {qty} -> {affordable_qty} olarak düşürüldü (kesirli hisse): kullanılabilir fon {available_funds:.2f} USD ile sınırlı.)"
                                ).strip()
                                qty = affordable_qty
                    if qty > 0 and "error" not in execution:
                        execution = ibkr_place_market_order(symbol, action, qty, asset_type, exchange, currency)
                        # Gercek bir emir denendi (fill/cancel farketmeksizin) - kullanilabilir
                        # fon degisebilir, sonraki sembol icin bayat deger kullanilmasin diye
                        # cache'i temizliyoruz.
                        _invalidate_cache("ibkr_available_funds")
                else:
                    execution = {
                        "simulated": True,
                        "broker": "IBKR",
                        "symbol": symbol,
                        "side": action,
                        "quantity": qty,
                        "message": "Paper mode: IBKR gerçek emir kapalı.",
                        "time": now_text(),
                    }
            else:
                # Varlik bazli pozisyon boyutlandirma: sabit miktar yerine, bosta bekleyen
                # futures USDT bakiyesinin belirli bir yuzdesi kadar pozisyon acilir
                # (BTC %25, ETH %20, diger varliklar %10 - varsayilan, env ile ayarlanabilir).
                # Kaldirac (leverage) artik sinyal gucune (confidence) gore belirlenir:
                # guclu sinyallerde max kaldirac (varsayilan 3x), zayif sinyallerde min
                # kaldirac (varsayilan 2x) kullanilir - max kaldirac hicbir zaman asilmaz.
                leverage = signal_leverage(confidence)
                if price > 0:
                    available_usdt = get_futures_available_usdt()
                    if available_usdt > 0:
                        pct = asset_size_pct(symbol)
                        sized_qty = round((available_usdt * pct * leverage) / price, 3)
                        if sized_qty > 0:
                            reason = (
                                reason
                                + f" (Pozisyon buyuklugu: bakiye {available_usdt:.2f} USDT'nin %{pct * 100:.0f}'i x{leverage} kaldirac (guven %{confidence}) -> {sized_qty:.6f} {symbol}.)"
                            ).strip()
                            qty = sized_qty
                min_notional = 21.0  # Binance min 20 USD + güvenlik payı
                if price > 0 and qty * price < min_notional:
                    adj_qty = math.ceil((min_notional / price) * 1000) / 1000.0
                    reason = (reason + f" (Miktar {qty} -> {adj_qty} olarak yükseltildi: min. işlem tutarı {min_notional}$ altında kalıyordu.)").strip()
                    qty = adj_qty
                if do_live:
                    ensure_binance_leverage(symbol, leverage)
                    execution = place_futures_order(symbol, action, qty, reduce_only=False)
                else:
                    execution = {
                        "simulated": True,
                        "broker": "Binance",
                        "symbol": symbol,
                        "side": action,
                        "quantity": qty,
                        "message": "Paper mode: Binance gerçek emir kapalı.",
                        "time": now_text(),
                    }
            if execution.get("error"):
                state.last_error = str(execution.get("error"))
            else:
                state.last_error = ""
                state.daily_trade_count += 1
                queue_signal_for_learning(symbol, action, price, eval_window)
        else:
            state.last_error = ""

        state.last_action = action
        state.last_confidence = confidence
        state.last_reason = reason
        state.last_price = price
        state.symbol = symbol
        state.last_update = now_text()
        state.updated_at_epoch = time.time()
        history.insert(
            0,
            {
                "time": state.last_update,
                "broker": broker,
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "price": price,
                "reason": reason,
                "execution": execution,
            },
        )
        del history[300:]

        # Log to persistent DB
        db_insert_auto_history(
            broker=broker,
            symbol=symbol,
            action=action,
            confidence=confidence,
            price=price,
            reason=reason,
            execution=execution,
        )
def _ibkr_keepalive_loop():
    while True:
        time.sleep(max(8, IBKR_KEEPALIVE_SEC))
        if not IBKR_ENABLED:
            continue
        try:
            ibkr_ping()
        except Exception:
            pass


def _auto_trader_loop():
    while True:
        with AUTO_LOCK:
            enabled = AUTO_TRADER.enabled
            interval_sec = max(8, AUTO_TRADER.interval_sec)
            elapsed = time.time() - AUTO_TRADER.updated_at_epoch if AUTO_TRADER.updated_at_epoch else 10_000
        if enabled and elapsed >= interval_sec:
            try:
                auto_trader_cycle()
            except Exception as e:
                with AUTO_LOCK:
                    AUTO_TRADER.last_error = str(e)
                    AUTO_TRADER.last_update = now_text()
                    AUTO_TRADER.updated_at_epoch = time.time()

        with IBKR_AUTO_LOCK:
            ibkr_enabled = IBKR_AUTO_TRADER.enabled
            ibkr_interval_sec = max(8, IBKR_AUTO_TRADER.interval_sec)
            ibkr_elapsed = time.time() - IBKR_AUTO_TRADER.updated_at_epoch if IBKR_AUTO_TRADER.updated_at_epoch else 10_000
        if ibkr_enabled and IBKR_ENABLED and ibkr_elapsed >= ibkr_interval_sec:
            try:
                auto_trader_cycle(IBKR_AUTO_TRADER, IBKR_AUTO_LOCK, IBKR_AUTO_HISTORY)
            except Exception as e:
                with IBKR_AUTO_LOCK:
                    IBKR_AUTO_TRADER.last_error = str(e)
                    IBKR_AUTO_TRADER.last_update = now_text()
                    IBKR_AUTO_TRADER.updated_at_epoch = time.time()

        with SPOT_AUTO_LOCK:
            spot_enabled = SPOT_AUTO_TRADER.enabled
            spot_interval_sec = max(8, SPOT_AUTO_TRADER.interval_sec)
            spot_elapsed = time.time() - SPOT_AUTO_TRADER.updated_at_epoch if SPOT_AUTO_TRADER.updated_at_epoch else 10_000
        if spot_enabled and spot_elapsed >= spot_interval_sec:
            try:
                auto_trader_cycle(SPOT_AUTO_TRADER, SPOT_AUTO_LOCK, SPOT_AUTO_HISTORY)
            except Exception as e:
                with SPOT_AUTO_LOCK:
                    SPOT_AUTO_TRADER.last_error = str(e)
                    SPOT_AUTO_TRADER.last_update = now_text()
                    SPOT_AUTO_TRADER.updated_at_epoch = time.time()

        time.sleep(1.0)


def start_background_workers_once():
    global KEEPALIVE_THREAD_STARTED, AUTO_THREAD_STARTED, IBKR_WORKER_THREAD_STARTED
    if not IBKR_WORKER_THREAD_STARTED:
        t0 = threading.Thread(target=_ibkr_worker_thread_main, daemon=True)
        t0.start()
        IBKR_WORKER_THREAD_STARTED = True
    if not KEEPALIVE_THREAD_STARTED:
        t1 = threading.Thread(target=_ibkr_keepalive_loop, daemon=True)
        t1.start()
        KEEPALIVE_THREAD_STARTED = True
    if not AUTO_THREAD_STARTED:
        t2 = threading.Thread(target=_auto_trader_loop, daemon=True)
        t2.start()
        AUTO_THREAD_STARTED = True


def get_24h(symbol: str, market: str) -> Dict[str, Any]:
    base = FUTURES_BASE if market.upper() == "FUTURES" else SPOT_BASE
    path = "/fapi/v1/ticker/24hr" if market.upper() == "FUTURES" else "/api/v3/ticker/24hr"
    return public_get(base, path, {"symbol": symbol})


def pressure_from_change(change: float) -> Dict[str, float]:
    if change > 1:
        buy = min(68.0, 52.0 + change * 3)
    elif change < -1:
        buy = max(32.0, 48.0 + change * 3)
    else:
        buy = 50.0 + change
    return {"buy_pressure": round(buy, 2), "sell_pressure": round(100 - buy, 2)}


def synthetic_orderbook(change: float, source: str) -> Dict[str, Any]:
    pressure = pressure_from_change(change)
    return {
        "bid_notional": 0.0,
        "ask_notional": 0.0,
        "buy_pressure": pressure["buy_pressure"],
        "sell_pressure": pressure["sell_pressure"],
        "summary": f"Alış %{pressure['buy_pressure']:.1f} / Satış %{pressure['sell_pressure']:.1f}",
        "synthetic": True,
        "source": source,
    }


def get_orderbook_pressure(symbol: str, market: str, limit: int = 50) -> Dict[str, Any]:
    base = FUTURES_BASE if market.upper() == "FUTURES" else SPOT_BASE
    path = "/fapi/v1/depth" if market.upper() == "FUTURES" else "/api/v3/depth"
    data = public_get(base, path, {"symbol": symbol, "limit": limit})

    bids = data.get("bids", [])
    asks = data.get("asks", [])
    bid_notional = sum(safe_float(p) * safe_float(q) for p, q in bids[:limit])
    ask_notional = sum(safe_float(p) * safe_float(q) for p, q in asks[:limit])
    total = bid_notional + ask_notional
    buy_pressure = 50.0 if total <= 0 else (bid_notional / total) * 100.0
    sell_pressure = 100.0 - buy_pressure

    return {
        "bid_notional": round(bid_notional, 2),
        "ask_notional": round(ask_notional, 2),
        "buy_pressure": round(buy_pressure, 2),
        "sell_pressure": round(sell_pressure, 2),
        "summary": f"Alış %{buy_pressure:.1f} / Satış %{sell_pressure:.1f}",
    }


def try_coinbase_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    product = COINBASE_MAP.get(symbol)
    if not product:
        return None
    try:
        data = get_json(f"https://api.coinbase.com/v2/prices/{product}/spot")
        price = safe_float(data.get("data", {}).get("amount"))
        if price > 0:
            return {
                "source": "coinbase",
                "price": price,
                "change_24h": 0.0,
                "high_24h": price,
                "low_24h": price,
                "quote_volume": 0.0,
            }
    except Exception:
        return None
    return None


def try_coingecko_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    coin_id = COINGECKO_MAP.get(symbol)
    if not coin_id:
        return None
    try:
        data = get_json(
            "https://api.coingecko.com/api/v3/simple/price",
            {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
            },
        )
        row = data.get(coin_id, {})
        price = safe_float(row.get("usd"))
        if price > 0:
            return {
                "source": "coingecko",
                "price": price,
                "change_24h": safe_float(row.get("usd_24h_change")),
                "high_24h": price,
                "low_24h": price,
                "quote_volume": safe_float(row.get("usd_24h_vol")),
            }
    except Exception:
        return None
    return None


def try_yahoo_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    yahoo_symbol = YAHOO_MAP.get(symbol)
    if not yahoo_symbol:
        return None
    try:
        data = get_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
            {"range": "1d", "interval": "1m"},
        )
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None
        meta = result[0].get("meta", {})
        price = safe_float(meta.get("regularMarketPrice") or meta.get("previousClose"))
        prev = safe_float(meta.get("previousClose"))
        if price <= 0:
            return None
        change = ((price - prev) / prev) * 100.0 if prev > 0 else 0.0
        return {
            "source": "yahoo",
            "price": price,
            "change_24h": change,
            "high_24h": safe_float(meta.get("regularMarketDayHigh"), price),
            "low_24h": safe_float(meta.get("regularMarketDayLow"), price),
            "quote_volume": safe_float(meta.get("regularMarketVolume")),
        }
    except Exception:
        return None
    return None


def get_market_snapshot(symbol: str, market: str) -> Dict[str, Any]:
    try:
        ticker = get_24h(symbol, market)
        change = safe_float(ticker.get("priceChangePercent"))
        return {
            "source": "binance",
            "price": safe_float(ticker.get("lastPrice") or ticker.get("weightedAvgPrice")),
            "change_24h": change,
            "high_24h": safe_float(ticker.get("highPrice")),
            "low_24h": safe_float(ticker.get("lowPrice")),
            "quote_volume": safe_float(ticker.get("quoteVolume")),
            "orderbook": get_orderbook_pressure(symbol, market),
        }
    except Exception as e:
        binance_error = short_binance_error(str(e))
        for provider in (try_coinbase_ticker, try_coingecko_ticker, try_yahoo_ticker):
            fallback = provider(symbol)
            if fallback:
                change = safe_float(fallback.get("change_24h"))
                return {
                    "source": fallback.get("source", "fallback"),
                    "price": safe_float(fallback.get("price")),
                    "change_24h": change,
                    "high_24h": safe_float(fallback.get("high_24h")),
                    "low_24h": safe_float(fallback.get("low_24h")),
                    "quote_volume": safe_float(fallback.get("quote_volume")),
                    "orderbook": synthetic_orderbook(change, str(fallback.get("source", "fallback"))),
                    "binance_error": binance_error,
                }
        raise RuntimeError(binance_error)


def get_futures_positions() -> List[Dict[str, Any]]:
    if BINANCE_PROXY_BASE_URL:
        try:
            # Try direct /positions endpoint first (VPS proxy has this)
            legacy_pos = _binance_proxy_request("GET", "/positions")
            rows = _proxy_extract_positions_from_legacy_positions(legacy_pos)
            if rows:
                return rows
            # If empty, try /portfolio fallback
            legacy = _binance_proxy_portfolio_payload()
            rows = _proxy_extract_positions_from_portfolio(legacy)
            if rows:
                return rows
            raise RuntimeError("Proxy /positions veya /portfolio'dan futures position bulunamadı.")
        except Exception as proxy_err:
            pass
    try:
        data = signed_request("GET", FUTURES_BASE, "/fapi/v2/positionRisk", {})
        positions = []
        for p in data:
            amt = safe_float(p.get("positionAmt"))
            if abs(amt) <= 0:
                continue
            entry = safe_float(p.get("entryPrice"))
            mark = safe_float(p.get("markPrice"))
            pnl = safe_float(p.get("unRealizedProfit"))
            side = "LONG" if amt > 0 else "SHORT"
            positions.append({
                "id": f"BINANCE-FUTURES-{p.get('symbol')}",
                "broker": "Binance",
                "market": "Futures",
                "symbol": p.get("symbol", ""),
                "side": side,
                "size": abs(amt),
                "entry_price": entry,
                "mark_price": mark,
                "pnl": pnl,
                "leverage": p.get("leverage", ""),
            })
        return positions
    except Exception as e:
        return [{"id": "error", "broker": "Binance", "market": "Futures", "symbol": "HATA", "side": "-", "size": 0, "entry_price": 0, "mark_price": 0, "pnl": 0, "error": str(e)}]


def binance_position_profit_pct(position: Dict[str, Any]) -> float:
    entry = safe_float(position.get("entry_price"))
    mark = safe_float(position.get("mark_price"))
    pnl = safe_float(position.get("pnl"))
    size = abs(safe_float(position.get("size")))
    leverage = max(1.0, safe_float(position.get("leverage"), 1.0))
    if entry <= 0 or mark <= 0:
        return 0.0
    if pnl != 0 and size > 0:
        initial_margin = (entry * size) / leverage
        if initial_margin > 0:
            return (pnl / initial_margin) * 100.0
    side = str(position.get("side", "")).upper()
    raw_pct = ((mark - entry) / entry) * 100.0
    directional_pct = raw_pct if side == "LONG" else -raw_pct
    return directional_pct * leverage


def enforce_binance_take_profit(channel: str = "auto") -> Optional[Dict[str, Any]]:
    """Binance futures pozisyonlarinda hem kar-al (BINANCE_TAKE_PROFIT_PCT) hem de
    zarar-kes (BINANCE_STOP_LOSS_PCT) esiklerini kontrol eder. Onceden sadece
    kar-al vardi; hesap zarar yonunde sinirsiz acik kalabiliyordu."""
    if BINANCE_TAKE_PROFIT_PCT <= 0 and BINANCE_STOP_LOSS_PCT <= 0:
        return None
    positions = [
        p for p in get_futures_positions()
        if p.get("id") != "error" and str(p.get("symbol", "")).upper() != "HATA"
    ]
    for position in positions:
        profit_pct = binance_position_profit_pct(position)
        hit_take_profit = BINANCE_TAKE_PROFIT_PCT > 0 and profit_pct >= BINANCE_TAKE_PROFIT_PCT
        hit_stop_loss = BINANCE_STOP_LOSS_PCT > 0 and profit_pct <= -BINANCE_STOP_LOSS_PCT
        if not hit_take_profit and not hit_stop_loss:
            continue
        symbol = str(position.get("symbol", "")).upper()
        size = abs(safe_float(position.get("size")))
        if not symbol or size <= 0:
            continue
        close_side = "SELL" if str(position.get("side", "")).upper() == "LONG" else "BUY"
        trigger = "take_profit_roi_pct" if hit_take_profit else "stop_loss_roi_pct"
        request_id = f"{'tp' if hit_take_profit else 'sl'}-{symbol}-{int(time.time())}"
        result = place_futures_order(
            symbol,
            close_side,
            size,
            reduce_only=True,
            request_id=request_id,
            channel=channel,
        )
        result["trigger"] = trigger
        result["trigger_pct"] = round(profit_pct, 4)
        result["target_pct"] = BINANCE_TAKE_PROFIT_PCT if hit_take_profit else -BINANCE_STOP_LOSS_PCT
        result["pnl"] = safe_float(position.get("pnl"))
        if not result.get("error"):
            entry_price = safe_float(position.get("entry_price"))
            exit_price = safe_float(position.get("mark_price"))
            pnl_amount = safe_float(position.get("pnl"))
            db_record_position_closure(
                broker="BINANCE_FUTURES",
                symbol=symbol,
                side=str(position.get("side", "")).upper(),
                qty=size,
                entry_price=entry_price,
                exit_price=exit_price,
                realized_pnl=pnl_amount,
                realized_pnl_pct=profit_pct,
                close_reason="TAKE_PROFIT" if hit_take_profit else "STOP_LOSS",
                detail=(
                    f"%{BINANCE_TAKE_PROFIT_PCT:.1f} kâr hedefi tetiklendi." if hit_take_profit
                    else f"%{BINANCE_STOP_LOSS_PCT:.1f} zarar-kes tetiklendi."
                ),
            )
        return result
    return None


def ibkr_position_profit_pct(position: Dict[str, Any]) -> float:
    """IBKR hisse pozisyonu icin maliyet bazli kar/zarar yuzdesini hesaplar."""
    avg_cost = safe_float(position.get("avgCost") or position.get("entry_price"))
    pnl = safe_float(position.get("pnl"))
    qty = abs(safe_float(position.get("position") or position.get("size")))
    if avg_cost > 0 and qty > 0:
        cost_basis = avg_cost * qty
        if cost_basis > 0:
            return (pnl / cost_basis) * 100.0
    mark = safe_float(position.get("mark_price"))
    if avg_cost > 0 and mark > 0:
        side = str(position.get("side", "LONG")).upper()
        raw_pct = ((mark - avg_cost) / avg_cost) * 100.0
        return raw_pct if side == "LONG" else -raw_pct
    return 0.0


def enforce_ibkr_take_profit_stop_loss(channel: str = "auto_take_profit") -> Optional[Dict[str, Any]]:
    """IBKR hisse pozisyonlarinda kar-al (IBKR_TAKE_PROFIT_PCT) ve zarar-kes
    (IBKR_STOP_LOSS_PCT) esiklerini kontrol eder, esik asilirsa pozisyonu piyasa
    emriyle kapatir. Onceden IBKR icin HICBIR otomatik kar-al/zarar-kes mekanizmasi
    yoktu - pozisyonlar sinirsiz acik kalabiliyordu."""
    if IBKR_TAKE_PROFIT_PCT <= 0 and IBKR_STOP_LOSS_PCT <= 0:
        return None
    if not bool(IBKR_RUNTIME.get("connected")):
        return None
    try:
        positions = ibkr_positions_snapshot()
    except Exception:
        return None
    for position in positions:
        qty = abs(safe_float(position.get("position") or position.get("size")))
        if qty <= 0:
            continue
        profit_pct = ibkr_position_profit_pct(position)
        hit_take_profit = IBKR_TAKE_PROFIT_PCT > 0 and profit_pct >= IBKR_TAKE_PROFIT_PCT
        hit_stop_loss = IBKR_STOP_LOSS_PCT > 0 and profit_pct <= -IBKR_STOP_LOSS_PCT
        if not hit_take_profit and not hit_stop_loss:
            continue
        symbol = str(position.get("symbol", "")).upper()
        if not symbol:
            continue
        side = str(position.get("side", "LONG")).upper()
        close_side = "SELL" if side == "LONG" else "BUY"
        asset_type = str(position.get("asset_type") or position.get("secType") or "STK").upper()
        exchange = str(position.get("exchange") or "SMART").upper()
        currency = str(position.get("currency") or "USD").upper()
        trigger = "take_profit_roi_pct" if hit_take_profit else "stop_loss_roi_pct"
        try:
            result = ibkr_place_market_order(
                symbol, close_side, qty, asset_type, exchange, currency,
                request_id=f"ibkr-{'tp' if hit_take_profit else 'sl'}-{symbol}-{int(time.time())}",
            )
        except Exception as e:
            result = {"simulated": False, "broker": "IBKR", "symbol": symbol, "error": str(e), "time": now_text()}
        result["trigger"] = trigger
        result["trigger_pct"] = round(profit_pct, 4)
        result["target_pct"] = IBKR_TAKE_PROFIT_PCT if hit_take_profit else -IBKR_STOP_LOSS_PCT
        result["symbol"] = symbol
        result["pnl"] = safe_float(position.get("pnl"))
        if not result.get("error"):
            entry_price = safe_float(position.get("avgCost") or position.get("entry_price"))
            exit_price = safe_float(position.get("mark_price"))
            pnl_amount = safe_float(position.get("pnl"))
            db_record_position_closure(
                broker="IBKR",
                symbol=symbol,
                side=side,
                qty=qty,
                entry_price=entry_price,
                exit_price=exit_price,
                realized_pnl=pnl_amount,
                realized_pnl_pct=profit_pct,
                close_reason="TAKE_PROFIT" if hit_take_profit else "STOP_LOSS",
                detail=(
                    f"%{IBKR_TAKE_PROFIT_PCT:.1f} kâr hedefi tetiklendi." if hit_take_profit
                    else f"%{IBKR_STOP_LOSS_PCT:.1f} zarar-kes tetiklendi."
                ),
            )
        return result
    return None


def get_futures_available_usdt() -> float:
    """Binance futures cuzdanindaki kullanilabilir (bosta bekleyen) USDT bakiyesini dondurur.
    Yeni pozisyon boyutlandirma (varlik basina %) bu deger uzerinden hesaplanir.
    Basarisiz olursa 0.0 doner; cagiran taraf bu durumda AUTO_TRADER.quantity'e (sabit miktar) geri duser."""
    try:
        data = signed_request("GET", FUTURES_BASE, "/fapi/v2/balance", {})
        for b in data:
            if str(b.get("asset", "")).upper() == "USDT":
                return safe_float(b.get("availableBalance"))
        return 0.0
    except Exception:
        return 0.0


def get_spot_available_usdt() -> float:
    """Binance spot cuzdanindaki bosta bekleyen (free) USDT miktarini dondurur.
    Spot auto-trader'in BUY pozisyon boyutlandirmasi bu deger uzerinden yapilir."""
    try:
        data = signed_request("GET", SPOT_BASE, "/api/v3/account", {})
        for b in data.get("balances", []):
            if str(b.get("asset", "")).upper() == "USDT":
                return safe_float(b.get("free"))
        return 0.0
    except Exception:
        return 0.0


def get_spot_asset_free_qty(asset: str) -> float:
    """Belirtilen varligin (ör. ETH, BTC - USDT'siz) spot cuzdanindaki bosta
    bekleyen miktarini dondurur. SELL islemi acmadan once elde ne kadar oldugunu
    kontrol etmek icin kullanilir (spot'ta short mumkun degil)."""
    try:
        data = signed_request("GET", SPOT_BASE, "/api/v3/account", {})
        for b in data.get("balances", []):
            if str(b.get("asset", "")).upper() == asset.upper():
                return safe_float(b.get("free"))
        return 0.0
    except Exception:
        return 0.0


def spot_auto_trader_size_pct(symbol: str) -> float:
    sym = normalize_symbol(symbol)
    if sym.startswith("BTC"):
        return SPOT_AUTO_SIZE_PCT_BTC
    if sym.startswith("ETH"):
        return SPOT_AUTO_SIZE_PCT_ETH
    return SPOT_AUTO_SIZE_PCT_DEFAULT


def place_spot_order(
    symbol: str,
    side: str,
    quantity: float,
    request_id: Optional[str] = None,
    channel: str = "auto_spot",
) -> Dict[str, Any]:
    """Binance SPOT piyasa emri gonderir (dogrudan imzali istek - futures'taki
    gibi VPS proxy'ye ihtiyac yok, cunku spot /api/v3/order Railway IP'sinden
    zaten dogrudan calisiyor - bkz. mevcut manuel spot emir yolu _resolve_place_order_market)."""
    request_id = str(request_id or uuid.uuid4())

    if quantity <= 0:
        return {"error": "Miktar 0'dan büyük olmalı.", "request_id": request_id, "simulated": False}

    if DAILY_REALIZED_PNL < MAX_DAILY_LOSS:
        error = f"Max daily loss exceeded. Current PnL: {DAILY_REALIZED_PNL} < {MAX_DAILY_LOSS}"
        db_insert_trade_journal(
            broker="Binance", channel=channel, symbol=symbol, side=side, quantity=quantity,
            status="REJECTED", simulated=False, payload={"reason": "max_daily_loss"},
            error_text=error, request_id=request_id,
        )
        return {"error": error, "request_id": request_id, "simulated": False}

    last_order_time = LAST_ORDER_TIME.get(f"SPOT_{symbol}", 0)
    if time.time() - last_order_time < MIN_ORDER_COOLDOWN_SEC:
        error = f"Order cooldown in effect for {symbol}. Min wait: {MIN_ORDER_COOLDOWN_SEC}s"
        return {"error": error, "request_id": request_id, "simulated": False}

    if request_id_seen(request_id):
        return {"error": "Request already seen (duplicate)", "request_id": request_id, "simulated": False}

    if not LIVE_TRADING:
        simulated = {
            "simulated": True,
            "message": "LIVE_TRADING=false olduğu için gerçek emir gönderilmedi.",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "time": now_text(),
            "request_id": request_id,
        }
        db_insert_trade_journal(
            broker="Binance", channel=channel, symbol=symbol, side=side, quantity=quantity,
            status="SIMULATED", simulated=True, payload=simulated, request_id=request_id,
        )
        TRADE_LOG.insert(0, simulated)
        return simulated

    try:
        params = {"symbol": symbol, "side": side, "type": "MARKET", "quantity": quantity}
        data = signed_request("POST", SPOT_BASE, "/api/v3/order", params)
        result = dict(data) if isinstance(data, dict) else {"raw": data}
        result["simulated"] = False
        result["request_id"] = request_id
        db_insert_trade_journal(
            broker="Binance", channel=channel, symbol=symbol, side=side, quantity=quantity,
            status="FILLED", simulated=False, payload=result, request_id=request_id,
        )
        TRADE_LOG.insert(0, {"simulated": False, "time": now_text(), "order": result, "request_id": request_id})
        LAST_ORDER_TIME[f"SPOT_{symbol}"] = time.time()
        return result
    except Exception as e:
        error = str(e)
        db_insert_trade_journal(
            broker="Binance", channel=channel, symbol=symbol, side=side, quantity=quantity,
            status="ERROR", simulated=False, payload={}, error_text=error, request_id=request_id,
        )
        return {"error": error, "request_id": request_id, "simulated": False}


def spot_position_profit_pct(position: Dict[str, Any], current_price: float) -> float:
    avg_cost = safe_float(position.get("avg_cost"))
    if avg_cost <= 0 or current_price <= 0:
        return 0.0
    return ((current_price - avg_cost) / avg_cost) * 100.0


def enforce_spot_take_profit_stop_loss(channel: str = "auto_take_profit") -> Optional[Dict[str, Any]]:
    """Takip edilen spot pozisyonlarda (biz kendi acilislarimizi izliyoruz -
    spot_positions tablosu) kar-al/zarar-kes esiklerini kontrol eder, esik
    asilirsa piyasa emriyle satar (short yok, sadece elimizdeki miktar kadar)."""
    if BINANCE_TAKE_PROFIT_PCT <= 0 and BINANCE_STOP_LOSS_PCT <= 0:
        return None
    try:
        positions = db_list_spot_positions()
    except Exception:
        return None
    for pos in positions:
        symbol = str(pos.get("symbol", "")).upper()
        qty = safe_float(pos.get("quantity"))
        if not symbol or qty <= 0:
            continue
        try:
            snap = get_market_snapshot(symbol, "SPOT")
            price = safe_float(snap.get("price"))
        except Exception:
            continue
        if price <= 0:
            continue
        profit_pct = spot_position_profit_pct(pos, price)
        hit_take_profit = BINANCE_TAKE_PROFIT_PCT > 0 and profit_pct >= BINANCE_TAKE_PROFIT_PCT
        hit_stop_loss = BINANCE_STOP_LOSS_PCT > 0 and profit_pct <= -BINANCE_STOP_LOSS_PCT
        if not hit_take_profit and not hit_stop_loss:
            continue
        asset = symbol.replace("USDT", "")
        free_qty = get_spot_asset_free_qty(asset)
        sell_qty = min(qty, free_qty) if free_qty > 0 else qty
        if sell_qty <= 0:
            continue
        trigger = "take_profit_roi_pct" if hit_take_profit else "stop_loss_roi_pct"
        result = place_spot_order(
            symbol, "SELL", sell_qty,
            request_id=f"spot-{'tp' if hit_take_profit else 'sl'}-{symbol}-{int(time.time())}",
            channel=channel,
        )
        if not result.get("error"):
            db_delete_spot_position(symbol)
        result["trigger"] = trigger
        result["trigger_pct"] = round(profit_pct, 4)
        result["target_pct"] = BINANCE_TAKE_PROFIT_PCT if hit_take_profit else -BINANCE_STOP_LOSS_PCT
        result["symbol"] = symbol
        if not result.get("error"):
            avg_cost = safe_float(pos.get("avg_cost"))
            pnl_amount = (price - avg_cost) * sell_qty
            result["pnl"] = pnl_amount
            db_record_position_closure(
                broker="BINANCE_SPOT",
                symbol=symbol,
                side="LONG",
                qty=sell_qty,
                entry_price=avg_cost,
                exit_price=price,
                realized_pnl=pnl_amount,
                realized_pnl_pct=profit_pct,
                close_reason="TAKE_PROFIT" if hit_take_profit else "STOP_LOSS",
                detail=(
                    f"%{BINANCE_TAKE_PROFIT_PCT:.1f} kâr hedefi tetiklendi." if hit_take_profit
                    else f"%{BINANCE_STOP_LOSS_PCT:.1f} zarar-kes tetiklendi."
                ),
            )
        return result
    return None


_LEVERAGE_APPLIED_CACHE: Dict[str, int] = {}
_LEVERAGE_LOCK = threading.Lock()


def ensure_binance_leverage(symbol: str, leverage: int) -> None:
    """Binance futures'ta ilgili sembol icin istenen kaldiraci ayarlar (POST /fapi/v1/leverage).
    Ayni deger zaten uygulanmissa (bu process icinde) tekrar cagirmaz. Hata durumunda
    sessizce gecer; asil emir Binance'in kendi hata mesajiyla (yetersiz kaldirac vb.)
    reddedilirse bu execution.error olarak zaten raporlanir."""
    if leverage <= 1:
        return
    with _LEVERAGE_LOCK:
        if _LEVERAGE_APPLIED_CACHE.get(symbol) == leverage:
            return
    try:
        signed_request("POST", FUTURES_BASE, "/fapi/v1/leverage", {"symbol": symbol, "leverage": leverage})
        with _LEVERAGE_LOCK:
            _LEVERAGE_APPLIED_CACHE[symbol] = leverage
    except Exception:
        pass


_USDTRY_RATE_CACHE: Dict[str, Any] = {"rate": 0.0, "ts": 0.0}
_USDTRY_RATE_CACHE_TTL_SEC = 30.0


def get_live_usdtry_rate() -> float:
    """Binance'in kendi USDT/TRY paritesinden canli kur ceker (public endpoint,
    IP whitelist gerektirmez). VPS proxy'sinin hesap ozetindeki TRY donusumu
    eski/sabit bir kur kullaniyordu ve gercek bakiyeden belirgin sekilde
    (~%5-10) dusuk gosteriyordu."""
    cached_ts = _USDTRY_RATE_CACHE.get("ts", 0.0)
    if cached_ts and (time.time() - cached_ts) < _USDTRY_RATE_CACHE_TTL_SEC:
        return _USDTRY_RATE_CACHE.get("rate", 0.0)
    try:
        rate = get_price("USDTTRY", "SPOT")
        if rate > 0:
            _USDTRY_RATE_CACHE["rate"] = rate
            _USDTRY_RATE_CACHE["ts"] = time.time()
            return rate
    except Exception:
        pass
    return _USDTRY_RATE_CACHE.get("rate", 0.0)


def get_binance_try_totals_live() -> Optional[Dict[str, float]]:
    """Spot ve futures bakiyelerini VPS proxy'sinin HAM (TRY'ye cevrilmemis)
    endpoint'lerinden ceker, her varligi canli fiyatla USD'ye cevirir ve
    canli USDT/TRY kuruyla TRY'ye donusturur. VPS'in kendi hesap-ozeti
    endpoint'i (build_binance_summary/get_spot_balances icinde kullanilan)
    eski bir kur kullandigi icin gercek bakiyeden dusuk gosteriyordu; bu
    fonksiyon dogru toplami bagimsiz olarak hesaplar ve mumkunse onun
    yerine kullanilir."""
    if not BINANCE_PROXY_BASE_URL:
        return None
    try:
        rate = get_live_usdtry_rate()
        if rate <= 0:
            return None
        spot_raw = _binance_proxy_request("GET", "/spot-balances")
        futures_raw = _binance_proxy_request("GET", "/futures-balances")
        spot_rows = spot_raw.get("balances", []) if isinstance(spot_raw, dict) else (spot_raw or [])
        futures_rows = futures_raw.get("balances", []) if isinstance(futures_raw, dict) else (futures_raw or [])
        spot_rows = _enrich_balances_with_usd(spot_rows, "SPOT")
        futures_rows = _enrich_balances_with_usd(futures_rows, "FUTURES")
        spot_usd = sum(safe_float(r.get("usdValue")) for r in spot_rows if isinstance(r, dict))
        futures_usd = sum(safe_float(r.get("usdValue")) for r in futures_rows if isinstance(r, dict))
        return {
            "spot_try": round(spot_usd * rate, 2),
            "futures_try": round(futures_usd * rate, 2),
            "total_try": round((spot_usd + futures_usd) * rate, 2),
            "usdtry_rate": rate,
        }
    except Exception:
        return None


def get_spot_balances() -> List[Dict[str, Any]]:
    if BINANCE_PROXY_BASE_URL:
        # VPS proxy /portfolio endpoint döndürüyor {"data": {"spotTry": ..., ...}, "ok": true}
        # Bundan spot balances generate etmeli
        try:
            legacy = _binance_proxy_portfolio_payload()
            rows = _proxy_extract_balances_from_portfolio(legacy)
            if rows:
                return rows
            rows2 = _proxy_extract_balances_from_legacy_portfolio(legacy)
            if rows2:
                return rows2
            # Fallback: /portfolio'dan "spotTry" verisinden synthetic balance oluştur
            spot_try = safe_float(legacy.get("data", {}).get("spotTry", 0.0))
            if spot_try > 0:
                return [{"asset": "USDT", "free": spot_try, "locked": 0, "total": spot_try}]
            raise RuntimeError("Proxy /portfolio içinde spot balance verisi bulunamadı.")
        except Exception as proxy_err:
            pass
    try:
        account = signed_request("GET", SPOT_BASE, "/api/v3/account", {})
        balances = []
        for b in account.get("balances", []):
            free = safe_float(b.get("free"))
            locked = safe_float(b.get("locked"))
            total = free + locked
            if total <= 0:
                continue
            asset = b.get("asset", "")
            balances.append({"asset": asset, "free": free, "locked": locked, "total": total})
        return balances
    except Exception as e:
        return [{"asset": "HATA", "free": 0, "locked": 0, "total": 0, "error": str(e)}]


def build_binance_summary(spot_balances: List[Dict[str, Any]], futures_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "currency": "USD_ESTIMATE",
        "spot_total": 0.0,
        "futures_total": 0.0,
        "binance_total": 0.0,
        "unrealized_pnl": 0.0,
    }
    if any(str(x.get("asset")) == "BINANCE_TRY_TOTAL" for x in spot_balances):
        summary["currency"] = "TRY_EQUIV"
        summary["spot_total"] = safe_float(next((x.get("total") for x in spot_balances if str(x.get("asset")) == "SPOT_TRY_EQUIV"), 0.0))
        summary["futures_total"] = safe_float(next((x.get("total") for x in spot_balances if str(x.get("asset")) == "FUTURES_TRY_EQUIV"), 0.0))
        summary["binance_total"] = safe_float(next((x.get("total") for x in spot_balances if str(x.get("asset")) == "BINANCE_TRY_TOTAL"), 0.0))
    else:
        spot_usd = 0.0
        for x in spot_balances:
            asset = str(x.get("asset", "")).upper()
            total = safe_float(x.get("total"))
            if asset in {"USDT", "USDC", "BUSD", "FDUSD"}:
                spot_usd += total
        futures_notional = sum(abs(safe_float(x.get("mark_price")) * safe_float(x.get("size"))) for x in futures_positions if x.get("symbol") != "HATA")
        summary["spot_total"] = round(spot_usd, 4)
        summary["futures_total"] = round(futures_notional, 4)
        summary["binance_total"] = round(spot_usd + futures_notional, 4)
    summary["unrealized_pnl"] = round(sum(safe_float(x.get("pnl")) for x in futures_positions if x.get("symbol") != "HATA"), 4)
    return summary


def get_ibkr_try_from_proxy() -> float:
    """VPS proxy'nin /account-summary endpoint'i gercek IBKR net likidasyon degerini
    (TRY'ye cevrilmis) zaten hesaplayip donduruyor. Railway'den IBKR'a dogrudan
    soket baglantisi kurulamadigi icin (circuit breaker acik) bu deger fallback
    olarak kullanilir."""
    if not BINANCE_PROXY_BASE_URL:
        return 0.0
    try:
        legacy = _binance_proxy_portfolio_payload()
        return safe_float(legacy.get("data", {}).get("ibkrTry", 0.0))
    except Exception:
        return 0.0


def get_portfolio() -> Dict[str, Any]:
    # Try cache first (60 second TTL)
    cached = get_cached_portfolio()
    if cached:
        return cached
    
    spot = get_spot_balances()
    futures_positions = get_futures_positions()
    total_unrealized_pnl = sum(safe_float(p.get("pnl")) for p in futures_positions if p.get("symbol") != "HATA")
    binance_summary = build_binance_summary(spot, futures_positions)
    ibkr_positions: List[Dict[str, Any]] = []
    ibkr_error = ""
    ibkr_connected = bool(IBKR_RUNTIME.get("connected"))
    ibkr_try = 0.0
    if IBKR_ENABLED:
        if ibkr_connected:
            try:
                ibkr_positions = ibkr_positions_snapshot()
            except Exception as e:
                ibkr_error = str(e)
            # IBKR dogrudan bagliyken de NetLiquidation degerini TRY'ye cevirip
            # portfoy toplamina dahil et. Onceden bu deger sadece proxy fallback
            # yolunda (ibkr baglanti YOKSA) hesaplaniyordu; dogrudan baglantida
            # ibkr_try hep 0 kaliyordu ve toplam bakiyeden IBKR hesabinin tamami
            # (~binlerce TRY) eksik gorunuyordu.
            try:
                acct_rows = ibkr_account_summary_snapshot()
                net_liq_usd = safe_float(next(
                    (r.get("value") for r in acct_rows if str(r.get("tag")) == "NetLiquidation" and str(r.get("currency")) in ("USD", "BASE")),
                    0.0,
                ))
                if net_liq_usd <= 0:
                    net_liq_usd = safe_float(next(
                        (r.get("value") for r in acct_rows if str(r.get("tag")) == "NetLiquidation"),
                        0.0,
                    ))
                if net_liq_usd > 0:
                    rate = get_live_usdtry_rate() or 0.0
                    if rate > 0:
                        ibkr_try = net_liq_usd * rate
            except Exception:
                pass
        else:
            ibkr_error = str(IBKR_RUNTIME.get("last_error", "") or "IBKR bağlı değil.")
            # Dogrudan IBKR baglantisi yoksa (Railway -> IBKR Gateway soket erisimi
            # calismiyorsa), VPS proxy'sinden gercek IBKR bakiyesini almayi dene.
            ibkr_try = get_ibkr_try_from_proxy()
    spot_try = safe_float(next((x.get("total") for x in spot if str(x.get("asset")) == "SPOT_TRY_EQUIV"), 0.0))
    futures_try = safe_float(next((x.get("total") for x in spot if str(x.get("asset")) == "FUTURES_TRY_EQUIV"), 0.0))
    total_try = safe_float(next((x.get("total") for x in spot if str(x.get("asset")) == "BINANCE_TRY_TOTAL"), 0.0))
    if total_try <= 0 and safe_float(binance_summary.get("binance_total")) > 0:
        total_try = safe_float(binance_summary.get("binance_total"))
        spot_try = safe_float(binance_summary.get("spot_total"))
        futures_try = safe_float(binance_summary.get("futures_total"))

    # VPS proxy'nin hesap-ozeti eski/sabit bir USD/TRY kuru kullandigi icin
    # gercek bakiyeden belirgin sekilde dusuk gosterebiliyor (kullanicinin
    # kendi Binance uygulamasindaki gercek bakiyeyle karsilastirmasi bunu
    # dogruladi). Mumkunse canli kurla hesaplanan dogru toplami kullan.
    live_totals = get_binance_try_totals_live()
    if live_totals and live_totals.get("total_try", 0.0) > 0:
        total_try = live_totals["total_try"]
        spot_try = live_totals["spot_try"]
        futures_try = live_totals["futures_try"]
        binance_summary["binance_total"] = total_try
        binance_summary["spot_total"] = spot_try
        binance_summary["futures_total"] = futures_try
        binance_summary["currency"] = "TRY_EQUIV_LIVE"
        binance_summary["usdtry_rate"] = live_totals.get("usdtry_rate")
    
    result = {
        "last_update": now_text(),
        "live_trading": LIVE_TRADING,
        "spot_balances": spot,
        "futures_positions": futures_positions,
        "binance_summary": binance_summary,
        # Legacy mobile clients read these fields directly from /portfolio.
        "data": {
            "binanceTry": round(total_try, 2),
            "totalTry": round(total_try + ibkr_try, 2),
            "spotTry": round(spot_try, 2),
            "futuresTry": round(futures_try, 2),
            "cashTry": 0.0,
            "fundingTry": 0.0,
            "goldFxTry": 0.0,
            "ibkrTry": round(ibkr_try, 2),
        },
        "ibkr_positions": ibkr_positions,
        "ibkr_connected": ibkr_connected,
        "ibkr_error": ibkr_error,
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
    }
    
    # Cache the result if successful
    if not any("error" in str(x).lower() for x in [spot, futures_positions]):
        set_cached_portfolio(result)

    try:
        db_record_balance_snapshot(total_try + ibkr_try, total_try, ibkr_try)
    except Exception:
        pass

    return result


def calculate_ai_signal(symbol: str, market: str) -> Dict[str, Any]:
    market = market.upper()
    snapshot = get_market_snapshot(symbol, market)
    price = safe_float(snapshot.get("price"))
    change = safe_float(snapshot.get("change_24h"))
    volume = safe_float(snapshot.get("quote_volume"))
    pressure = snapshot.get("orderbook", synthetic_orderbook(change, str(snapshot.get("source", "fallback"))))

    buy_pressure = pressure["buy_pressure"]
    sell_pressure = pressure["sell_pressure"]

    signal = "WAIT"
    confidence = 50
    reasons = []

    if change > 2.0 and buy_pressure > 58:
        signal = "BUY"
        confidence = min(90, int(60 + change * 3 + (buy_pressure - 50) * 0.6))
        reasons.append("Pozitif momentum ve alış baskısı aynı yönde.")
    elif change < -2.0 and sell_pressure > 58:
        signal = "SELL"
        confidence = min(90, int(60 + abs(change) * 3 + (sell_pressure - 50) * 0.6))
        reasons.append("Negatif momentum ve satış baskısı aynı yönde.")
    elif abs(change) >= 6:
        signal = "WAIT"
        confidence = 68
        reasons.append("Aşırı volatilite var; acele işlem yerine teyit beklenmeli.")
    elif buy_pressure > 65:
        signal = "WATCH_BUY"
        confidence = 63
        reasons.append("Emir defterinde alış baskısı var ama trend teyidi zayıf.")
    elif sell_pressure > 65:
        signal = "WATCH_SELL"
        confidence = 63
        reasons.append("Emir defterinde satış baskısı var ama trend teyidi zayıf.")
    else:
        reasons.append("Net yön yok; manuel işlemde temkinli kalınmalı.")
    if snapshot.get("source") != "binance":
        reasons.append(f"Piyasa verisi {snapshot.get('source')} kaynağından alındı.")

    # Mevcut açık pozisyon kontrolü: aynı yönde yığılmayı engellemek için bilgi ekler.
    open_positions = get_futures_positions() if market == "FUTURES" else []
    same_symbol_positions = [p for p in open_positions if p.get("symbol") == symbol]
    if same_symbol_positions:
        reasons.append("Bu sembolde açık futures pozisyon var; yeni işlemden önce mevcut risk kontrol edilmeli.")
        if signal in ["BUY", "SELL"]:
            confidence = max(50, confidence - 10)

    result = {
        "symbol": symbol,
        "market": market,
        "price": round(price, 6),
        "change_24h": round(change, 2),
        "quote_volume": round(volume, 2),
        "orderbook": pressure,
        "data_source": snapshot.get("source", "binance"),
        "signal": signal,
        "confidence": confidence,
        "reason": " ".join(reasons),
        "last_update": now_text(),
        "engine_enabled": ENGINE.enabled,
    }

    with state_lock:
        ENGINE.last_update = result["last_update"]
        ENGINE.last_symbol = symbol
        ENGINE.last_market = market
        ENGINE.last_signal = signal
        ENGINE.confidence = confidence
        ENGINE.reason = result["reason"]

    return result


def place_futures_order(
    symbol: str,
    side: str,
    quantity: float,
    reduce_only: bool = False,
    order_type: str = "MARKET",
    request_id: Optional[str] = None,
    channel: str = "auto",
    use_proxy: bool = True,
) -> Dict[str, Any]:
    request_id = str(request_id or uuid.uuid4())
    
    # Risk check: max daily loss
    if DAILY_REALIZED_PNL < MAX_DAILY_LOSS:
        error = f"Max daily loss exceeded. Current PnL: {DAILY_REALIZED_PNL} < {MAX_DAILY_LOSS}"
        db_insert_trade_journal(
            broker="Binance",
            channel=channel,
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="REJECTED",
            simulated=False,
            payload={"reason": "max_daily_loss"},
            error_text=error,
            request_id=request_id,
        )
        return {"error": error, "request_id": request_id, "simulated": False}
    
    if not reduce_only:
        # Risk check: cooldown
        last_order_time = LAST_ORDER_TIME.get(symbol, 0)
        if time.time() - last_order_time < MIN_ORDER_COOLDOWN_SEC:
            error = f"Order cooldown in effect for {symbol}. Min wait: {MIN_ORDER_COOLDOWN_SEC}s"
            db_insert_trade_journal(
                broker="Binance",
                channel=channel,
                symbol=symbol,
                side=side,
                quantity=quantity,
                status="REJECTED",
                simulated=False,
                payload={"reason": "cooldown"},
                error_text=error,
                request_id=request_id,
            )
            return {"error": error, "request_id": request_id, "simulated": False}

        # Risk check: max concurrent symbols
        if MAX_CONCURRENT_POSITIONS > 0:
            open_positions = [
                p for p in get_futures_positions()
                if p.get("id") != "error" and p.get("symbol")
            ]
            open_symbols = {str(p.get("symbol")) for p in open_positions}
            if symbol not in open_symbols and len(open_symbols) >= MAX_CONCURRENT_POSITIONS:
                error = (
                    f"Max concurrent position limit reached ({len(open_symbols)}/{MAX_CONCURRENT_POSITIONS}). "
                    f"New symbol {symbol} cannot be opened."
                )
                db_insert_trade_journal(
                    broker="Binance",
                    channel=channel,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    status="REJECTED",
                    simulated=False,
                    payload={"reason": "max_concurrent_positions", "open_symbols": sorted(open_symbols)},
                    error_text=error,
                    request_id=request_id,
                )
                return {"error": error, "request_id": request_id, "simulated": False}
    
    # Dedup check
    if request_id_seen(request_id):
        error = "Request already seen (duplicate)"
        return {"error": error, "request_id": request_id, "simulated": False}
    
    if not LIVE_TRADING:
        simulated = {
            "simulated": True,
            "message": "LIVE_TRADING=false olduğu için gerçek emir gönderilmedi.",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "time": now_text(),
            "request_id": request_id,
        }
        db_insert_trade_journal(
            broker="Binance",
            channel=channel,
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="SIMULATED",
            simulated=True,
            payload=simulated,
            request_id=request_id,
        )
        TRADE_LOG.insert(0, simulated)
        return simulated

    if BINANCE_ORDER_PROXY_BASE_URL and use_proxy:
        payload = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "reduce_only": reduce_only,
            "order_type": order_type,
            "request_id": request_id,
            "channel": channel,
        }
        try:
            data = _binance_proxy_request("POST", "/binance/private/order", json_body=payload, base_url=BINANCE_ORDER_PROXY_BASE_URL)
            result = dict(data.get("result", data))
            result.setdefault("request_id", request_id)
            db_insert_trade_journal(
                broker="Binance",
                channel=channel,
                symbol=symbol,
                side=side,
                quantity=quantity,
                status=str(result.get("status") or "SENT"),
                simulated=False,
                payload=result,
                request_id=request_id,
            )
            TRADE_LOG.insert(0, {"simulated": False, "time": now_text(), "order": result, "request_id": request_id})
            LAST_ORDER_TIME[symbol] = time.time()
            return result
        except Exception as e1:
            try:
                if reduce_only:
                    legacy_close = _binance_proxy_request(
                        "POST",
                        "/close-position",
                        json_body={
                            "symbol": symbol,
                            "request_id": request_id,
                        },
                        base_url=BINANCE_ORDER_PROXY_BASE_URL,
                    )
                    result = dict(legacy_close)
                    result.setdefault("request_id", request_id)
                    db_insert_trade_journal(
                        broker="Binance",
                        channel=channel,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        status=str(result.get("status") or ("FAILED" if result.get("error") else "SENT")),
                        simulated=bool(result.get("simulated", False)),
                        payload=result,
                        error_text=str(result.get("error", "")),
                        request_id=request_id,
                    )
                    if result.get("error"):
                        raise RuntimeError(str(result.get("error")))
                    TRADE_LOG.insert(0, {"simulated": bool(result.get("simulated", False)), "time": now_text(), "order": result, "request_id": request_id})
                    LAST_ORDER_TIME[symbol] = time.time()
                    return result
                legacy = _binance_proxy_request(
                    "POST",
                    "/manual-order",
                    json_body={
                        "symbol": symbol,
                        "side": side.upper(),
                        "quantity": quantity,
                        "reduceOnly": reduce_only,
                        "request_id": request_id,
                    },
                    base_url=BINANCE_ORDER_PROXY_BASE_URL,
                )
                result = dict(legacy)
                result.setdefault("request_id", request_id)
                db_insert_trade_journal(
                    broker="Binance",
                    channel=channel,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    status=str(result.get("status") or ("FAILED" if result.get("error") else "SENT")),
                    simulated=bool(result.get("simulated", False)),
                    payload=result,
                    error_text=str(result.get("error", "")),
                    request_id=request_id,
                )
                if result.get("error"):
                    raise RuntimeError(str(result.get("error")))
                TRADE_LOG.insert(0, {"simulated": bool(result.get("simulated", False)), "time": now_text(), "order": result, "request_id": request_id})
                LAST_ORDER_TIME[symbol] = time.time()
                return result
            except Exception as e2:
                db_insert_trade_journal(
                    broker="Binance",
                    channel=channel,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    status="FAILED",
                    simulated=False,
                    payload={},
                    error_text=f"{e1} | legacy: {e2}",
                    request_id=request_id,
                )
                raise RuntimeError(f"Proxy order başarısız: {e1} | legacy: {e2}") from e2

    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
        "reduceOnly": "true" if reduce_only else "false",
    }
    try:
        data = signed_request("POST", FUTURES_BASE, "/fapi/v1/order", params)
        log = {"simulated": False, "time": now_text(), "order": data, "request_id": request_id}
        db_insert_trade_journal(
            broker="Binance",
            channel=channel,
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="SENT",
            simulated=False,
            payload=data,
            request_id=request_id,
        )
        TRADE_LOG.insert(0, log)
        LAST_ORDER_TIME[symbol] = time.time()
        return log
    except Exception as e:
        db_insert_trade_journal(
            broker="Binance",
            channel=channel,
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="FAILED",
            simulated=False,
            payload={},
            error_text=str(e),
            request_id=request_id,
        )
        raise


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "app": APP_NAME,
        "ok": True,
        "time": now_text(),
        "live_trading": LIVE_TRADING,
        "api_key_loaded": bool(BINANCE_API_KEY),
        "binance_proxy_mode": bool(BINANCE_PROXY_BASE_URL),
        "binance_proxy_base_url": BINANCE_PROXY_BASE_URL,
        "ibkr_enabled": IBKR_ENABLED,
        "ibkr_connected": bool(IBKR_RUNTIME.get("connected")),
        "auto_trader_enabled": AUTO_TRADER.enabled,
    })


@app.route("/ibkr/health", methods=["GET"])
def ibkr_health():
    # NOT: burada canli bir ibkr_ping() cagrisi YAPMIYORUZ. ib_insync'in IB client'i
    # hangi thread'in event loop'unda connect edildiyse ona bagli kaliyor; bu endpoint'i
    # farkli bir gunicorn istek thread'inden tetiklemek, keepalive arka plan thread'i ile
    # cakisip gunicorn worker'ini timeout ile cokertebiliyordu. Bunun yerine keepalive
    # dongusunun zaten surekli guncelledigi IBKR_RUNTIME onbellegini donduruyoruz;
    # gercek zamanli olarak ayni bilgiyi, worker'i riske atmadan saglar.
    with IBKR_LOCK:
        connected = bool(IBKR_RUNTIME.get("connected"))
        last_ok = IBKR_RUNTIME.get("last_ok", "")
        last_error = IBKR_RUNTIME.get("last_error", "")
        last_real_error = IBKR_RUNTIME.get("last_real_error", "")
        last_real_error_time = IBKR_RUNTIME.get("last_real_error_time", "")
        reconnect_count = int(IBKR_RUNTIME.get("reconnect_count", 0))
        failed_attempts = int(IBKR_RUNTIME.get("failed_attempts", 0))
        circuit_breaker_open = bool(IBKR_RUNTIME.get("circuit_breaker_open"))
    payload = {
        "ok": connected,
        "broker": "IBKR",
        "host": IBKR_HOST,
        "port": IBKR_PORT,
        "client_id": IBKR_CLIENT_ID,
        "account": IBKR_ACCOUNT,
        "connected": connected,
        "last_ok": last_ok,
        "last_error": last_error,
        "last_real_error": last_real_error,
        "last_real_error_time": last_real_error_time,
        "reconnect_count": reconnect_count,
        "failed_attempts": failed_attempts,
        "circuit_breaker_open": circuit_breaker_open,
        "time": now_text(),
    }
    return jsonify(payload), (200 if connected else 503)


@app.route("/symbols", methods=["GET"])
def symbols():
    market = request.args.get("market", "FUTURES").upper()
    try:
        base = FUTURES_BASE if market == "FUTURES" else SPOT_BASE
        path = "/fapi/v1/exchangeInfo" if market == "FUTURES" else "/api/v3/exchangeInfo"
        data = public_get(base, path)
        rows = []
        for s in data.get("symbols", []):
            symbol = s.get("symbol", "")
            status = s.get("status", "")
            quote = s.get("quoteAsset", "")
            if status in ["TRADING"] and quote == "USDT":
                rows.append(symbol)
        return jsonify({"market": market, "symbols": rows[:500], "last_update": now_text()})
    except Exception as e:
        return jsonify({"market": market, "symbols": DEFAULT_SYMBOLS, "error": str(e), "last_update": now_text()}), 200


def get_personal_cash_flow() -> Dict[str, Any]:
    """Piyasa geneli 'net para akışı' göstergesinden (MarketFlowRisk) farklı olarak,
    kullanıcının KENDİ hesabındaki (Binance + IBKR toplamı) gerçek değer değişimini
    hesaplar. balance_snapshots tablosuna periyodik kaydedilen anlık görüntülerle
    şimdiki değeri karşılaştırır."""
    current = get_cached_portfolio() or get_portfolio()
    current_total = safe_float((current.get("data") or {}).get("totalTry"))

    def _delta(hours: float) -> Dict[str, Any]:
        snap = db_closest_balance_snapshot(hours)
        if not snap or current_total <= 0:
            return {"available": False, "change_try": 0.0, "change_pct": 0.0, "from_time": None}
        prev_total = safe_float(snap.get("total_try"))
        if prev_total <= 0:
            return {"available": False, "change_try": 0.0, "change_pct": 0.0, "from_time": snap.get("created_at")}
        change_try = current_total - prev_total
        change_pct = (change_try / prev_total) * 100.0
        return {
            "available": True,
            "change_try": round(change_try, 2),
            "change_pct": round(change_pct, 2),
            "from_total_try": round(prev_total, 2),
            "from_time": snap.get("created_at"),
        }

    return {
        "ok": True,
        "current_total_try": round(current_total, 2),
        "today_24h": _delta(24),
        "week_7d": _delta(24 * 7),
        "month_30d": _delta(24 * 30),
        "note": (
            "Bu bölüm piyasa geneli para akışından farklıdır; SİZİN Binance+IBKR "
            "hesabınızın toplam TRY değerindeki gerçek değişimi (yatırım/çekim + "
            "kâr-zarar dahil net etki) gösterir."
        ),
        "time": now_text(),
    }


@app.route("/daily-investment-advice", methods=["GET"])
def daily_investment_advice_endpoint():
    """Günlük yatırım tavsiyesi: tüm profesyonel analiz motorlarını (balon/çöküş
    riski, defter değeri, bilanço sağlığı, manipülasyon, sektör senaryoları)
    günde 1 kez tarayıp kısa, aksiyona dönük Türkçe bir özet döner."""
    try:
        return jsonify(get_daily_investment_advice())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "summary": "", "notes": [], "time": now_text()}), 200


@app.route("/personal-cash-flow", methods=["GET"])
def personal_cash_flow_endpoint():
    """Kişisel hesap net para akışı: MarketsView'deki piyasa geneli akıştan farklı
    olarak kullanıcının kendi Binance+IBKR toplam bakiyesindeki 24s/7g/30g gerçek
    değişimi döner (önceden bu veri hiç yoktu, sadece piyasa geneli gösteriliyordu)."""
    try:
        return jsonify(get_personal_cash_flow())
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "current_total_try": 0.0, "time": now_text()}), 200


@app.route("/portfolio", methods=["GET"])
def portfolio():
    return jsonify(get_portfolio())


@app.route("/positions", methods=["GET"])
def positions():
    return jsonify({"positions": get_futures_positions(), "last_update": now_text()})


@app.route("/binance/health", methods=["GET"])
def binance_health():
    return jsonify({
        "ok": True,
        "proxy_mode": bool(BINANCE_PROXY_BASE_URL),
        "proxy_base_url": BINANCE_PROXY_BASE_URL,
        "proxy_token_set": bool(BINANCE_PROXY_TOKEN),
        "last_update": now_text(),
    })


@app.route("/binance/private/spot-balances", methods=["GET"])
def binance_private_spot_balances():
    if BINANCE_PROXY_TOKEN and request.headers.get("X-Binance-Proxy-Token", "") != BINANCE_PROXY_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        balances = []
        account = signed_request("GET", SPOT_BASE, "/api/v3/account", {})
        for b in account.get("balances", []):
            free = safe_float(b.get("free"))
            locked = safe_float(b.get("locked"))
            total = free + locked
            if total <= 0:
                continue
            balances.append({"asset": b.get("asset", ""), "free": free, "locked": locked, "total": total})
        return jsonify({"ok": True, "balances": balances, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "balances": [{"asset": "HATA", "free": 0, "locked": 0, "total": 0, "error": str(e)}], "error": str(e), "last_update": now_text()}), 500


@app.route("/binance/private/futures-positions", methods=["GET"])
def binance_private_futures_positions():
    if BINANCE_PROXY_TOKEN and request.headers.get("X-Binance-Proxy-Token", "") != BINANCE_PROXY_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    try:
        positions = []
        data = signed_request("GET", FUTURES_BASE, "/fapi/v2/positionRisk", {})
        for p in data:
            amt = safe_float(p.get("positionAmt"))
            if abs(amt) <= 0:
                continue
            entry = safe_float(p.get("entryPrice"))
            mark = safe_float(p.get("markPrice"))
            pnl = safe_float(p.get("unRealizedProfit"))
            side = "LONG" if amt > 0 else "SHORT"
            positions.append({
                "id": f"BINANCE-FUTURES-{p.get('symbol')}",
                "broker": "Binance",
                "market": "Futures",
                "symbol": p.get("symbol", ""),
                "side": side,
                "size": abs(amt),
                "entry_price": entry,
                "mark_price": mark,
                "pnl": pnl,
                "leverage": p.get("leverage", ""),
            })
        return jsonify({"ok": True, "positions": positions, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "positions": [{"id": "error", "broker": "Binance", "market": "Futures", "symbol": "HATA", "side": "-", "size": 0, "entry_price": 0, "mark_price": 0, "pnl": 0, "error": str(e)}], "error": str(e), "last_update": now_text()}), 500


@app.route("/binance/private/order", methods=["POST"])
def binance_private_order():
    if BINANCE_PROXY_TOKEN and request.headers.get("X-Binance-Proxy-Token", "") != BINANCE_PROXY_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    body = request.get_json(force=True) or {}
    try:
        result = place_futures_order(
            str(body.get("symbol", "ETHUSDT")).upper().replace("/", ""),
            str(body.get("side", "BUY")).upper(),
            safe_float(body.get("quantity"), 0),
            reduce_only=safe_bool(body.get("reduce_only", False)),
            order_type=str(body.get("order_type", "MARKET")),
            request_id=str(body.get("request_id") or uuid.uuid4()),
            channel=str(body.get("channel", "proxy")),
            use_proxy=False,
        )
        code = 200 if not result.get("error") else 400
        return jsonify({"ok": code == 200, "result": result, "last_update": now_text()}), code
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "last_update": now_text()}), 500


@app.route("/ibkr/positions", methods=["GET"])
def ibkr_positions():
    try:
        rows = ibkr_positions_snapshot()
        return jsonify({"ok": True, "positions": rows, "data": rows, "last_update": now_text(), "broker": "IBKR"})
    except Exception as e:
        return jsonify({"ok": False, "positions": [], "data": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 500


@app.route("/ibkr-positions", methods=["GET"])
def ibkr_positions_alias():
    # Mobil uygulama bu path'i cagiriyor; /ibkr/positions ile ayni veriyi dondurur.
    # NOT: iOS tarafi (TradingCenterView.loadIBKRPositions) yanitta "ok": true alanini
    # zorunlu tutuyor - bu alan olmadan gercek pozisyon verisi gelse bile "IBKR pozisyon
    # okunamadi" hatasi gosteriyordu, veri sanki hic gelmiyormus gibi gorunuyordu.
    try:
        rows = ibkr_positions_snapshot()
        return jsonify({"ok": True, "positions": rows, "data": rows, "last_update": now_text(), "broker": "IBKR"})
    except Exception as e:
        return jsonify({"ok": False, "positions": [], "data": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 500


_STABLECOIN_ASSETS = {"USDT", "USDC", "BUSD", "FDUSD", "TUSD", "DAI"}
_ASSET_PRICE_CACHE: Dict[str, Any] = {}
_ASSET_PRICE_CACHE_TTL_SEC = 15.0


def _asset_usd_price(asset: str, market: str) -> float:
    # Binance bakiyelerindeki her coin icin (USDT disinda) canli USD fiyatini
    # bulup satirlara ekliyoruz. iOS uygulamasi usdValue alani yoksa stablecoin
    # disindaki varliklari (orn. futures cuzdanindaki ETH bakiyesi) tamamen
    # gormezden gelip toplam bakiyeyi yanlis (oldugundan dusuk) hesapliyordu.
    asset = asset.upper()
    if asset in _STABLECOIN_ASSETS:
        return 1.0
    cache_key = f"{asset}|{market}"
    cached = _ASSET_PRICE_CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _ASSET_PRICE_CACHE_TTL_SEC:
        return cached[1]
    price = 0.0
    try:
        price = get_price(f"{asset}USDT", market)
    except Exception:
        try:
            # Futures'ta islem gormeyen bir coin ise spot fiyatina dus.
            price = get_price(f"{asset}USDT", "SPOT")
        except Exception:
            price = 0.0
    _ASSET_PRICE_CACHE[cache_key] = (time.time(), price)
    return price


def _enrich_balances_with_usd(balances: Any, market: str) -> Any:
    if not isinstance(balances, list):
        return balances
    for row in balances:
        if not isinstance(row, dict):
            continue
        asset = str(row.get("asset") or row.get("symbol") or row.get("coin") or "").upper()
        if not asset or asset in {"HATA", "SPOT_TRY_EQUIV", "FUTURES_TRY_EQUIV", "BINANCE_TRY_TOTAL"}:
            continue
        # Uygulamanin zaten okudugu direkt USD alanlarindan biri varsa dokunma.
        has_direct = any(
            row.get(k) not in (None, "")
            for k in ("usdValue", "valueUSD", "value_usd", "totalUSDValue", "usdtValue", "totalUSDT")
        )
        if has_direct:
            continue
        qty = safe_float(row.get("total"))
        if qty <= 0:
            qty = safe_float(row.get("balance"))
        if qty <= 0:
            qty = safe_float(row.get("free")) + safe_float(row.get("locked"))
        if qty <= 0:
            continue
        price = _asset_usd_price(asset, market)
        if price > 0:
            row["usdValue"] = round(qty * price, 4)
            row["usd_price"] = price
    return balances


@app.route("/spot-balances", methods=["GET"])
def spot_balances_proxy_alias():
    # Mobil uygulamanin dogrudan cagirdigi path. Railway'in IP'si Binance'de
    # whitelist'li olmadigi icin VPS proxy'sinden (5055) gecirilir.
    try:
        data = _binance_proxy_request("GET", "/spot-balances")
        if isinstance(data, dict):
            data.setdefault("last_update", now_text())
            if "balances" in data:
                data["balances"] = _enrich_balances_with_usd(data["balances"], "SPOT")
            return jsonify(data)
        data = _enrich_balances_with_usd(data, "SPOT")
        return jsonify({"ok": True, "balances": data, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "balances": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/futures-balances", methods=["GET"])
def futures_balances_proxy_alias():
    try:
        data = _binance_proxy_request("GET", "/futures-balances")
        if isinstance(data, dict):
            data.setdefault("last_update", now_text())
            if "balances" in data:
                data["balances"] = _enrich_balances_with_usd(data["balances"], "FUTURES")
            return jsonify(data)
        data = _enrich_balances_with_usd(data, "FUTURES")
        return jsonify({"ok": True, "balances": data, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "balances": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/account-summary", methods=["GET"])
def account_summary_alias():
    # Mobil uygulama burada IBKR hesap ozet satirlarini (tag/currency/value) bekliyor
    # (Binance TRY toplami zaten /portfolio ve /spot-balances+/futures-balances'tan geliyor).
    try:
        rows = ibkr_account_summary_snapshot()
        return jsonify({"ok": True, "data": rows, "broker": "IBKR", "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "data": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 200


@app.route("/market-summary", methods=["GET"])
def market_summary():
    symbol = request.args.get("symbol", "ETHUSDT").upper().replace("/", "")
    market = request.args.get("market", "FUTURES").upper()
    try:
        snapshot = get_market_snapshot(symbol, market)
        return jsonify({
            "symbol": symbol,
            "market": market,
            "price": safe_float(snapshot.get("price")),
            "change_24h": safe_float(snapshot.get("change_24h")),
            "high_24h": safe_float(snapshot.get("high_24h")),
            "low_24h": safe_float(snapshot.get("low_24h")),
            "quote_volume": safe_float(snapshot.get("quote_volume")),
            "orderbook": snapshot.get("orderbook", {}),
            "data_source": snapshot.get("source", "binance"),
            "warning": snapshot.get("binance_error", ""),
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({"error": str(e), "symbol": symbol, "market": market, "last_update": now_text()}), 500


@app.route("/ibkr/market-summary", methods=["GET"])
def ibkr_market_summary():
    symbol = request.args.get("symbol", "AAPL")
    asset_type = request.args.get("asset_type", "STK")
    exchange = request.args.get("exchange", "SMART")
    currency = request.args.get("currency", "USD")
    try:
        return jsonify(ibkr_market_snapshot(symbol, asset_type, exchange, currency))
    except Exception as e:
        return jsonify({
            "broker": "IBKR",
            "symbol": normalize_symbol(symbol),
            "asset_type": str(asset_type or "STK").upper(),
            "error": str(e),
            "last_update": now_text(),
        }), 500


@app.route("/ibkr/ai-signal", methods=["GET"])
def ibkr_ai_signal():
    symbol = request.args.get("symbol", "AAPL")
    asset_type = request.args.get("asset_type", "STK")
    exchange = request.args.get("exchange", "SMART")
    currency = request.args.get("currency", "USD")
    try:
        snap = ibkr_market_snapshot(symbol, asset_type, exchange, currency)
        change = safe_float(snap.get("change_24h"))
        signal = "WAIT"
        confidence = 55
        reason = "Net yön yok."
        if change > 0.7:
            signal = "BUY"
            confidence = min(90, int(57 + abs(change) * 10))
            reason = "IBKR momentum pozitif."
        elif change < -0.7:
            signal = "SELL"
            confidence = min(90, int(57 + abs(change) * 10))
            reason = "IBKR momentum negatif."
        if signal in ["BUY", "SELL"]:
            confidence = max(0, min(95, confidence + learning_bias(signal)))
        return jsonify({
            "symbol": normalize_symbol(symbol),
            "market": "IBKR",
            "asset_type": str(asset_type).upper(),
            "price": safe_float(snap.get("price")),
            "change_24h": change,
            "quote_volume": 0.0,
            "orderbook": synthetic_orderbook(change, "ibkr"),
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "last_update": now_text(),
            "engine_enabled": ENGINE.enabled,
            "data_source": "ibkr",
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "symbol": normalize_symbol(symbol),
            "market": "IBKR",
            "signal": "WAIT",
            "confidence": 0,
            "reason": "IBKR veri alınamadı.",
            "last_update": now_text(),
        }), 500


@app.route("/ai-signal", methods=["GET"])
def ai_signal():
    symbol = request.args.get("symbol", "ETHUSDT").upper().replace("/", "")
    market = request.args.get("market", "FUTURES").upper()
    try:
        return jsonify(calculate_ai_signal(symbol, market))
    except Exception as e:
        return jsonify({"error": str(e), "symbol": symbol, "market": market, "signal": "WAIT", "confidence": 0, "reason": "Veri alınamadı.", "last_update": now_text()}), 500


@app.route("/market-intel", methods=["GET"])
def market_intel():
    try:
        btc = get_market_snapshot("BTCUSDT", "FUTURES")
        eth = get_market_snapshot("ETHUSDT", "FUTURES")
        gold = get_market_snapshot("XAUUSD", "SPOT")
        reit = get_market_snapshot("VNQ", "SPOT")
        btc_change = safe_float(btc.get("change_24h"))
        eth_change = safe_float(eth.get("change_24h"))
        btc_buy = safe_float((btc.get("orderbook") or {}).get("buy_pressure"), 50.0)
        eth_buy = safe_float((eth.get("orderbook") or {}).get("buy_pressure"), 50.0)
        trend_score = (btc_change + eth_change) / 2.0
        risk_score = abs(trend_score) * 10 + abs(btc_buy - 50) + abs(eth_buy - 50)
        regime = "YATAY"
        if trend_score >= 1.2:
            regime = "RISK_ON"
        elif trend_score <= -1.2:
            regime = "RISK_OFF"
        hedge = "Düşük hedge"
        if risk_score > 35:
            hedge = "Orta hedge"
        if risk_score > 50:
            hedge = "Yüksek hedge"

        spot = get_spot_balances()
        stable_total = sum(safe_float(x.get("total")) for x in spot if str(x.get("asset")) in ["USDT", "USDC", "FDUSD", "BUSD"])
        cash_ratio_hint = "Nakit oranı düşük"
        if stable_total >= 1000:
            cash_ratio_hint = "Nakit tamponu var"
        if stable_total >= 5000:
            cash_ratio_hint = "Nakit tamponu güçlü"

        return jsonify({
            "regime": regime,
            "trend_score": round(trend_score, 2),
            "risk_score": round(risk_score, 2),
            "hedge_hint": hedge,
            "cash_flow_hint": cash_ratio_hint,
            "whale_tracking": {
                "btc_buy_pressure": round(btc_buy, 2),
                "eth_buy_pressure": round(eth_buy, 2),
                "comment": "Emir defteri baskısı anlık whale izleme göstergesi olarak kullanılıyor.",
            },
            "cross_asset": {
                "gold_change_24h": round(safe_float(gold.get("change_24h")), 3),
                "gold_source": str(gold.get("source", "unknown")),
                "real_estate_proxy_change_24h": round(safe_float(reit.get("change_24h")), 3),
                "real_estate_proxy_symbol": "VNQ",
                "real_estate_source": str(reit.get("source", "unknown")),
            },
            "macro_note": "Bu çıktı yatırım tavsiyesi değildir; küresel makro koşullar için ek veri kaynağıyla birlikte değerlendirilmelidir.",
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({"error": str(e), "last_update": now_text()}), 500


def compute_cross_asset_intel() -> Dict[str, Any]:
    def quick_change(symbol: str, market: str = "FUTURES") -> float:
        symbol = symbol.upper()
        if symbol in {"XAUUSD", "VNQ"}:
            y = try_yahoo_ticker(symbol)
            if y:
                return safe_float(y.get("change_24h"))
            return 0.0
        path = "/fapi/v1/ticker/24hr" if market.upper() == "FUTURES" else "/api/v3/ticker/24hr"
        base = FUTURES_BASE if market.upper() == "FUTURES" else SPOT_BASE
        try:
            r = requests.get(f"{base}{path}", params={"symbol": symbol}, timeout=3)
            if r.status_code < 400:
                return safe_float((r.json() or {}).get("priceChangePercent"))
        except Exception:
            pass
        return 0.0

    btc_change = quick_change("BTCUSDT", "FUTURES")
    eth_change = quick_change("ETHUSDT", "FUTURES")
    gold_change = quick_change("XAUUSD", "SPOT")
    reit_change = quick_change("VNQ", "SPOT")
    btc_buy = safe_float(pressure_from_change(btc_change).get("buy_pressure"), 50.0)
    eth_buy = safe_float(pressure_from_change(eth_change).get("buy_pressure"), 50.0)
    trend_score = (btc_change + eth_change) / 2.0
    risk_score = abs(trend_score) * 10 + abs(btc_buy - 50) + abs(eth_buy - 50)
    regime = "YATAY"
    if trend_score >= 1.2:
        regime = "RISK_ON"
    elif trend_score <= -1.2:
        regime = "RISK_OFF"
    hedge = "Düşük hedge"
    if risk_score > 35:
        hedge = "Orta hedge"
    if risk_score > 50:
        hedge = "Yüksek hedge"
    return {
        "regime": regime,
        "trend_score": round(trend_score, 2),
        "risk_score": round(risk_score, 2),
        "hedge_hint": hedge,
        "btc_buy_pressure": round(btc_buy, 2),
        "eth_buy_pressure": round(eth_buy, 2),
        "gold_change_24h": round(gold_change, 3),
        "gold_source": "yahoo",
        "real_estate_proxy_change_24h": round(reit_change, 3),
        "real_estate_proxy_symbol": "VNQ",
        "real_estate_source": "yahoo",
    }


@app.route("/ai/investment-plan", methods=["GET"])
def ai_investment_plan():
    """
    Güncel veriyle bugün için gerekçeli varlık dağılım önerisi üretir.
    Bu bir yatırım tavsiyesi değildir; karar destek çıktısıdır.
    """
    try:
        intel = compute_cross_asset_intel()
        risk_score = safe_float(intel.get("risk_score"))
        trend_score = safe_float(intel.get("trend_score"))
        gold_change = safe_float(intel.get("gold_change_24h"))
        reit_change = safe_float(intel.get("real_estate_proxy_change_24h"))

        # Basit, yorumlanabilir puanlama
        crypto_weight = 45.0 if trend_score > 0 else 30.0
        gold_weight = 25.0
        cash_weight = 20.0
        real_estate_weight = 10.0
        if risk_score >= 45:
            crypto_weight = 25.0
            gold_weight = 35.0
            cash_weight = 30.0
            real_estate_weight = 10.0
        elif risk_score <= 25 and trend_score > 0.8:
            crypto_weight = 50.0
            gold_weight = 20.0
            cash_weight = 20.0
            real_estate_weight = 10.0

        if gold_change > 0.8:
            gold_weight += 5.0
            cash_weight -= 5.0
        if reit_change < -0.8:
            real_estate_weight -= 3.0
            cash_weight += 3.0

        total = crypto_weight + gold_weight + cash_weight + real_estate_weight
        if total != 100:
            cash_weight += 100 - total

        rationale = [
            f"Piyasa rejimi: {intel.get('regime', 'YATAY')}, risk skoru: {round(risk_score, 2)}.",
            f"Kripto trend skoru {round(trend_score, 2)} olduğundan kripto ağırlığı %{round(crypto_weight,1)}.",
            f"Altın 24s değişimi %{round(gold_change,2)}; portföyde koruma amacıyla altın %{round(gold_weight,1)}.",
            f"Gayrimenkul proxy (VNQ) 24s %{round(reit_change,2)}; temkinli pay %{round(real_estate_weight,1)}.",
            f"Nakit payı %{round(cash_weight,1)} ile kısa vadeli belirsizlik tamponu korunuyor.",
        ]

        return jsonify({
            "ok": True,
            "plan": {
                "crypto_pct": round(crypto_weight, 1),
                "gold_pct": round(gold_weight, 1),
                "real_estate_pct": round(real_estate_weight, 1),
                "cash_pct": round(cash_weight, 1),
            },
            "rationale": rationale,
            "risk_context": {
                "risk_score": round(risk_score, 2),
                "trend_score": round(trend_score, 2),
                "hedge_hint": intel.get("hedge_hint", ""),
            },
            "disclaimer": "Bu çıktı yatırım tavsiyesi değildir; kendi risk profilin ve vade planınla birlikte değerlendirilmelidir.",
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "last_update": now_text()}), 500


@app.route("/economy-radar", methods=["GET"])
def economy_radar():
    try:
        intel = compute_cross_asset_intel()
        plan = ai_investment_plan().get_json()
        return jsonify({
            "ok": True,
            "intel": intel,
            "today_plan": plan.get("plan", {}),
            "today_rationale": plan.get("rationale", []),
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "last_update": now_text()}), 500


@app.route("/ai-engine/on", methods=["POST"])
def engine_on():
    with state_lock:
        ENGINE.enabled = True
        ENGINE.last_update = now_text()
    return jsonify(asdict(ENGINE))


@app.route("/ai-engine/off", methods=["POST"])
def engine_off():
    with state_lock:
        ENGINE.enabled = False
        ENGINE.last_update = now_text()
    return jsonify(asdict(ENGINE))


@app.route("/ai-engine/status", methods=["GET"])
def engine_status():
    with state_lock:
        return jsonify(asdict(ENGINE))


@app.route("/auto-trader/start", methods=["POST"])
def auto_trader_start():
    body = request.get_json(force=True) or {}
    with AUTO_LOCK:
        AUTO_TRADER.enabled = True
        AUTO_TRADER.broker = str(body.get("broker", AUTO_TRADER.broker)).upper()
        AUTO_TRADER.symbol = normalize_symbol(body.get("symbol", AUTO_TRADER.symbol))
        if "symbols" in body:
            raw_symbols = body.get("symbols")
            if isinstance(raw_symbols, list):
                AUTO_TRADER.symbols = [normalize_symbol(s) for s in raw_symbols if str(s).strip()]
            else:
                AUTO_TRADER.symbols = _parse_symbol_list(str(raw_symbols))
        AUTO_TRADER.market = str(body.get("market", AUTO_TRADER.market)).upper()
        AUTO_TRADER.asset_type = str(body.get("asset_type", AUTO_TRADER.asset_type)).upper()
        AUTO_TRADER.exchange = str(body.get("exchange", AUTO_TRADER.exchange)).upper()
        AUTO_TRADER.currency = str(body.get("currency", AUTO_TRADER.currency)).upper()
        AUTO_TRADER.mode = "live" if str(body.get("mode", AUTO_TRADER.mode)).lower() == "live" else "paper"
        AUTO_TRADER.quantity = max(0.0, safe_float(body.get("quantity"), AUTO_TRADER.quantity))
        AUTO_TRADER.interval_sec = max(8, int(safe_float(body.get("interval_sec"), AUTO_TRADER.interval_sec)))
        AUTO_TRADER.min_confidence = max(50, min(95, int(safe_float(body.get("min_confidence"), AUTO_TRADER.min_confidence))))
        AUTO_TRADER.evaluation_window_sec = max(60, int(safe_float(body.get("evaluation_window_sec"), AUTO_TRADER.evaluation_window_sec)))
        AUTO_TRADER.max_daily_trades = max(1, int(safe_float(body.get("max_daily_trades"), AUTO_TRADER.max_daily_trades)))
        AUTO_TRADER.last_update = now_text()
        AUTO_TRADER.updated_at_epoch = 0.0
    return jsonify(asdict(AUTO_TRADER))


@app.route("/auto-trader/stop", methods=["POST"])
def auto_trader_stop():
    with AUTO_LOCK:
        AUTO_TRADER.enabled = False
        AUTO_TRADER.last_update = now_text()
        AUTO_TRADER.last_reason = "Auto trader durduruldu."
    return jsonify(asdict(AUTO_TRADER))


@app.route("/auto-trader/status", methods=["GET"])
def auto_trader_status():
    with AUTO_LOCK:
        payload = asdict(AUTO_TRADER)
        payload["learning"] = LEARNING_STATS
        payload["ibkr_connected"] = bool(IBKR_RUNTIME.get("connected"))
    return jsonify(payload)


@app.route("/auto-trader/ibkr/start", methods=["POST"])
def ibkr_auto_trader_start():
    body = request.get_json(force=True) or {}
    with IBKR_AUTO_LOCK:
        IBKR_AUTO_TRADER.enabled = True
        IBKR_AUTO_TRADER.symbol = normalize_symbol(body.get("symbol", IBKR_AUTO_TRADER.symbol))
        if "symbols" in body:
            raw_symbols = body.get("symbols")
            if isinstance(raw_symbols, list):
                IBKR_AUTO_TRADER.symbols = [normalize_symbol(s) for s in raw_symbols if str(s).strip()]
            else:
                IBKR_AUTO_TRADER.symbols = _parse_symbol_list(str(raw_symbols))
        IBKR_AUTO_TRADER.asset_type = str(body.get("asset_type", IBKR_AUTO_TRADER.asset_type)).upper()
        IBKR_AUTO_TRADER.exchange = str(body.get("exchange", IBKR_AUTO_TRADER.exchange)).upper()
        IBKR_AUTO_TRADER.currency = str(body.get("currency", IBKR_AUTO_TRADER.currency)).upper()
        IBKR_AUTO_TRADER.mode = "live" if str(body.get("mode", IBKR_AUTO_TRADER.mode)).lower() == "live" else "paper"
        IBKR_AUTO_TRADER.quantity = max(0.0, safe_float(body.get("quantity"), IBKR_AUTO_TRADER.quantity))
        IBKR_AUTO_TRADER.interval_sec = max(8, int(safe_float(body.get("interval_sec"), IBKR_AUTO_TRADER.interval_sec)))
        IBKR_AUTO_TRADER.min_confidence = max(50, min(95, int(safe_float(body.get("min_confidence"), IBKR_AUTO_TRADER.min_confidence))))
        IBKR_AUTO_TRADER.max_daily_trades = max(1, int(safe_float(body.get("max_daily_trades"), IBKR_AUTO_TRADER.max_daily_trades)))
        IBKR_AUTO_TRADER.last_update = now_text()
        IBKR_AUTO_TRADER.updated_at_epoch = 0.0
    return jsonify(asdict(IBKR_AUTO_TRADER))


@app.route("/auto-trader/ibkr/stop", methods=["POST"])
def ibkr_auto_trader_stop():
    with IBKR_AUTO_LOCK:
        IBKR_AUTO_TRADER.enabled = False
        IBKR_AUTO_TRADER.last_update = now_text()
        IBKR_AUTO_TRADER.last_reason = "IBKR auto trader durduruldu."
    return jsonify(asdict(IBKR_AUTO_TRADER))


@app.route("/auto-trader/ibkr/status", methods=["GET"])
def ibkr_auto_trader_status():
    with IBKR_AUTO_LOCK:
        payload = asdict(IBKR_AUTO_TRADER)
        payload["ibkr_connected"] = bool(IBKR_RUNTIME.get("connected"))
    return jsonify(payload)


@app.route("/auto-trader/ibkr/history", methods=["GET"])
def ibkr_auto_trader_history():
    try:
        limit = max(1, min(int(request.args.get("limit", "120")), 500))
        db_records = [r for r in db_recent_auto_history(limit * 2) if str(r.get("broker", "")).upper() == "IBKR"][:limit]
        return jsonify({"ok": True, "history": db_records, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "history": [], "last_update": now_text()}), 200


@app.route("/auto-trader/spot/start", methods=["POST"])
def spot_auto_trader_start():
    body = request.get_json(force=True) or {}
    with SPOT_AUTO_LOCK:
        SPOT_AUTO_TRADER.enabled = True
        SPOT_AUTO_TRADER.symbol = normalize_symbol(body.get("symbol", SPOT_AUTO_TRADER.symbol))
        if "symbols" in body:
            raw_symbols = body.get("symbols")
            if isinstance(raw_symbols, list):
                SPOT_AUTO_TRADER.symbols = [normalize_symbol(s) for s in raw_symbols if str(s).strip()]
            else:
                SPOT_AUTO_TRADER.symbols = _parse_symbol_list(str(raw_symbols))
        SPOT_AUTO_TRADER.mode = "live" if str(body.get("mode", SPOT_AUTO_TRADER.mode)).lower() == "live" else "paper"
        SPOT_AUTO_TRADER.interval_sec = max(8, int(safe_float(body.get("interval_sec"), SPOT_AUTO_TRADER.interval_sec)))
        SPOT_AUTO_TRADER.min_confidence = max(50, min(95, int(safe_float(body.get("min_confidence"), SPOT_AUTO_TRADER.min_confidence))))
        SPOT_AUTO_TRADER.max_daily_trades = max(1, int(safe_float(body.get("max_daily_trades"), SPOT_AUTO_TRADER.max_daily_trades)))
        SPOT_AUTO_TRADER.last_update = now_text()
        SPOT_AUTO_TRADER.updated_at_epoch = 0.0
    return jsonify(asdict(SPOT_AUTO_TRADER))


@app.route("/auto-trader/spot/stop", methods=["POST"])
def spot_auto_trader_stop():
    with SPOT_AUTO_LOCK:
        SPOT_AUTO_TRADER.enabled = False
        SPOT_AUTO_TRADER.last_update = now_text()
        SPOT_AUTO_TRADER.last_reason = "Spot auto trader durduruldu."
    return jsonify(asdict(SPOT_AUTO_TRADER))


@app.route("/auto-trader/spot/status", methods=["GET"])
def spot_auto_trader_status():
    with SPOT_AUTO_LOCK:
        payload = asdict(SPOT_AUTO_TRADER)
    try:
        payload["positions"] = db_list_spot_positions()
    except Exception:
        payload["positions"] = []
    return jsonify(payload)


@app.route("/auto-trader/spot/history", methods=["GET"])
def spot_auto_trader_history():
    try:
        limit = max(1, min(int(request.args.get("limit", "120")), 500))
        db_records = [r for r in db_recent_auto_history(limit * 2) if str(r.get("broker", "")).upper() == "BINANCE_SPOT"][:limit]
        return jsonify({"ok": True, "history": db_records, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "history": [], "last_update": now_text()}), 200


@app.route("/auto-trader/spot/positions", methods=["GET"])
def spot_auto_trader_positions():
    try:
        positions = db_list_spot_positions()
        enriched = []
        for pos in positions:
            symbol = str(pos.get("symbol", "")).upper()
            try:
                snap = get_market_snapshot(symbol, "SPOT")
                price = safe_float(snap.get("price"))
            except Exception:
                price = 0.0
            profit_pct = spot_position_profit_pct(pos, price) if price > 0 else 0.0
            enriched.append({**pos, "current_price": price, "profit_pct": round(profit_pct, 3)})
        return jsonify({"ok": True, "positions": enriched, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "positions": [], "last_update": now_text()}), 200


@app.route("/ai-scenario-analysis", methods=["POST"])
def ai_scenario_analysis_endpoint():
    """iOS 'DD AI analizi' (AICenterView) icin serbest metin senaryo analizi.
    Body: {"scenario": "Fed faiz indirirse BTC, altin ve Nasdaq nasil etkilenir?"}
    Onceden bu ekran her zaman ayni sabit metni donduruyordu (kullanici girdisi
    tamamen goz ardi ediliyordu); artik kullanicinin yazdigi metin gercekten
    okunup, ilgili senaryo(lar) ve guncel piyasa verisiyle kisisellestirilmis
    bir yanit uretiliyor."""
    try:
        body = request.get_json(silent=True) or {}
        scenario_text = str(body.get("scenario") or body.get("text") or "").strip()
        if not scenario_text:
            return jsonify({"ok": False, "error": "scenario metni bos olamaz"}), 400
        result = analyze_user_scenario(scenario_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "result_text": "Analiz sırasında bir hata oluştu, lütfen tekrar deneyin."}), 200


@app.route("/valuation-bubble-analysis", methods=["GET"])
def valuation_bubble_analysis_endpoint():
    """ABD borsalari (S&P500/Nasdaq), altin ve ana sektorlerin (teknoloji,
    finans, enerji, saglik, yari iletken) + Bitcoin'in 1 yillik veriye dayali
    asiri degerleme/balon ve genel piyasa cokusu/duzeltme riski analizini, ayrica
    hisselerin defter degerine (P/B) gore asiri fiyatlanip fiyatlanmadigini ve
    bilanco/nakit akis tablosu bazli profesyonel finansal saglik analizini dondurur."""
    try:
        payload = {"ok": True, **get_valuation_bubble_analysis()}
        try:
            payload["book_value_analysis"] = get_fundamental_valuation_analysis()
        except Exception as e:
            payload["book_value_analysis"] = {"assets": [], "error": str(e)}
        try:
            payload["financial_statement_analysis"] = get_financial_statement_analysis()
        except Exception as e:
            payload["financial_statement_analysis"] = {"assets": [], "error": str(e)}
        try:
            payload["positioning_and_manipulation_analysis"] = get_market_positioning_and_manipulation_analysis()
        except Exception as e:
            payload["positioning_and_manipulation_analysis"] = {"crypto_positioning": [], "stock_positioning": [], "error": str(e)}
        try:
            payload["sector_scenario_analysis"] = get_sector_scenario_analysis()
        except Exception as e:
            payload["sector_scenario_analysis"] = {"scenarios": [], "error": str(e)}
        return jsonify(payload)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "assets": [], "time": now_text()}), 200


@app.route("/market-signals/external", methods=["GET"])
def market_signals_external():
    """Funding rate + Fear&Greed Index gibi harici piyasa sinyallerini gosterir (sadece bilgi amaçlı)."""
    symbol = normalize_symbol(request.args.get("symbol", AUTO_TRADER.symbol))
    try:
        funding = get_funding_rate(symbol)
    except Exception as e:
        funding = {"error": str(e)}
    try:
        fear_greed = get_fear_greed_index()
    except Exception as e:
        fear_greed = {"error": str(e)}
    try:
        macro_regime = get_macro_regime()
    except Exception as e:
        macro_regime = {"error": str(e)}
    try:
        whale_positioning = get_whale_positioning(symbol)
    except Exception as e:
        whale_positioning = {"error": str(e)}
    try:
        geopolitical_risk = get_geopolitical_risk_signal()
    except Exception as e:
        geopolitical_risk = {"error": str(e)}
    try:
        regulatory_activity = get_regulatory_activity_signal()
    except Exception as e:
        regulatory_activity = {"error": str(e)}
    try:
        news_sentiment = get_news_sentiment_signal()
    except Exception as e:
        news_sentiment = {"error": str(e)}
    try:
        google_trends = get_google_trends_signal()
    except Exception as e:
        google_trends = {"error": str(e)}
    return jsonify({
        "symbol": symbol,
        "funding_rate": funding,
        "fear_greed_index": fear_greed,
        "macro_regime": macro_regime,
        "whale_positioning": whale_positioning,
        "geopolitical_risk": geopolitical_risk,
        "regulatory_activity": regulatory_activity,
        "news_sentiment": news_sentiment,
        "google_trends": google_trends,
        "buy_bias": get_external_signal_bias(symbol, "BUY"),
        "sell_bias": get_external_signal_bias(symbol, "SELL"),
        "time": now_text(),
    })


@app.route("/auto-trader/positions-opened-24h", methods=["GET"])
def auto_trader_positions_opened_24h():
    """Son 24 saatte gercekten acilan (simule/hata olmayan, BUY/SELL) pozisyon
    sayisini broker bazinda ve toplam olarak dondurur. Ana sayfada 'son 24
    saatte kac pozisyon acildi' gostergesi icin kullanilir."""
    try:
        cutoff = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with DB_LOCK:
            conn = sqlite3.connect(RUNTIME_DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    """
                    SELECT broker, symbol, action, created_at, execution_json
                    FROM auto_history
                    WHERE created_at >= ? AND action IN ('BUY', 'SELL')
                    ORDER BY created_at DESC
                    """,
                    (cutoff,),
                ).fetchall()
            finally:
                conn.close()
        total = 0
        by_broker: Dict[str, int] = {}
        items: List[Dict[str, Any]] = []
        for r in rows:
            exec_json = r["execution_json"] or "{}"
            try:
                execution = json.loads(exec_json)
            except Exception:
                execution = {}
            simulated = bool(execution.get("simulated", False))
            has_error = bool(execution.get("error"))
            if simulated or has_error:
                continue
            broker = str(r["broker"] or "").upper()
            total += 1
            by_broker[broker] = by_broker.get(broker, 0) + 1
            items.append({
                "broker": broker,
                "symbol": r["symbol"],
                "action": r["action"],
                "time": r["created_at"],
            })
        return jsonify({
            "ok": True,
            "total_opened_24h": total,
            "by_broker": by_broker,
            "items": items[:50],
            "window_hours": 24,
            "time": now_text(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "total_opened_24h": 0, "by_broker": {}, "items": []}), 500


@app.route("/intermarket-analysis", methods=["GET"])
def intermarket_analysis():
    """Piyasalar arasi (kripto <-> hisse <-> emtia) gercek korelasyon analizi.
    Watchlist'teki tum semboller (Binance + IBKR) icin canli fiyat gecmisinden
    hesaplanan Pearson korelasyonunu ve varsa aktif lag/hedge sinyallerini dondurur."""
    try:
        with AUTO_LOCK:
            binance_symbols = list(AUTO_TRADER.symbols) if AUTO_TRADER.symbols else []
        with IBKR_AUTO_LOCK:
            ibkr_symbols = list(IBKR_AUTO_TRADER.symbols) if IBKR_AUTO_TRADER.symbols else []
        all_symbols = binance_symbols + ibkr_symbols
        pairs = compute_correlation_matrix(all_symbols)
        active_signals = []
        for sym in all_symbols:
            sig = get_correlation_pair_signal(sym, all_symbols)
            if sig.get("action") in ("BUY", "SELL"):
                active_signals.append({
                    "symbol": normalize_symbol(sym),
                    "action": sig["action"],
                    "peer": sig.get("peer"),
                    "correlation": sig.get("correlation"),
                    "peer_move_pct": sig.get("peer_move_pct"),
                    "note": sig.get("note"),
                })
        cross_asset = get_cross_asset_correlations()
        return jsonify({
            "ok": True,
            "pairs": pairs[:30],
            "cross_asset_pairs": cross_asset.get("pairs", []),
            "active_lag_signals": active_signals,
            "symbols_tracked": len(all_symbols),
            "time": now_text(),
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "pairs": [], "active_lag_signals": []}), 500


@app.route("/auto-trader/history", methods=["GET"])
def auto_trader_history():
    """Return auto-trader signal history. Combines in-memory + persistent DB."""
    try:
        limit = max(1, min(int(request.args.get("limit", "120")), 500))
        
        # Get DB records (persistent)
        db_records = db_recent_auto_history(limit)
        
        # Get in-memory records (for current session)
        with AUTO_LOCK:
            mem_records = AUTO_HISTORY[:limit]
        
        return jsonify({
            "ok": True,
            "persistent_records": len(db_records),
            "session_records": len(mem_records),
            "history": db_records,
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "last_update": now_text(),
        }), 500


@app.route("/ai/learning-report", methods=["GET"])
def ai_learning_report():
    rows = []
    for side in ["BUY", "SELL"]:
        wins = int(LEARNING_STATS.get(side, {}).get("wins", 0))
        losses = int(LEARNING_STATS.get(side, {}).get("losses", 0))
        total = wins + losses
        win_rate = (wins / total * 100.0) if total > 0 else 0.0
        rows.append({"side": side, "wins": wins, "losses": losses, "win_rate": round(win_rate, 2)})
    return jsonify({
        "stats": rows,
        "pending_evaluations": len(SIGNAL_QUEUE),
        "note": "Öğrenme sinyal performansına dayanır; yatırım tavsiyesi değildir.",
        "last_update": now_text(),
    })


@app.route("/manual-order", methods=["POST"])
def manual_order():
    body = request.get_json(force=True) or {}
    symbol = str(body.get("symbol", "ETHUSDT")).upper().replace("/", "")
    side = str(body.get("side", "BUY")).upper()
    quantity = safe_float(body.get("quantity"), 0)
    reduce_only = safe_bool(body.get("reduceOnly", False), False)
    request_id = str(body.get("request_id") or request.headers.get("X-Request-ID") or uuid.uuid4())

    if quantity <= 0:
        return jsonify({"error": "Miktar 0'dan büyük olmalı."}), 400
    if side not in ["BUY", "SELL"]:
        return jsonify({"error": "side BUY veya SELL olmalı."}), 400

    try:
        result = place_futures_order(
            symbol,
            side,
            quantity,
            reduce_only=reduce_only,
            request_id=request_id,
            channel="manual",
        )
        if result.get("error"):
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "time": now_text()}), 500


@app.route("/ibkr/manual-order", methods=["POST"])
def ibkr_manual_order():
    body = request.get_json(force=True) or {}
    symbol = body.get("symbol", "AAPL")
    side = body.get("side", "BUY")
    quantity = safe_float(body.get("quantity"), 0)
    asset_type = str(body.get("asset_type", "STK"))
    exchange = str(body.get("exchange", "SMART"))
    currency = str(body.get("currency", "USD"))
    try:
        request_id = str(uuid.uuid4())
        return jsonify(ibkr_place_market_order(symbol, side, quantity, asset_type, exchange, currency, request_id=request_id))
    except Exception as e:
        return jsonify({
            "broker": "IBKR",
            "symbol": normalize_symbol(symbol),
            "asset_type": str(asset_type).upper(),
            "error": str(e),
            "last_update": now_text(),
        }), 500


@app.route("/close-position", methods=["POST"])
def close_position():
    body = request.get_json(force=True) or {}
    symbol = str(body.get("symbol", "")).upper().replace("/", "")
    if not symbol:
        return jsonify({"error": "symbol gerekli."}), 400

    positions = get_futures_positions()
    target = next((p for p in positions if p.get("symbol") == symbol), None)
    if not target:
        return jsonify({"message": "Bu sembolde açık pozisyon bulunamadı.", "symbol": symbol})

    size = abs(safe_float(target.get("size")))
    side = "SELL" if target.get("side") == "LONG" else "BUY"
    try:
        request_id = str(body.get("request_id") or request.headers.get("X-Request-ID") or uuid.uuid4())
        result = place_futures_order(
            symbol,
            side,
            size,
            reduce_only=True,
            request_id=request_id,
            channel="manual",
        )
        if result.get("error"):
            return jsonify(result), 400
        db_record_position_closure(
            broker="BINANCE_FUTURES",
            symbol=symbol,
            side=str(target.get("side", "")).upper(),
            qty=size,
            entry_price=safe_float(target.get("entry_price")),
            exit_price=safe_float(target.get("mark_price")),
            realized_pnl=safe_float(target.get("pnl")),
            realized_pnl_pct=binance_position_profit_pct(target),
            close_reason="MANUAL",
            detail="Kullanıcı manuel olarak pozisyonu kapattı.",
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "time": now_text()}), 500


@app.route("/position-closures", methods=["GET"])
def position_closures_alias():
    """Bir pozisyon kapandiginda 'neden kapandi (kar al/zarar kes/manuel), kar mi
    zarar mi, ne kadar' sorusuna net cevap veren rapor listesi. Kullanici
    'IBKR'de AMD pozisyonu kapandi, neden kapandigini/kar mi zarar mi bilmiyorum'
    dedigi icin eklendi."""
    try:
        limit = max(1, min(int(request.args.get("limit", "50")), 200))
    except Exception:
        limit = 50
    reason_labels = CLOSE_REASON_LABELS_TR
    try:
        rows = db_recent_position_closures(limit)
        items = []
        for r in rows:
            reason = str(r.get("close_reason", "-"))
            pnl = safe_float(r.get("realized_pnl"))
            items.append({
                "time": r.get("created_at"),
                "broker": r.get("broker"),
                "symbol": r.get("symbol"),
                "side": r.get("side"),
                "qty": r.get("qty"),
                "entry_price": r.get("entry_price"),
                "exit_price": r.get("exit_price"),
                "realized_pnl": pnl,
                "realized_pnl_pct": r.get("realized_pnl_pct"),
                "close_reason": reason,
                "close_reason_label": reason_labels.get(reason, reason),
                "is_profit": pnl >= 0,
                "detail": r.get("detail") or "",
                "summary": (
                    f"{r.get('symbol')} ({r.get('broker')}) pozisyonu "
                    f"{reason_labels.get(reason, reason)} nedeniyle kapandı: "
                    f"{'+' if pnl >= 0 else ''}{pnl:.2f} ({safe_float(r.get('realized_pnl_pct')):.2f}%)."
                ),
            })
        return jsonify({"ok": True, "items": items, "time": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "items": [], "error": str(e), "time": now_text()}), 200


@app.route("/position-closures/test-email", methods=["POST", "GET"])
def position_closures_test_email():
    """Mail ayarlarinin (NOTIFY_EMAIL_*) dogru calistigini canli olarak
    dogrulamak icin ornek bir kapanis maili gonderir. Kayit olusturmaz,
    sadece mail atar."""
    if not (NOTIFY_EMAIL_ENABLED and NOTIFY_EMAIL_SENDER and NOTIFY_EMAIL_PASSWORD and NOTIFY_EMAIL_RECIPIENT):
        return jsonify({
            "ok": False,
            "error": "E-posta ayarları eksik (NOTIFY_EMAIL_ENABLED/SENDER/PASSWORD/RECIPIENT).",
        }), 200
    send_position_closure_email(
        broker="TEST",
        symbol="TESTUSDT",
        side="LONG",
        qty=1.0,
        entry_price=100.0,
        exit_price=105.0,
        realized_pnl=5.0,
        realized_pnl_pct=5.0,
        close_reason="TAKE_PROFIT",
        detail="Bu bir test mailidir; ayarların doğru çalıştığını kontrol etmek için gönderildi.",
    )
    return jsonify({"ok": True, "message": "Test maili gönderildi (birkaç saniye içinde gelmeli).", "time": now_text()})


# ---------------------------------------------------------------------------
# Mobil uygulama (DFinans iOS) icin ek route'lar. Uygulama daha once
# http://46.101.194.52:5055 (VPS) adresine gidiyordu; Railway backend'ine
# tasindiginda cagiracagi tum path'ler burada karsilaniyor.
# ---------------------------------------------------------------------------

@app.route("/ibkr-status", methods=["GET"])
def ibkr_status_alias():
    return ibkr_health()


@app.route("/ibkr-price", methods=["GET"])
def ibkr_price_alias():
    symbol = request.args.get("symbol", "AAPL")
    asset_type = request.args.get("asset_type", "STK")
    exchange = request.args.get("exchange", "SMART")
    currency = request.args.get("currency", "USD")
    try:
        snap = ibkr_market_snapshot(symbol, asset_type, exchange, currency)
        price = safe_float(snap.get("price"))
        change = safe_float(snap.get("change_24h"))
        return jsonify({
            "symbol": normalize_symbol(symbol),
            "price": price,
            "priceText": f"${price:,.2f}" if price else "-",
            "last": price,
            "marketPrice": price,
            "close": price,
            "changePercent": change,
            "dailyChange": change,
            "source": "IBKR",
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({
            "symbol": normalize_symbol(symbol),
            "price": 0,
            "error": str(e),
            "source": "IBKR",
            "last_update": now_text(),
        }), 200


@app.route("/order", methods=["POST"])
def ibkr_order_alias():
    # Mobil uygulama IBKR gercek emirlerini bu path'e gonderiyor.
    body = request.get_json(force=True) or {}
    symbol = body.get("symbol", "AAPL")
    side = str(body.get("side", "BUY")).upper()
    if side in ("AL", "BUY", "LONG"):
        side = "BUY"
    elif side in ("SAT", "SELL", "SHORT"):
        side = "SELL"
    quantity = safe_float(body.get("quantity"), 0)
    asset_type = str(body.get("assetType", body.get("asset_type", "STK")))
    exchange = str(body.get("exchange", "SMART"))
    currency = str(body.get("currency", "USD"))
    if quantity <= 0:
        return jsonify({"success": False, "message": "Miktar 0'dan büyük olmalı."}), 400
    try:
        request_id = str(body.get("request_id") or uuid.uuid4())
        result = ibkr_place_market_order(symbol, side, quantity, asset_type, exchange, currency, request_id=request_id)
        return jsonify({
            "success": not bool(result.get("error")),
            "message": f"IBKR emri gönderildi. Durum: {result.get('status', '-')}, Ortalama fiyat: {result.get('avg_fill_price', 0)}",
            "orderId": str(result.get("order_id", "")),
            "result": result,
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"IBKR emir hatası: {e}"}), 500


@app.route("/cancel_order", methods=["POST"])
def ibkr_cancel_order_alias():
    body = request.get_json(force=True) or {}
    order_id = body.get("orderId") or body.get("order_id")
    try:
        def _run(ib, _):
            cancelled = False
            for trade in ib.openTrades():
                if str(getattr(trade.order, "orderId", "")) == str(order_id):
                    ib.cancelOrder(trade.order)
                    cancelled = True
            return cancelled
        cancelled = ibkr_execute(_run)
        return jsonify({"success": True, "message": "IBKR emir iptali gönderildi." if cancelled else "Eşleşen açık IBKR emri bulunamadı, yine de iptal talebi iletildi."})
    except Exception as e:
        return jsonify({"success": False, "message": f"IBKR iptal hatası: {e}"}), 500


@app.route("/history", methods=["GET"])
def ibkr_history_alias():
    symbol = request.args.get("symbol", "AAPL")
    asset_type = request.args.get("asset_type", "STK")
    exchange = request.args.get("exchange", "SMART")
    currency = request.args.get("currency", "USD")
    duration = request.args.get("duration", "1 M")
    bar_size = request.args.get("bar_size", "1 day")
    try:
        def _run(ib, ibs):
            contract = build_ibkr_contract(ibs, symbol, asset_type, exchange, currency)
            qualified = ib.qualifyContracts(contract)
            if not qualified:
                raise RuntimeError("IBKR contract doğrulanamadı.")
            bars = ib.reqHistoricalData(
                qualified[0],
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow="TRADES",
                useRTH=True,
                formatDate=1,
            )
            return [
                {
                    "date": str(b.date),
                    "open": safe_float(b.open),
                    "high": safe_float(b.high),
                    "low": safe_float(b.low),
                    "close": safe_float(b.close),
                    "volume": safe_float(b.volume),
                }
                for b in bars
            ]
        points = ibkr_execute(_run)
        return jsonify({"success": True, "symbol": normalize_symbol(symbol), "points": points, "last_update": now_text()})
    except Exception as e:
        return jsonify({"success": False, "symbol": normalize_symbol(symbol), "points": [], "error": str(e), "last_update": now_text()}), 200


def _resolve_place_order_market(payload: Dict[str, Any]) -> Dict[str, Any]:
    market = str(payload.get("market", "usdtm")).lower()
    symbol = str(payload.get("symbol", "ETHUSDT")).upper().replace("/", "")
    side = str(payload.get("side", "BUY")).upper()
    quantity = safe_float(payload.get("amount", payload.get("quantity")), 0)
    leverage = int(safe_float(payload.get("leverage"), 1) or 1)
    request_id = str(payload.get("request_id") or uuid.uuid4())

    if quantity <= 0:
        return {"ok": False, "error": "amount/quantity 0'dan büyük olmalı."}
    if side not in ("BUY", "SELL"):
        return {"ok": False, "error": "side BUY veya SELL olmalı."}

    if market == "spot":
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": quantity,
            }
            data = signed_request("POST", SPOT_BASE, "/api/v3/order", params)
            db_insert_trade_journal(
                broker="Binance", channel="manual-spot", symbol=symbol, side=side,
                quantity=quantity, status="FILLED", simulated=False, payload=data, request_id=request_id,
            )
            return {"ok": True, "result": data}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # usdtm / coinm -> futures
    try:
        if leverage > 1:
            ensure_binance_leverage(symbol, leverage)
        result = place_futures_order(
            symbol, side, quantity,
            reduce_only=False, request_id=request_id, channel="manual",
        )
        if result.get("error"):
            return {"ok": False, "error": result.get("error")}
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.route("/place-order", methods=["POST"])
def place_order_alias():
    body = request.get_json(force=True) or {}
    outcome = _resolve_place_order_market(body)
    if not outcome.get("ok"):
        return jsonify({"success": False, "message": outcome.get("error", "Emir gönderilemedi.")}), 400
    return jsonify({"success": True, "message": "Emir başarıyla gönderildi.", "result": outcome.get("result")})


@app.route("/cancel-order", methods=["POST"])
def cancel_order_dash_alias():
    body = request.get_json(force=True) or {}
    symbol = str(body.get("symbol", "")).upper().replace("/", "")
    order_id = body.get("orderId")
    market = str(body.get("market", "usdtm")).lower()
    try:
        base = SPOT_BASE if market == "spot" else FUTURES_BASE
        path = "/api/v3/order" if market == "spot" else "/fapi/v1/order"
        params: Dict[str, Any] = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        signed_request("DELETE", base, path, params)
        return jsonify({"success": True, "message": f"{symbol} emri iptal edildi."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Emir iptal hatası: {e}"}), 500


def _open_orders_snapshot() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        futures_orders = signed_request("GET", FUTURES_BASE, "/fapi/v1/openOrders", {})
        for o in futures_orders:
            rows.append({
                "symbol": o.get("symbol", "-"),
                "type": o.get("type", "-"),
                "side": o.get("side", "-"),
                "amount": str(o.get("origQty", "-")),
                "price": str(o.get("price", "-")),
                "status": o.get("status", "Açık"),
                "orderId": o.get("orderId"),
            })
    except Exception:
        pass
    try:
        spot_orders = signed_request("GET", SPOT_BASE, "/api/v3/openOrders", {})
        for o in spot_orders:
            rows.append({
                "symbol": o.get("symbol", "-"),
                "type": o.get("type", "-"),
                "side": o.get("side", "-"),
                "amount": str(o.get("origQty", "-")),
                "price": str(o.get("price", "-")),
                "status": o.get("status", "Açık"),
                "orderId": o.get("orderId"),
            })
    except Exception:
        pass
    return rows


@app.route("/orders", methods=["GET"])
def orders_alias():
    try:
        return jsonify({"success": True, "orders": _open_orders_snapshot(), "last_update": now_text()})
    except Exception as e:
        return jsonify({"success": False, "orders": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/open-orders", methods=["GET"])
def open_orders_alias():
    try:
        return jsonify({"orders": _open_orders_snapshot(), "last_update": now_text()})
    except Exception as e:
        return jsonify({"orders": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/dd-ai-dashboard", methods=["GET"])
def dd_ai_dashboard_route():
    try:
        return jsonify(build_dd_ai_dashboard())
    except Exception as e:
        return jsonify({
            "updated_at": now_text(), "ai_confidence": 0, "market_regime": "-",
            "macro": {"vix": "-", "nasdaq": "-", "sp500": "-", "dxy": "-", "gold": "-", "oil": "-"},
            "market_mood": {"general_mode": "-", "risk_appetite": "-", "institutional_flow": "-", "bubble_risk": "-"},
            "institutional_scores": {}, "learning_rates": {},
            "last_decision": {"symbol": "-", "action": "-", "confidence": 0, "reason": str(e)},
        }), 200


@app.route("/market-flow-risk", methods=["GET"])
def market_flow_risk_route():
    try:
        return jsonify(build_market_flow_risk())
    except Exception as e:
        return jsonify({
            "ok": False, "updated_at": now_text(), "market_state": "-", "risk_score": 0,
            "warning": str(e),
            "net_flows": {
                "crypto": {"value": "-", "raw": 0.0, "status": "-"},
                "stocks": {"value": "-", "raw": 0.0, "status": "-"},
                "commodities": {"value": "-", "raw": 0.0, "status": "-"},
                "fx_bonds": {"value": "-", "raw": 0.0, "status": "-"},
            },
        }), 200


@app.route("/ai-status", methods=["GET"])
def ai_status_alias():
    with AUTO_LOCK:
        mode = AI_UI_MODE.get("mode", "off")
    return jsonify({"ok": True, "mode": mode, "source": "railway", "last_update": now_text()})


@app.route("/ai-control", methods=["POST"])
def ai_control_alias():
    body = request.get_json(force=True) or {}
    mode = str(body.get("mode", "off")).lower()
    if mode not in ("off", "watch", "auto"):
        mode = "off"
    with AUTO_LOCK:
        AI_UI_MODE["mode"] = mode
        AUTO_TRADER.enabled = (mode == "auto")
        AUTO_TRADER.last_update = now_text()
        AUTO_TRADER.last_reason = f"Mobil uygulamadan mod değişti: {mode}"
    return jsonify({"ok": True, "mode": mode, "last_update": now_text()})


@app.route("/ai-logs", methods=["GET"])
def ai_logs_alias():
    try:
        limit = max(1, min(int(request.args.get("limit", "100")), 500))
    except Exception:
        limit = 100
    try:
        return jsonify({"ok": True, "logs": build_ai_log_entries(limit), "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "logs": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/signal", methods=["GET"])
def signal_alias():
    symbol = normalize_symbol(request.args.get("symbol", AUTO_TRADER.symbol))
    try:
        result = calculate_ai_signal(symbol, "FUTURES")
        return jsonify({
            "symbol": symbol,
            "signal": result.get("signal", "WAIT"),
            "confidence": int(safe_float(result.get("confidence"), 50)),
        })
    except Exception as e:
        return jsonify({"symbol": symbol, "signal": "WAIT", "confidence": 50, "error": str(e)})


@app.route("/status", methods=["GET"])
def status_alias():
    with IBKR_LOCK:
        ibkr_connected = bool(IBKR_RUNTIME.get("connected"))
    with AUTO_LOCK:
        auto_enabled = AUTO_TRADER.enabled
    return jsonify({
        "ok": True,
        "status": "online",
        "ibkr_connected": ibkr_connected,
        "auto_trader_enabled": auto_enabled,
        "time": now_text(),
    })


@app.route("/trade-log", methods=["GET"])
def trade_log():
    return jsonify({"logs": TRADE_LOG[:100], "last_update": now_text()})


@app.route("/trade-journal", methods=["GET"])
def trade_journal():
    """Return persistent trade journal from SQLite database."""
    try:
        limit = max(1, min(int(request.args.get("limit", "150")), 500))
        records = db_recent_trade_journal(limit)
        return jsonify({
            "ok": True,
            "total": len(records),
            "records": records,
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "last_update": now_text(),
        }), 500


init_runtime_db()
start_background_workers_once()


if __name__ == "__main__":
    print(f"\n{APP_NAME} çalışıyor")
    print(f"Adres: http://127.0.0.1:{PORT}")
    print(f"Canlı emir modu: {LIVE_TRADING}")
    print("Railway/Cloud için /health endpointini kontrol et.\n")
    app.run(host=HOST, port=PORT, debug=False)
