# IBKR Gateway Setup - Production (Railway)

## Önceki Çalışan Setup'ı Restore Ettik

System artık **IBKR Gateway** için hazır. Sistemde 3 seçeneğin var:

---

## **SEÇENEK 1: Railway'de IBKR Gateway Service Ekle (Önerilen)**

### Adımlar:

1. **Railway Dashboard'a git**: https://railway.app/dashboard
2. **Projekti seç**: `dfinans-live-backend-production`
3. **"New"** butonu → **"Service"**
4. **GitHub'tan deploy et**:
   - Owner: `DONDUDURAN`
   - Repository: `dfinans-live-backend`
   - Branch: `main`
   - Root Directory: `ibkr-gateway-image`

5. **Port configuration**:
   - Exposed Port: `4003`
   - Private Port: `4003`

6. **Environment Variables ekle**:
   ```
   IBKR_USERID=<your-interactive-brokers-username>
   IBKR_PASSWORD=<your-interactive-brokers-password>
   IBKR_ACCOUNT=<your-account-number>
   IBC_MODE=gateway
   IBC_GATEWAY=true
   IBC_FIX_USESSL=false
   IBC_FIX_SOCKETPORT=4003
   ```

7. **Deploy et** → Bekle (~5-10 dakika)

8. **Test et**:
   ```bash
   curl https://dfinans-live-backend-production-b43e.up.railway.app/ibkr/health
   ```
   
   Expected response:
   ```json
   {
     "connected": true,
     "account": "YOUR_ACCOUNT",
     "timestamp": "...",
     "circuit_breaker_open": false
   }
   ```

---

## **SEÇENEK 2: Lokal Development (Docker Compose)**

Interactive Brokers TWS'i lokal makine'de çalıştırmak ve Gateway'e bağlanmak:

### Setup:

```bash
# 1. Terminal 1: Backend + Gateway containers başlat
cd /Users/donduduran/dfinans-live-backend
export IBKR_USERID=your_username
export IBKR_PASSWORD=your_password
export IBKR_ACCOUNT=your_account
docker-compose up --build

# 2. Terminal 2: Test et
curl http://localhost:5055/ibkr/health

# 3. Auto-trader başlat
curl -X POST http://localhost:5055/auto-trader/start \
  -H "Content-Type: application/json" \
  -d '{"broker":"IBKR","symbol":"NVDA"}'
```

---

## **SEÇENEK 3: Lokal TWS + Remote Backend**

Interactive Brokers Trader Workstation'ı local'de çalıştır:

### Setup:

1. **TWS'i indir ve kur**:
   - https://www.interactivebrokers.com/en/index.php?f=14099#tws-software
   - Kur ve başlat

2. **TWS Settings**:
   - **Edit** → **Preferences**
   - **API** → **Settings**
   - ☑ **Enable ActiveX and Socket Clients**
   - **Socket Port**: `4003`
   - ☑ **Allow connections from localhost only** (unchecked)
   - **Apply**

3. **Backend environment'ı güncelle**:
   - Production Railway'de (Settings → Variables):
     ```
     IBKR_HOST=<your-machine-ip>
     IBKR_PORT=4003
     ```
   - (Lokal IP adresini kullan, örn: `192.168.1.100`)

4. **Test et**:
   ```bash
   curl https://dfinans-live-backend-production-b43e.up.railway.app/ibkr/health
   ```

---

## Şu Anda Yapılan Değişiklikler:

### Dosyalar:
- ✅ **docker-compose.yml**: IBKR Gateway image ile update
- ✅ **railway.json**: Multi-service Railway config
- ✅ **ibkr-gateway-image/**: Önceki working setup

### Code Status:
- ✅ IBKR_ENABLED = true
- ✅ IBKR_FORCE_DISABLED = false
- ✅ AUTO_TRADER_ENABLED = true
- ✅ AUTO_TRADER_MODE = "live"
- ✅ NVDA-only configuration

### Backend Endpoint'leri:
- `GET /ibkr/health` → Connection status
- `POST /ibkr/circuit-breaker-reset` → Reset connection
- `POST /auto-trader/start` → Start trading
- `GET /auto-trader/status` → Trading status

---

## Troubleshooting:

### "Circuit breaker open"
```bash
curl -X POST https://dfinans-live-backend-production-b43e.up.railway.app/ibkr/circuit-breaker-reset
```

### "Connection timeout"
- IBKR Gateway service running mi? (Option 1)
- TWS açık mı? (Option 3)
- Port 4003 açık mı?
- Firewall?

### Test IBKR connection:
```bash
curl https://dfinans-live-backend-production-b43e.up.railway.app/ibkr/test-connect
```

---

## Sonraki Adımlar:

1. **Seçeneğinden birini seç** → Set up et
2. **Gateway connect olana kadar bekle**
3. `GET /ibkr/health` → `"connected": true` görene kadar kontrol et
4. NVDA auto-trader başlat
5. Trades izle

---

**Notlar:**
- IBKR credentials Railway environment'da secure olarak saklanıyor
- NVDA-only limitation stricter ile uygulanıyor
- USD markets only
- Live trading mode aktif

