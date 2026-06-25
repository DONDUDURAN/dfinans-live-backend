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
import hmac
import time
import json
import math
import uuid
import sqlite3
import hashlib
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
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
IBKR_ENABLED = os.getenv("IBKR_ENABLED", "false").lower() == "true"
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", "7497"))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "21"))
IBKR_ACCOUNT = os.getenv("IBKR_ACCOUNT", "")
IBKR_KEEPALIVE_SEC = int(os.getenv("IBKR_KEEPALIVE_SEC", "20"))
IBKR_LIVE_TRADING = os.getenv("IBKR_LIVE_TRADING", "false").lower() == "true"
AUTO_TRADER_ENABLED = os.getenv("AUTO_TRADER_ENABLED", "false").lower() == "true"
AUTO_TRADER_MODE = os.getenv("AUTO_TRADER_MODE", "paper").lower()
RUNTIME_DB_PATH = os.getenv("DFINANS_RUNTIME_DB_PATH", "/tmp/dfinans_runtime.db")

# Railway / cloud IP bloklarında Binance bazen ana endpoint'i 451 ile engelleyebiliyor.
# Bu yüzden varsayılanı api1/fapi1 yaptık ve public/signed isteklerde fallback endpoint listesi kullanıyoruz.
SPOT_BASE = os.getenv("BINANCE_SPOT_BASE", "https://api1.binance.com")
FUTURES_BASE = os.getenv("BINANCE_FUTURES_BASE", "https://fapi1.binance.com")
SPOT_BASES = [SPOT_BASE, "https://api.binance.com", "https://api2.binance.com", "https://api3.binance.com"]
FUTURES_BASES = [FUTURES_BASE, "https://fapi.binance.com", "https://fapi2.binance.com", "https://fapi3.binance.com"]

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
}

app = Flask(__name__)
CORS(app)

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
}
IBKR_LOCK = threading.Lock()
KEEPALIVE_THREAD_STARTED = False
AUTO_THREAD_STARTED = False


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
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


def db_insert_auto_history(row: Dict[str, Any]) -> None:
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
                    str(row.get("broker", "")),
                    str(row.get("symbol", "")),
                    str(row.get("action", "")),
                    int(safe_float(row.get("confidence"), 0)),
                    safe_float(row.get("price"), 0),
                    str(row.get("reason", "")),
                    json.dumps(row.get("execution", {}), ensure_ascii=False),
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
                r = requests.get(url, headers=headers, timeout=12)
            elif method.upper() == "POST":
                r = requests.post(url, headers=headers, timeout=12)
            elif method.upper() == "DELETE":
                r = requests.delete(url, headers=headers, timeout=12)
            else:
                raise ValueError("Desteklenmeyen HTTP metodu")

            if r.status_code < 400:
                return r.json()
            last_error = f"{r.status_code} - {short_binance_error(r.text)}"
        except Exception as e:
            last_error = str(e)

    raise RuntimeError(f"Binance hata: {last_error}")

def public_get(base: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    last_error = ""
    for try_base in base_candidates(base):
        try:
            r = requests.get(f"{try_base}{path}", params=params or {}, timeout=12)
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


def get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 12) -> Dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 D-finans/1.0", "Accept": "application/json"}
    r = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


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


def ensure_ibkr_connection(force_reconnect: bool = False):
    require_ibkr_enabled()
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
        ib = ibs.IB()
        ib.connect(IBKR_HOST, IBKR_PORT, clientId=IBKR_CLIENT_ID, timeout=8)
        if not ib.isConnected():
            IBKR_RUNTIME["last_error"] = "IBKR bağlantısı kurulamadı."
            raise RuntimeError("IBKR bağlantısı kurulamadı.")
        IBKR_RUNTIME["ib"] = ib
        IBKR_RUNTIME["connected"] = True
        IBKR_RUNTIME["last_ok"] = now_text()
        IBKR_RUNTIME["last_error"] = ""
        IBKR_RUNTIME["reconnect_count"] = int(IBKR_RUNTIME.get("reconnect_count", 0)) + 1
        return ib, ibs


def ibkr_execute(action):
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            ib, ibs = ensure_ibkr_connection(force_reconnect=(attempt == 1))
            result = action(ib, ibs)
            with IBKR_LOCK:
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
        return {
            "symbol": normalize_symbol(symbol),
            "asset_type": str(asset_type or "STK").upper(),
            "exchange": exchange,
            "currency": currency,
            "data_source": "ibkr",
            "price": round(price, 6),
            "change_24h": round(change_24h, 4),
            "prev_close": round(prev, 6),
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
                "entry_price": safe_float(pos.avgCost),
                "mark_price": 0.0,
                "pnl": 0.0,
                "leverage": "",
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

    if broker == "IBKR":
        snap = ibkr_market_snapshot(symbol, asset_type, exchange, currency)
        price = safe_float(snap.get("price"))
        change = safe_float(snap.get("change_24h"))
        if change > 0.6:
            action = "BUY"
        elif change < -0.6:
            action = "SELL"
        confidence = min(90, int(55 + abs(change) * 11))
        reason = f"IBKR momentum analizi: 24s değişim %{change:.2f}"
    else:
        ai = calculate_ai_signal(symbol, market)
        action = str(ai.get("signal", "WAIT")).upper()
        confidence = int(ai.get("confidence", 50))
        price = safe_float(ai.get("price"))
        reason = str(ai.get("reason", ""))

    if action in ["BUY", "SELL"]:
        confidence = max(0, min(95, confidence + learning_bias(action)))
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
                if do_live:
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


def get_spot_balances() -> List[Dict[str, Any]]:
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


def get_portfolio() -> Dict[str, Any]:
    spot = get_spot_balances()
    futures_positions = get_futures_positions()
    total_unrealized_pnl = sum(safe_float(p.get("pnl")) for p in futures_positions if p.get("symbol") != "HATA")
    return {
        "last_update": now_text(),
        "live_trading": LIVE_TRADING,
        "spot_balances": spot,
        "futures_positions": futures_positions,
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
    }


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


def place_futures_order(symbol: str, side: str, quantity: float, reduce_only: bool = False, order_type: str = "MARKET") -> Dict[str, Any]:
    if not LIVE_TRADING:
        simulated = {
            "simulated": True,
            "message": "LIVE_TRADING=false olduğu için gerçek emir gönderilmedi.",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "reduceOnly": reduce_only,
            "time": now_text(),
        }
        TRADE_LOG.insert(0, simulated)
        return simulated

    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": order_type.upper(),
        "quantity": quantity,
        "reduceOnly": "true" if reduce_only else "false",
    }
    data = signed_request("POST", FUTURES_BASE, "/fapi/v1/order", params)
    log = {"simulated": False, "time": now_text(), "order": data}
    TRADE_LOG.insert(0, log)
    return log


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "app": APP_NAME,
        "ok": True,
        "time": now_text(),
        "live_trading": LIVE_TRADING,
        "api_key_loaded": bool(BINANCE_API_KEY),
        "ibkr_enabled": IBKR_ENABLED,
        "ibkr_connected": bool(IBKR_RUNTIME.get("connected")),
        "auto_trader_enabled": AUTO_TRADER.enabled,
    })


@app.route("/ibkr/health", methods=["GET"])
def ibkr_health():
    try:
        ibkr_ping()
        return jsonify({
            "ok": True,
            "broker": "IBKR",
            "host": IBKR_HOST,
            "port": IBKR_PORT,
            "client_id": IBKR_CLIENT_ID,
            "account": IBKR_ACCOUNT,
            "connected": bool(IBKR_RUNTIME.get("connected")),
            "last_ok": IBKR_RUNTIME.get("last_ok", ""),
            "reconnect_count": int(IBKR_RUNTIME.get("reconnect_count", 0)),
            "time": now_text(),
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "broker": "IBKR",
            "connected": False,
            "error": str(e),
            "last_error": IBKR_RUNTIME.get("last_error", ""),
            "time": now_text(),
        }), 500


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


@app.route("/ibkr/positions", methods=["GET"])
def ibkr_positions():
    try:
        return jsonify({"positions": ibkr_positions_snapshot(), "last_update": now_text(), "broker": "IBKR"})
    except Exception as e:
        return jsonify({"positions": [], "broker": "IBKR", "error": str(e), "last_update": now_text()}), 500


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
            "macro_note": "Bu çıktı yatırım tavsiyesi değildir; küresel makro koşullar için ek veri kaynağıyla birlikte değerlendirilmelidir.",
            "last_update": now_text(),
        })
    except Exception as e:
        return jsonify({"error": str(e), "last_update": now_text()}), 500


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


@app.route("/auto-trader/history", methods=["GET"])
def auto_trader_history():
    with AUTO_LOCK:
        return jsonify({"history": AUTO_HISTORY[:120], "last_update": now_text()})


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
    reduce_only = bool(body.get("reduceOnly", False))

    if quantity <= 0:
        return jsonify({"error": "Miktar 0'dan büyük olmalı."}), 400
    if side not in ["BUY", "SELL"]:
        return jsonify({"error": "side BUY veya SELL olmalı."}), 400

    try:
        result = place_futures_order(symbol, side, quantity, reduce_only=reduce_only)
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
        return jsonify(ibkr_place_market_order(symbol, side, quantity, asset_type, exchange, currency))
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
        result = place_futures_order(symbol, side, size, reduce_only=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "time": now_text()}), 500


@app.route("/trade-log", methods=["GET"])
def trade_log():
    return jsonify({"logs": TRADE_LOG[:100], "last_update": now_text()})


start_background_workers_once()


if __name__ == "__main__":
    print(f"\n{APP_NAME} çalışıyor")
    print(f"Adres: http://127.0.0.1:{PORT}")
    print(f"Canlı emir modu: {LIVE_TRADING}")
    print("Railway/Cloud için /health endpointini kontrol et.\n")
    app.run(host=HOST, port=PORT, debug=False)
