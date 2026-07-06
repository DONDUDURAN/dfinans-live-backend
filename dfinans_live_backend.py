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
import sqlite3
import hashlib
import threading
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
RUNTIME_DB_PATH = os.getenv("DFINANS_RUNTIME_DB_PATH", "/tmp/dfinans_runtime.db")
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

# Risk management state
DAILY_REALIZED_PNL = 0.0
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "-500.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "5"))
LAST_ORDER_TIME: Dict[str, float] = {}
MIN_ORDER_COOLDOWN_SEC = float(os.getenv("MIN_ORDER_COOLDOWN_SEC", "2.0"))
BINANCE_TAKE_PROFIT_PCT = float(os.getenv("BINANCE_TAKE_PROFIT_PCT", "5.0"))

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


def ibkr_execute(action):
    ensure_thread_event_loop()
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            # Ayni ib_insync IB client'i (ve onun event loop'unu) ayni anda birden
            # fazla thread'in (gunicorn istek thread'i, keepalive arka plan thread'i,
            # auto-trader dongusu) kullanmasi ciddi kilitlenmelere/timeout'lara yol
            # aciyordu. Tum baglanti + istek akisini tek bir lock altinda serilestirerek
            # bu race condition'i onluyoruz.
            with IBKR_LOCK:
                ib, ibs = ensure_ibkr_connection(force_reconnect=(attempt == 1))
                result = action(ib, ibs)
                IBKR_RUNTIME["connected"] = bool(ib.isConnected())
                IBKR_RUNTIME["last_ok"] = now_text()
                IBKR_RUNTIME["last_error"] = ""
            return result
        except Exception as e:
            last_error = e
            with IBKR_LOCK:
                IBKR_RUNTIME["connected"] = False
                IBKR_RUNTIME["last_error"] = str(e)
                _ibkr_disconnect_locked()
            time.sleep(0.7)
    raise RuntimeError(f"IBKR işlem hatası: {last_error}")


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


def ibkr_market_snapshot(symbol: str, asset_type: str, exchange: str, currency: str) -> Dict[str, Any]:
    def _run(ib, ibs):
        contract = build_ibkr_contract(ibs, symbol, asset_type, exchange, currency)
        qualified = ib.qualifyContracts(contract)
        if not qualified:
            raise RuntimeError("IBKR contract doğrulanamadı.")
        ticker = ib.reqMktData(qualified[0], "", True, False)
        ib.sleep(2.5)
        price = safe_float(ticker.marketPrice())
        last_price = safe_float(getattr(ticker, "last", 0))
        close_price = safe_float(getattr(ticker, "close", 0))
        if price <= 0:
            price = last_price if last_price > 0 else close_price
        if price <= 0:
            raise RuntimeError("IBKR canlı fiyat alınamadı.")
        prev = close_price if close_price > 0 else price
        change_24h = ((price - prev) / prev) * 100.0 if prev > 0 else 0.0
        # Ikinci, bagimsiz sinyal: emir defteri (bid/ask) buyuklugu dengesizligi.
        # Momentum (change_24h) fiyattan turetilirken, bu deger gercek en iyi
        # alis/satis emri boyutlarindan (top-of-book) geliyor - birbirinden bagimsiz.
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
    return ibkr_execute(_run)


def ibkr_positions_snapshot() -> List[Dict[str, Any]]:
    def _run(ib, _):
        rows = []
        for pos in ib.positions():
            if IBKR_ACCOUNT and pos.account != IBKR_ACCOUNT:
                continue
            qty = safe_float(pos.position)
            if qty == 0:
                continue
            avg_cost = safe_float(pos.avgCost)
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
                "mark_price": 0.0,
                "pnl": 0.0,
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
        if IBKR_ACCOUNT:
            order.account = IBKR_ACCOUNT
        trade = ib.placeOrder(qualified[0], order)
        for _ in range(40):
            status = str(getattr(trade.orderStatus, "status", ""))
            if status in ibs.OrderStatus.DoneStates:
                break
            ib.sleep(0.25)

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


def auto_trader_cycle() -> None:
    with AUTO_LOCK:
        if not AUTO_TRADER.enabled:
            return
        broker = AUTO_TRADER.broker.upper()
        symbol = normalize_symbol(AUTO_TRADER.symbol)
        market = AUTO_TRADER.market.upper()
        qty = max(0.0, AUTO_TRADER.quantity)
        min_conf = AUTO_TRADER.min_confidence
        mode = AUTO_TRADER.mode
        asset_type = AUTO_TRADER.asset_type
        exchange = AUTO_TRADER.exchange
        currency = AUTO_TRADER.currency
        eval_window = AUTO_TRADER.evaluation_window_sec
        max_daily = AUTO_TRADER.max_daily_trades
        day_key = datetime.now().strftime("%Y-%m-%d")
        if not AUTO_TRADER.last_update.startswith(day_key):
            AUTO_TRADER.daily_trade_count = 0

    action = "WAIT"
    confidence = 50
    reason = "Koşullar bekleniyor."
    price = 0.0
    execution: Dict[str, Any] = {"simulated": True, "message": "Emir yok"}

    if broker == "BINANCE":
        tp_execution = enforce_binance_take_profit(channel="auto_take_profit")
        if tp_execution:
            with AUTO_LOCK:
                AUTO_TRADER.last_action = "TAKE_PROFIT"
                AUTO_TRADER.last_confidence = 100
                AUTO_TRADER.last_reason = (
                    f"{tp_execution.get('symbol', symbol)} için %"
                    f"{tp_execution.get('target_pct', BINANCE_TAKE_PROFIT_PCT)} kâr hedefi tetiklendi."
                )
                AUTO_TRADER.last_price = 0.0
                AUTO_TRADER.last_update = now_text()
                AUTO_TRADER.last_error = str(tp_execution.get("error", "") or "")
                AUTO_TRADER.updated_at_epoch = time.time()
                AUTO_HISTORY.insert(
                    0,
                    {
                        "time": AUTO_TRADER.last_update,
                        "broker": broker,
                        "symbol": tp_execution.get("symbol", symbol),
                        "action": "TAKE_PROFIT",
                        "confidence": 100,
                        "price": 0.0,
                        "reason": AUTO_TRADER.last_reason,
                        "execution": tp_execution,
                    },
                )
                del AUTO_HISTORY[300:]
                db_insert_auto_history(
                    broker=broker,
                    symbol=str(tp_execution.get("symbol", symbol)),
                    action="TAKE_PROFIT",
                    confidence=100,
                    price=0.0,
                    reason=AUTO_TRADER.last_reason,
                    execution=tp_execution,
                )
            return

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
    resolve_learning(symbol, price)

    with AUTO_LOCK:
        allow_trade = (
            action in ["BUY", "SELL"]
            and confidence >= min_conf
            and AUTO_TRADER.daily_trade_count < max_daily
            and qty > 0
        )
        do_live = mode == "live" and ((broker == "IBKR" and IBKR_LIVE_TRADING) or (broker != "IBKR" and LIVE_TRADING))
        if allow_trade:
            if broker == "IBKR":
                if do_live:
                    execution = ibkr_place_market_order(symbol, action, qty, asset_type, exchange, currency)
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
                AUTO_TRADER.last_error = str(execution.get("error"))
            else:
                AUTO_TRADER.daily_trade_count += 1
                queue_signal_for_learning(symbol, action, price, eval_window)

        AUTO_TRADER.last_action = action
        AUTO_TRADER.last_confidence = confidence
        AUTO_TRADER.last_reason = reason
        AUTO_TRADER.last_price = price
        AUTO_TRADER.last_update = now_text()
        AUTO_TRADER.last_error = ""
        AUTO_TRADER.updated_at_epoch = time.time()
        AUTO_HISTORY.insert(
            0,
            {
                "time": AUTO_TRADER.last_update,
                "broker": broker,
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "price": price,
                "reason": reason,
                "execution": execution,
            },
        )
        del AUTO_HISTORY[300:]
        
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
        time.sleep(1.0)


def start_background_workers_once():
    global KEEPALIVE_THREAD_STARTED, AUTO_THREAD_STARTED
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
    if BINANCE_TAKE_PROFIT_PCT <= 0:
        return None
    positions = [
        p for p in get_futures_positions()
        if p.get("id") != "error" and str(p.get("symbol", "")).upper() != "HATA"
    ]
    for position in positions:
        profit_pct = binance_position_profit_pct(position)
        if profit_pct < BINANCE_TAKE_PROFIT_PCT:
            continue
        symbol = str(position.get("symbol", "")).upper()
        size = abs(safe_float(position.get("size")))
        if not symbol or size <= 0:
            continue
        close_side = "SELL" if str(position.get("side", "")).upper() == "LONG" else "BUY"
        request_id = f"tp-{symbol}-{int(time.time())}"
        result = place_futures_order(
            symbol,
            close_side,
            size,
            reduce_only=True,
            request_id=request_id,
            channel=channel,
        )
        result["trigger"] = "take_profit_roi_pct"
        result["trigger_pct"] = round(profit_pct, 4)
        result["target_pct"] = BINANCE_TAKE_PROFIT_PCT
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
        return jsonify({"positions": ibkr_positions_snapshot(), "last_update": now_text(), "broker": "IBKR"})
    except Exception as e:
        return jsonify({"positions": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 500


@app.route("/ibkr-positions", methods=["GET"])
def ibkr_positions_alias():
    # Mobil uygulama bu path'i cagiriyor; /ibkr/positions ile ayni veriyi dondurur.
    try:
        return jsonify({"positions": ibkr_positions_snapshot(), "last_update": now_text(), "broker": "IBKR"})
    except Exception as e:
        return jsonify({"positions": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 500


@app.route("/spot-balances", methods=["GET"])
def spot_balances_proxy_alias():
    # Mobil uygulamanin dogrudan cagirdigi path. Railway'in IP'si Binance'de
    # whitelist'li olmadigi icin VPS proxy'sinden (5055) gecirilir.
    try:
        data = _binance_proxy_request("GET", "/spot-balances")
        if isinstance(data, dict):
            data.setdefault("last_update", now_text())
            return jsonify(data)
        return jsonify({"ok": True, "balances": data, "last_update": now_text()})
    except Exception as e:
        return jsonify({"ok": False, "balances": [], "error": str(e), "last_update": now_text()}), 200


@app.route("/futures-balances", methods=["GET"])
def futures_balances_proxy_alias():
    try:
        data = _binance_proxy_request("GET", "/futures-balances")
        if isinstance(data, dict):
            data.setdefault("last_update", now_text())
            return jsonify(data)
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
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "time": now_text()}), 500


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
    return jsonify({"logs": TRADE_LOG[:100], "last_update": now_text()})


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
