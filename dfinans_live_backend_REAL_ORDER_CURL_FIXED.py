#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import time
import hmac
import hashlib
from urllib.parse import urlencode
from datetime import datetime
from typing import Any, Dict, Optional
import requests
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

APP_NAME = "D-finans Live Backend"
HOST = "0.0.0.0"
PORT = int(os.getenv("DFINANS_BACKEND_PORT", "5055"))

BINANCE_API_KEY = os.getenv("BINANCE_LIVE_API_KEY", os.getenv("BINANCE_API_KEY", ""))
BINANCE_SECRET_KEY = os.getenv("BINANCE_LIVE_SECRET_KEY", os.getenv("BINANCE_SECRET_KEY", ""))
LIVE_TRADING = os.getenv("BINANCE_LIVE_TRADING", os.getenv("LIVE_TRADING", "true")).lower() == "true"

app = Flask(__name__)
CORS(app)

BINANCE_SPOT_BASES = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com",
    "https://data-api.binance.vision",
]
BINANCE_FUTURES_BASES = [
    "https://fapi.binance.com",
    "https://fapi1.binance.com",
    "https://fapi2.binance.com",
    "https://fapi3.binance.com",
]

COINBASE_MAP = {
    "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD", "XRPUSDT": "XRP-USD", "ADAUSDT": "ADA-USD",
}
YAHOO_MAP = {
    "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "SOLUSDT": "SOL-USD",
    "BNBUSDT": "BNB-USD", "XRPUSDT": "XRP-USD", "ADAUSDT": "ADA-USD",
    "AAPL": "AAPL", "NVDA": "NVDA", "MSFT": "MSFT", "TSLA": "TSLA",
    "AMZN": "AMZN", "SPY": "SPY", "QQQ": "QQQ", "XAUUSD": "GC=F",
    "WTI": "CL=F", "EURUSD": "EURUSD=X",
}
COINGECKO_MAP = {
    "BTCUSDT": "bitcoin", "ETHUSDT": "ethereum", "SOLUSDT": "solana",
    "BNBUSDT": "binancecoin", "XRPUSDT": "ripple", "ADAUSDT": "cardano",
}

def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default

def get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 D-finans/1.0", "Accept": "application/json"}
    r = requests.get(url, params=params or {}, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

def try_binance(symbol: str, market: str) -> Optional[Dict[str, Any]]:
    market = market.upper()
    if market == "FUTURES":
        bases, path = BINANCE_FUTURES_BASES, "/fapi/v1/ticker/24hr"
    else:
        bases, path = BINANCE_SPOT_BASES, "/api/v3/ticker/24hr"
    for base in bases:
        try:
            data = get_json(base + path, {"symbol": symbol})
            price = safe_float(data.get("lastPrice") or data.get("weightedAvgPrice"))
            if price > 0:
                return {
                    "source": "binance",
                    "price": price,
                    "change_24h": safe_float(data.get("priceChangePercent")),
                    "high_24h": safe_float(data.get("highPrice")),
                    "low_24h": safe_float(data.get("lowPrice")),
                    "quote_volume": safe_float(data.get("quoteVolume")),
                }
        except Exception as e:
            print("Binance hata:", base, e)
    return None

def try_coinbase(symbol: str) -> Optional[Dict[str, Any]]:
    product = COINBASE_MAP.get(symbol)
    if not product:
        return None
    try:
        data = get_json(f"https://api.coinbase.com/v2/prices/{product}/spot")
        price = safe_float(data.get("data", {}).get("amount"))
        if price > 0:
            return {"source": "coinbase", "price": price, "change_24h": 0.0, "high_24h": price, "low_24h": price, "quote_volume": 0.0}
    except Exception as e:
        print("Coinbase hata:", e)
    return None

def try_yahoo(symbol: str) -> Optional[Dict[str, Any]]:
    ys = YAHOO_MAP.get(symbol)
    if not ys:
        return None
    try:
        data = get_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{ys}", {"range": "1d", "interval": "1m"})
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None
        meta = result[0].get("meta", {})
        price = safe_float(meta.get("regularMarketPrice") or meta.get("previousClose"))
        prev = safe_float(meta.get("previousClose"))
        change = ((price - prev) / prev) * 100.0 if price > 0 and prev > 0 else 0.0
        if price > 0:
            return {
                "source": "yahoo",
                "price": price,
                "change_24h": change,
                "high_24h": safe_float(meta.get("regularMarketDayHigh"), price),
                "low_24h": safe_float(meta.get("regularMarketDayLow"), price),
                "quote_volume": safe_float(meta.get("regularMarketVolume")),
            }
    except Exception as e:
        print("Yahoo hata:", e)
    return None

def try_coingecko(symbol: str) -> Optional[Dict[str, Any]]:
    coin_id = COINGECKO_MAP.get(symbol)
    if not coin_id:
        return None
    try:
        data = get_json("https://api.coingecko.com/api/v3/simple/price", {
            "ids": coin_id, "vs_currencies": "usd",
            "include_24hr_change": "true", "include_24hr_vol": "true"
        })
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
    except Exception as e:
        print("CoinGecko hata:", e)
    return None

def get_market_data(symbol: str, market: str) -> Dict[str, Any]:
    symbol = symbol.upper().replace("/", "")
    for provider in (lambda: try_binance(symbol, market), lambda: try_coinbase(symbol), lambda: try_yahoo(symbol), lambda: try_coingecko(symbol)):
        data = provider()
        if data and data.get("price", 0) > 0:
            return data
    return {"source": "unavailable", "price": 0.0, "change_24h": 0.0, "high_24h": 0.0, "low_24h": 0.0, "quote_volume": 0.0}

def pressure_from_change(change: float) -> Dict[str, float]:
    if change > 1:
        buy = min(68.0, 52.0 + change * 3)
    elif change < -1:
        buy = max(32.0, 48.0 + change * 3)
    else:
        buy = 50.0 + change
    return {"buy_pressure": round(buy, 2), "sell_pressure": round(100 - buy, 2)}


def signed_request(method: str, base: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        raise RuntimeError("Binance API anahtarı eksik. BINANCE_LIVE_API_KEY ve BINANCE_LIVE_SECRET_KEY girilmeli.")

    params2 = dict(params or {})
    params2["timestamp"] = int(time.time() * 1000)
    query = urlencode(params2, doseq=True)
    signature = hmac.new(BINANCE_SECRET_KEY.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    url = f"{base}{path}?{query}&signature={signature}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY, "User-Agent": "D-finans/1.0"}

    if method.upper() == "GET":
        r = requests.get(url, headers=headers, timeout=12)
    elif method.upper() == "POST":
        r = requests.post(url, headers=headers, timeout=12)
    elif method.upper() == "DELETE":
        r = requests.delete(url, headers=headers, timeout=12)
    else:
        raise ValueError("Desteklenmeyen HTTP metodu")

    r.raise_for_status()
    return r.json()



def signed_request_curl(method: str, base: str, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Mac SSL/LibreSSL sorunu için Binance signed request işlemlerini sistem curl ile yapar.
    Bu sayede Python requests SSL hatasına takılmaz.
    """
    if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
        raise RuntimeError("Binance API anahtarı eksik. BINANCE_LIVE_API_KEY ve BINANCE_LIVE_SECRET_KEY girilmeli.")

    params2 = dict(params or {})
    params2["timestamp"] = int(time.time() * 1000)
    params2["recvWindow"] = 10000

    query = urlencode(params2, doseq=True)
    signature = hmac.new(BINANCE_SECRET_KEY.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    url = f"{base}{path}?{query}&signature={signature}"

    cmd = [
        "curl", "-sS", "-X", method.upper(),
        "-H", f"X-MBX-APIKEY: {BINANCE_API_KEY}",
        "-H", "Content-Type: application/json",
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "curl Binance bağlantı hatası")

    raw = result.stdout.strip()
    if not raw:
        return {}

    data = json.loads(raw)
    if isinstance(data, dict) and data.get("code") not in (None, 0):
        raise RuntimeError(f"Binance hata {data.get('code')}: {data.get('msg')}")
    return data

def get_futures_positions() -> list:
    """
    Güvenli pozisyon modu:
    - USDT-M Futures pozisyonlarını okur.
    - COIN-M Futures pozisyonlarına şimdilik dokunmaz.
    - Mevcut COIN-M zarardaki pozisyon korunur.
    """
    positions = []

    # USDT-M FUTURES
    try:
        data = signed_request_curl(
            "GET",
            BINANCE_FUTURES_BASES[0],
            "/fapi/v2/positionRisk",
            {}
        )

        for p in data:
            amount = safe_float(p.get("positionAmt"))

            if abs(amount) <= 0:
                continue

            entry = safe_float(p.get("entryPrice"))
            mark = safe_float(p.get("markPrice"))
            pnl = safe_float(p.get("unRealizedProfit"))
            side = "LONG" if amount > 0 else "SHORT"

            positions.append({
                "id": f"BINANCE-USDTM-{p.get('symbol')}",
                "broker": "Binance",
                "market": "USDT-M Futures",
                "symbol": p.get("symbol", ""),
                "side": side,
                "size": str(abs(amount)),
                "amount": str(abs(amount)),
                "entry_price": str(entry),
                "entry": str(entry),
                "mark_price": str(mark),
                "pnl": str(round(pnl, 4)),
                "leverage": str(p.get("leverage", "")),
            })

    except Exception as e:
        print("USDT-M pozisyon okuma hatası:", e)

    # COIN-M FUTURES KORUMA MODU
    # Mevcut ETHUSD CM pozisyonuna dokunmamak için COIN-M pozisyon okuma/emir tarafı kapalı.
    # VPS + sabit IP kurulduğunda dapi.binance.com tekrar güvenli şekilde açılabilir.

    return positions

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"app": APP_NAME, "ok": True, "port": PORT, "time": now_text()})

@app.route("/market-summary", methods=["GET"])
def market_summary():
    symbol = request.args.get("symbol", "BTCUSDT").upper().replace("/", "")
    market_arg = request.args.get("market", "SPOT").upper()
    market = "FUTURES" if market_arg in ["FUTURES", "VADELI", "VADELİ"] else "SPOT"
    data = get_market_data(symbol, market)
    pressure = pressure_from_change(data["change_24h"])
    price = data["price"]
    change = data["change_24h"]
    buy_pressure = pressure["buy_pressure"]
    sell_pressure = pressure["sell_pressure"]
    return jsonify({
        "symbol": symbol,
        "market": market,
        "price": round(price, 6),
        "change_24h": round(change, 2),
        "high_24h": round(data["high_24h"], 6),
        "low_24h": round(data["low_24h"], 6),
        "quote_volume": round(data["quote_volume"], 2),
        "buy_pressure": buy_pressure,
        "sell_pressure": sell_pressure,
        "whale_status": "Alıcı baskısı" if buy_pressure > 58 else "Satıcı baskısı" if sell_pressure > 58 else "Normal",
        "whale_detail": f"Veri kaynağı: {data['source']}",
        "flow_status": "Pozitif" if change >= 0 else "Negatif",
        "flow_detail": f"24s değişim %{round(change, 2)}",
        "order_cluster_title": "Canlı veri",
        "order_cluster_detail": "Fallback kaynakla güncel fiyat alındı" if price > 0 else "Veri alınamadı",
        "position_density_title": f"Alış %{round(buy_pressure)}",
        "position_density_detail": f"Satış %{round(sell_pressure)}",
        "reversal_zone": "Canlı fiyat geldikten sonra hesaplanır",
        "data_source": data["source"],
        "error_note": "" if price > 0 else "Hiçbir public veri kaynağından fiyat alınamadı.",
        "last_update": now_text(),
    })

@app.route("/positions", methods=["GET"])
def positions():
    return jsonify({
        "positions": get_futures_positions(),
        "last_update": now_text(),
        "api_key_loaded": bool(BINANCE_API_KEY),
        "live_trading": LIVE_TRADING
    })



@app.route("/orders/send", methods=["POST"])
def send_order():
    """
    Gerçek emir endpointi.
    Güvenlik:
    - Sadece Binance USDT-M Futures.
    - COIN-M ve Spot emir kapalı.
    - Varsayılan maksimum emir tutarı 25 USDT.
    - LIVE_TRADING true değilse emir göndermez.
    """
    try:
        body = request.get_json(force=True) or {}

        broker = str(body.get("broker", "binance")).lower()
        market = str(body.get("market", "futures")).lower()
        symbol = str(body.get("symbol", "")).upper().replace("/", "").replace(" PERP", "").strip()
        side_raw = str(body.get("side", "LONG")).upper().strip()
        order_type = str(body.get("type", "MARKET")).upper().strip()
        amount_usdt = safe_float(body.get("amount"), 0)
        leverage = int(safe_float(body.get("leverage"), 1))

        if broker != "binance":
            return jsonify({"ok": False, "error": "Şimdilik sadece Binance destekleniyor."}), 400

        if market not in ["futures", "usdt-m", "usdtm"]:
            return jsonify({"ok": False, "error": "COIN-M ve Spot koruma modunda. Sadece USDT-M Futures açık."}), 400

        if not symbol or not symbol.endswith("USDT"):
            return jsonify({"ok": False, "error": "Sadece USDT-M semboller destekleniyor. Örn: BTCUSDT"}), 400

        if amount_usdt <= 0:
            return jsonify({"ok": False, "error": "Miktar 0'dan büyük olmalı."}), 400

        max_trade = safe_float(os.getenv("MAX_TRADE_USDT", "25"), 25)
        if amount_usdt > max_trade:
            return jsonify({"ok": False, "error": f"Güvenlik limiti: tek emir maksimum {max_trade} USDT."}), 400

        if leverage < 1:
            leverage = 1
        if leverage > 10:
            leverage = 10

        if not LIVE_TRADING:
            return jsonify({
                "ok": False,
                "error": "LIVE_TRADING kapalı. BINANCE_LIVE_TRADING=true yapmadan gerçek emir gönderilmez."
            }), 400

        # Fiyatı public endpointten al. Bu endpoint SSL hatası verirse curl kullanıyoruz.
        ticker = subprocess.run(
            ["curl", "-sS", f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"],
            capture_output=True, text=True, timeout=20
        )
        if ticker.returncode != 0:
            raise RuntimeError(ticker.stderr.strip() or "Fiyat alınamadı")

        ticker_json = json.loads(ticker.stdout)
        mark_price = safe_float(ticker_json.get("price"), 0)
        if mark_price <= 0:
            return jsonify({"ok": False, "error": "Geçerli fiyat alınamadı."}), 400

        quantity = amount_usdt / mark_price

        # Binance quantity precision için exchangeInfo almadan güvenli yuvarlama.
        # Büyük coinlerde 3-4 basamak yeterli; küçük coinlerde 1 basamak gerekebilir.
        if symbol.startswith("BTC"):
            quantity = round(quantity, 3)
        elif symbol.startswith("ETH"):
            quantity = round(quantity, 3)
        else:
            quantity = round(quantity, 1)

        if quantity <= 0:
            return jsonify({"ok": False, "error": "Hesaplanan adet 0. Miktarı artır."}), 400

        # LONG -> BUY, SHORT -> SELL
        binance_side = "BUY" if side_raw in ["LONG", "BUY", "AL"] else "SELL"

        # Kaldıraç ayarla; hata verirse emri kesmeyelim ama loglayalım.
        try:
            signed_request_curl("POST", BINANCE_FUTURES_BASES[0], "/fapi/v1/leverage", {
                "symbol": symbol,
                "leverage": leverage
            })
        except Exception as lev_err:
            print("Kaldıraç ayarlanamadı:", lev_err)

        params = {
            "symbol": symbol,
            "side": binance_side,
            "type": "MARKET",
            "quantity": quantity
        }

        if order_type == "LIMIT":
            price = safe_float(body.get("price"), 0)
            if price <= 0:
                return jsonify({"ok": False, "error": "Limit emir için fiyat gerekli."}), 400
            params["type"] = "LIMIT"
            params["timeInForce"] = "GTC"
            params["price"] = price

        result = signed_request_curl("POST", BINANCE_FUTURES_BASES[0], "/fapi/v1/order", params)

        return jsonify({
            "ok": True,
            "message": "Gerçek USDT-M Futures emri Binance'e iletildi.",
            "symbol": symbol,
            "side": side_raw,
            "binance_side": binance_side,
            "amount_usdt": amount_usdt,
            "quantity": quantity,
            "price": mark_price,
            "result": result,
            "last_update": now_text()
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "last_update": now_text()}), 400

@app.route("/symbols", methods=["GET"])
def symbols():
    market = request.args.get("market", "SPOT").upper()
    return jsonify({"market": market, "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"], "last_update": now_text()})

if __name__ == "__main__":
    print(f"\n{APP_NAME} çalışıyor")
    print(f"Adres: http://127.0.0.1:{PORT}")
    print("Test: /health ve /market-summary\n")
    app.run(host=HOST, port=PORT, debug=False)
