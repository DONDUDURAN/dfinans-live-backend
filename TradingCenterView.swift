import SwiftUI

// MARK: - Backend Models

struct TCHealth: Codable {
    let ok: Bool
    let time: String
    let live_trading: Bool
    let api_key_loaded: Bool
}

struct TCSymbolsResponse: Codable {
    let market: String
    let symbols: [String]
    let last_update: String?
}

struct TCOrderbook: Codable {
    let bid_notional: Double
    let ask_notional: Double
    let buy_pressure: Double
    let sell_pressure: Double
    let summary: String
}

struct TCMarketSummary: Codable {
    let symbol: String
    let market: String
    let price: Double?
    let change_24h: Double?
    let high_24h: Double?
    let low_24h: Double?
    let quote_volume: Double?
    let orderbook: TCOrderbook?
    let last_update: String?
    let error: String?
}

struct TCAISignal: Codable {
    let symbol: String
    let market: String
    let price: Double?
    let change_24h: Double?
    let quote_volume: Double?
    let orderbook: TCOrderbook?
    let signal: String
    let confidence: Int
    let reason: String
    let last_update: String
    let engine_enabled: Bool?
    let error: String?
}

struct TCPosition: Codable, Identifiable {
    let id: String
    let broker: String
    let market: String
    let symbol: String
    let side: String
    let size: Double
    let entry_price: Double
    let mark_price: Double
    let pnl: Double
    let leverage: String?
    let error: String?
}

struct TCPositionsResponse: Codable {
    let positions: [TCPosition]
    let last_update: String
}

struct TCSpotBalance: Codable, Identifiable {
    var id: String { asset }
    let asset: String
    let free: Double
    let locked: Double
    let total: Double
    let error: String?
}

struct TCPortfolioResponse: Codable {
    let last_update: String
    let live_trading: Bool
    let spot_balances: [TCSpotBalance]
    let futures_positions: [TCPosition]
    let total_unrealized_pnl: Double
}

struct TCEngineStatus: Codable {
    let enabled: Bool
    let last_update: String
    let last_symbol: String
    let last_market: String
    let last_signal: String
    let confidence: Int
    let reason: String
    let daily_trade_count: Int
    let max_daily_trades: Int
    let risk_profile: String
    let live_trading: Bool
}

// MARK: - ViewModel

@MainActor
final class TradingCenterViewModel: ObservableObject {
    // Mac IP adresini burada değiştir.
    // Örnek: http://192.168.1.40:5055
    @Published var baseURL: String = UserDefaults.standard.string(forKey: "dfinans_backend_base_url") ?? "http://127.0.0.1:5055"

    @Published var selectedBroker: String = "Binance"
    @Published var selectedMarket: String = "FUTURES"
    @Published var selectedSymbol: String = "ETHUSDT"
    @Published var symbols: [String] = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

    @Published var health: TCHealth?
    @Published var marketSummary: TCMarketSummary?
    @Published var aiSignal: TCAISignal?
    @Published var engineStatus: TCEngineStatus?
    @Published var positions: [TCPosition] = []
    @Published var spotBalances: [TCSpotBalance] = []

    @Published var quantityText: String = "0.01"
    @Published var statusText: String = "Backend bağlantısı bekleniyor."
    @Published var isLoading: Bool = false
    @Published var lastRefresh: Date = Date()

    private var timer: Timer?
    private var isRefreshingNow: Bool = false
    private var refreshTick: Int = 0
    private let ibkrSymbols = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ", "BTCUSD", "ETHUSD"]

    func saveBaseURL() {
        UserDefaults.standard.set(baseURL, forKey: "dfinans_backend_base_url")
    }

    func startAutoRefresh() {
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 8.0, repeats: true) { [weak self] _ in
            Task { await self?.loadAll() }
        }
    }

    func stopAutoRefresh() {
        timer?.invalidate()
        timer = nil
    }

    func loadAll() async {
        if isRefreshingNow { return }
        isRefreshingNow = true
        defer { isRefreshingNow = false }
        isLoading = true
        saveBaseURL()
        refreshTick += 1

        async let healthTask: Void = loadHealth()
        async let engineTask: Void = loadEngineStatus()
        async let marketTask: Void = loadMarketAndSignal()
        if refreshTick % 3 == 1 {
            async let symbolTask: Void = loadSymbols()
            async let portfolioTask: Void = loadPortfolio()
            _ = await (symbolTask, portfolioTask)
        }
        _ = await (healthTask, engineTask, marketTask)

        lastRefresh = Date()
        isLoading = false
    }

    func loadHealth() async {
        do {
            health = try await get("/health")
        } catch {
            statusText = "Backend bağlantısı yok: \(error.localizedDescription)"
        }
    }

    func loadSymbols() async {
        if selectedBroker == "IBKR" {
            symbols = ibkrSymbols
            if !symbols.contains(selectedSymbol) {
                selectedSymbol = symbols.first ?? "AAPL"
            }
            return
        }
        do {
            let response: TCSymbolsResponse = try await get("/symbols?market=\(selectedMarket)")
            if !response.symbols.isEmpty {
                symbols = response.symbols
                if !symbols.contains(selectedSymbol) {
                    selectedSymbol = symbols.first ?? "ETHUSDT"
                }
            }
        } catch {
            statusText = "Sembol listesi alınamadı."
        }
    }

    func loadPortfolio() async {
        if selectedBroker == "IBKR" {
            do {
                let response: TCPositionsResponse = try await get("/ibkr/positions")
                positions = response.positions.filter { $0.symbol != "HATA" }
                spotBalances = []
            } catch {
                statusText = "IBKR pozisyonları alınamadı: \(error.localizedDescription)"
            }
            return
        }
        do {
            let response: TCPortfolioResponse = try await get("/portfolio")
            positions = response.futures_positions.filter { $0.symbol != "HATA" }
            spotBalances = response.spot_balances.filter { $0.asset != "HATA" }
        } catch {
            statusText = "Portföy alınamadı: \(error.localizedDescription)"
        }
    }

    func loadEngineStatus() async {
        do {
            engineStatus = try await get("/ai-engine/status")
        } catch {
            statusText = "AI motor durumu alınamadı."
        }
    }

    func loadMarketAndSignal() async {
        let safeSymbol = selectedSymbol.replacingOccurrences(of: "/", with: "")
        do {
            if selectedBroker == "IBKR" {
                let assetType = ibkrAssetType(for: safeSymbol)
                marketSummary = try await get("/ibkr/market-summary?symbol=\(safeSymbol)&asset_type=\(assetType)&exchange=SMART&currency=USD")
                aiSignal = try await get("/ibkr/ai-signal?symbol=\(safeSymbol)&asset_type=\(assetType)&exchange=SMART&currency=USD")
            } else {
                marketSummary = try await get("/market-summary?symbol=\(safeSymbol)&market=\(selectedMarket)")
                aiSignal = try await get("/ai-signal?symbol=\(safeSymbol)&market=\(selectedMarket)")
            }
            statusText = "Canlı veri güncellendi."
        } catch {
            statusText = "Piyasa/AI verisi alınamadı: \(error.localizedDescription)"
        }
    }

    func setEngine(_ enabled: Bool) async {
        do {
            engineStatus = try await post(enabled ? "/ai-engine/on" : "/ai-engine/off", body: [:])
            statusText = enabled ? "AI motor açıldı." : "AI motor kapatıldı."
        } catch {
            statusText = "AI motor durumu değiştirilemedi."
        }
    }

    func sendManualOrder(side: String) async {
        guard let quantity = Double(quantityText.replacingOccurrences(of: ",", with: ".")), quantity > 0 else {
            statusText = "Miktar geçerli değil."
            return
        }
        let body: [String: Any] = [
            "symbol": selectedSymbol.replacingOccurrences(of: "/", with: ""),
            "side": side,
            "quantity": quantity
        ]
        do {
            if selectedBroker == "IBKR" {
                let symbol = selectedSymbol.replacingOccurrences(of: "/", with: "")
                let assetType = ibkrAssetType(for: symbol)
                var ibkrBody = body
                ibkrBody["asset_type"] = assetType
                ibkrBody["exchange"] = "SMART"
                ibkrBody["currency"] = "USD"
                let _: [String: JSONValue] = try await post("/ibkr/manual-order", body: ibkrBody)
            } else {
                var binanceBody = body
                binanceBody["reduceOnly"] = false
                let _: [String: JSONValue] = try await post("/manual-order", body: binanceBody)
            }
            statusText = "Manuel \(side) emri backend'e gönderildi."
            await loadAll()
        } catch {
            statusText = "Emir gönderilemedi: \(error.localizedDescription)"
        }
    }

    private func ibkrAssetType(for symbol: String) -> String {
        let clean = symbol.uppercased().replacingOccurrences(of: "-", with: "").replacingOccurrences(of: "/", with: "")
        if ["BTCUSD", "ETHUSD"].contains(clean) {
            return "CRYPTO"
        }
        return "STK"
    }

    func closePosition(_ position: TCPosition) async {
        do {
            let _: [String: JSONValue] = try await post("/close-position", body: ["symbol": position.symbol])
            statusText = "\(position.symbol) kapatma emri gönderildi."
            await loadAll()
        } catch {
            statusText = "Pozisyon kapatılamadı: \(error.localizedDescription)"
        }
    }

    private func makeURL(_ path: String) throws -> URL {
        let cleaned = baseURL.trimmingCharacters(in: .whitespacesAndNewlines).trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard let url = URL(string: cleaned + path) else { throw URLError(.badURL) }
        return url
    }

    private func get<T: Decodable>(_ path: String) async throws -> T {
        let url = try makeURL(path)
        let (data, response) = try await URLSession.shared.data(from: url)
        try validate(response, data: data)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func post<T: Decodable>(_ path: String, body: [String: Any]) async throws -> T {
        let url = try makeURL(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response, data: data)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func validate(_ response: URLResponse, data: Data) throws {
        if let http = response as? HTTPURLResponse, http.statusCode >= 400 {
            let text = String(data: data, encoding: .utf8) ?? "Bilinmeyen hata"
            throw NSError(domain: "DfinansBackend", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: text])
        }
    }
}

// Basit JSON decode yardımcı tipi
struct JSONValue: Codable {}

// MARK: - View

struct TradingCenterView: View {
    @StateObject private var vm = TradingCenterViewModel()

    private let brokers = ["Binance", "IBKR"]
    private let markets = ["SPOT", "FUTURES"]

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(red: 0.02, green: 0.09, blue: 0.07), Color(red: 0.00, green: 0.18, blue: 0.12)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 16) {
                    header
                    backendCard
                    selectorCard
                    aiDecisionCard
                    marketCard
                    manualOrderCard
                    positionsCard
                    spotBalancesCard
                    statusCard
                }
                .padding(16)
            }
        }
        .foregroundColor(.white)
        .onAppear {
            Task { await vm.loadAll() }
            vm.startAutoRefresh()
        }
        .onDisappear {
            vm.stopAutoRefresh()
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 6) {
                Text("D-finans")
                    .font(.system(size: 30, weight: .black))
                Text("Trading Center")
                    .font(.headline)
                    .foregroundColor(.white.opacity(0.82))
                Text("Canlı veri • AI analiz • Manuel işlem • Açık pozisyon")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.70))
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 8) {
                liveBadge
                Button {
                    Task { await vm.loadAll() }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.headline)
                        .padding(10)
                        .background(Color.white.opacity(0.12))
                        .clipShape(Circle())
                }
            }
        }
    }

    private var liveBadge: some View {
        let isLive = vm.health?.live_trading == true
        return Text(isLive ? "GERÇEK EMİR AÇIK" : "EMİR KORUMALI")
            .font(.caption.bold())
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(isLive ? Color.red.opacity(0.80) : Color.green.opacity(0.26))
            .clipShape(Capsule())
    }

    private var backendCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Backend Bağlantısı")
                        .font(.headline)
                    Spacer()
                    Text(vm.health?.ok == true ? "Bağlı" : "Kontrol et")
                        .font(.caption.bold())
                        .foregroundColor(vm.health?.ok == true ? .green : .orange)
                }

                TextField("http://Mac-IP:5055", text: $vm.baseURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled(true)
                    .padding(12)
                    .background(Color.black.opacity(0.25))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .foregroundColor(.white)

                HStack {
                    infoPill(title: "API", value: vm.health?.api_key_loaded == true ? "Yüklü" : "Eksik")
                    infoPill(title: "Son", value: vm.health?.time ?? "-")
                }
            }
        }
    }

    private var selectorCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                Text("Varlık Seçimi")
                    .font(.headline)

                Picker("Broker", selection: $vm.selectedBroker) {
                    ForEach(brokers, id: \.self) { Text($0) }
                }
                .pickerStyle(.segmented)
                .onChange(of: vm.selectedBroker) { newValue in
                    if newValue == "IBKR" {
                        vm.selectedMarket = "SPOT"
                        if vm.selectedSymbol.hasSuffix("USDT") {
                            vm.selectedSymbol = "AAPL"
                        }
                    }
                    Task { await vm.loadAll() }
                }

                Picker("Piyasa", selection: $vm.selectedMarket) {
                    ForEach(markets, id: \.self) { Text($0) }
                }
                .pickerStyle(.segmented)
                .onChange(of: vm.selectedMarket) { _ in
                    Task { await vm.loadAll() }
                }

                Picker("Sembol", selection: $vm.selectedSymbol) {
                    ForEach(vm.symbols, id: \.self) { symbol in
                        Text(symbol).tag(symbol)
                    }
                }
                .pickerStyle(.menu)
                .padding(12)
                .frame(maxWidth: .infinity)
                .background(Color.black.opacity(0.25))
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .onChange(of: vm.selectedSymbol) { _ in
                    Task { await vm.loadMarketAndSignal() }
                }
            }
        }
    }

    private var aiDecisionCard: some View {
        card {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("dd AI Yorumu")
                            .font(.headline)
                        Text(vm.aiSignal?.last_update ?? "Henüz güncellenmedi")
                            .font(.caption)
                            .foregroundColor(.white.opacity(0.65))
                    }
                    Spacer()
                    Toggle("", isOn: Binding(
                        get: { vm.engineStatus?.enabled ?? false },
                        set: { newValue in Task { await vm.setEngine(newValue) } }
                    ))
                    .labelsHidden()
                }

                HStack(spacing: 10) {
                    bigMetric(title: "Sinyal", value: translatedSignal(vm.aiSignal?.signal ?? "WAIT"))
                    bigMetric(title: "Güven", value: "%\(vm.aiSignal?.confidence ?? 0)")
                    bigMetric(title: "AI", value: (vm.engineStatus?.enabled ?? false) ? "Açık" : "Kapalı")
                }

                Text(vm.aiSignal?.reason ?? "AI yorumu bekleniyor.")
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.86))
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var marketCard: some View {
        card {
            VStack(alignment: .leading, spacing: 14) {
                Text("Canlı Piyasa Özeti")
                    .font(.headline)

                HStack(spacing: 10) {
                    bigMetric(title: "Fiyat", value: formatPrice(vm.marketSummary?.price))
                    bigMetric(title: "24s", value: formatPercent(vm.marketSummary?.change_24h))
                    bigMetric(title: "Hacim", value: shortNumber(vm.marketSummary?.quote_volume))
                }

                if let ob = vm.marketSummary?.orderbook ?? vm.aiSignal?.orderbook {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Emir Defteri Baskısı")
                            .font(.subheadline.bold())
                        GeometryReader { geo in
                            HStack(spacing: 0) {
                                Rectangle()
                                    .fill(Color.green.opacity(0.65))
                                    .frame(width: geo.size.width * CGFloat(ob.buy_pressure / 100.0))
                                Rectangle()
                                    .fill(Color.red.opacity(0.65))
                                    .frame(width: geo.size.width * CGFloat(ob.sell_pressure / 100.0))
                            }
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }
                        .frame(height: 16)

                        HStack {
                            Text("Alış %\(String(format: "%.1f", ob.buy_pressure))")
                            Spacer()
                            Text("Satış %\(String(format: "%.1f", ob.sell_pressure))")
                        }
                        .font(.caption.bold())
                        .foregroundColor(.white.opacity(0.80))
                    }
                }
            }
        }
    }

    private var manualOrderCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                Text("Manuel İşlem")
                    .font(.headline)

                HStack {
                    TextField("Miktar", text: $vm.quantityText)
                        .keyboardType(.decimalPad)
                        .padding(12)
                        .background(Color.black.opacity(0.25))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .foregroundColor(.white)

                    Button("LONG") {
                        Task { await vm.sendManualOrder(side: "BUY") }
                    }
                    .buttonStyle(TradeButtonStyle(kind: .buy))

                    Button("SHORT") {
                        Task { await vm.sendManualOrder(side: "SELL") }
                    }
                    .buttonStyle(TradeButtonStyle(kind: .sell))
                }

                Text("Gerçek emir için backend tarafında LIVE_TRADING=true olmalı. Kapalıysa emir simülasyon loguna düşer.")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.60))
            }
        }
    }

    private var positionsCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("Açık Futures Pozisyonları")
                        .font(.headline)
                    Spacer()
                    Text("\(vm.positions.count)")
                        .font(.caption.bold())
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color.white.opacity(0.12))
                        .clipShape(Capsule())
                }

                if vm.positions.isEmpty {
                    emptyText("Açık futures pozisyon bulunamadı veya API yetkisi eksik.")
                } else {
                    ForEach(vm.positions) { p in
                        positionRow(p)
                    }
                }
            }
        }
    }

    private var spotBalancesCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                Text("Spot Cüzdan")
                    .font(.headline)

                if vm.spotBalances.isEmpty {
                    emptyText("Spot bakiye bulunamadı veya API yetkisi eksik.")
                } else {
                    ForEach(vm.spotBalances.prefix(12)) { b in
                        HStack {
                            Text(b.asset)
                                .font(.subheadline.bold())
                            Spacer()
                            Text(formatNumber(b.total))
                                .font(.subheadline.monospacedDigit())
                        }
                        .padding(10)
                        .background(Color.black.opacity(0.18))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
            }
        }
    }

    private var statusCard: some View {
        card {
            VStack(alignment: .leading, spacing: 6) {
                Text("Durum")
                    .font(.headline)
                Text(vm.statusText)
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.82))
                Text("Son yenileme: \(vm.lastRefresh.formatted(date: .omitted, time: .standard))")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.60))
            }
        }
    }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        content()
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: 22)
                    .fill(Color.white.opacity(0.08))
                    .overlay(
                        RoundedRectangle(cornerRadius: 22)
                            .stroke(Color.white.opacity(0.12), lineWidth: 1)
                    )
            )
    }

    private func infoPill(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.55))
            Text(value)
                .font(.caption.bold())
                .lineLimit(1)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.black.opacity(0.20))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func bigMetric(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.58))
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .lineLimit(1)
                .minimumScaleFactor(0.65)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.black.opacity(0.22))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private func positionRow(_ p: TCPosition) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                VStack(alignment: .leading, spacing: 3) {
                    Text(p.symbol)
                        .font(.headline)
                    Text("\(p.side) • \(p.market) • \(p.leverage ?? "-")x")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.65))
                }
                Spacer()
                Text(formatSigned(p.pnl))
                    .font(.headline.monospacedDigit())
                    .foregroundColor(p.pnl >= 0 ? .green : .red)
            }

            HStack {
                infoPill(title: "Miktar", value: formatNumber(p.size))
                infoPill(title: "Giriş", value: formatPrice(p.entry_price))
                infoPill(title: "Mark", value: formatPrice(p.mark_price))
            }

            Button("Pozisyonu Kapat") {
                Task { await vm.closePosition(p) }
            }
            .font(.subheadline.bold())
            .padding(11)
            .frame(maxWidth: .infinity)
            .background(Color.red.opacity(0.28))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
        .padding(12)
        .background(Color.black.opacity(0.18))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }

    private func emptyText(_ text: String) -> some View {
        Text(text)
            .font(.subheadline)
            .foregroundColor(.white.opacity(0.60))
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.black.opacity(0.16))
            .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    private func translatedSignal(_ signal: String) -> String {
        switch signal {
        case "BUY": return "AL"
        case "SELL": return "SAT"
        case "WATCH_BUY": return "AL İzle"
        case "WATCH_SELL": return "SAT İzle"
        default: return "Bekle"
        }
    }

    private func formatPrice(_ value: Double?) -> String {
        guard let value else { return "-" }
        if value >= 1000 { return String(format: "%.2f", value) }
        if value >= 1 { return String(format: "%.4f", value) }
        return String(format: "%.6f", value)
    }

    private func formatPercent(_ value: Double?) -> String {
        guard let value else { return "-" }
        return String(format: "%+.2f%%", value)
    }

    private func formatNumber(_ value: Double) -> String {
        if value >= 1000 { return String(format: "%.2f", value) }
        if value >= 1 { return String(format: "%.4f", value) }
        return String(format: "%.6f", value)
    }

    private func formatSigned(_ value: Double) -> String {
        return String(format: "%+.2f USDT", value)
    }

    private func shortNumber(_ value: Double?) -> String {
        guard let value else { return "-" }
        if value >= 1_000_000_000 { return String(format: "%.2fB", value / 1_000_000_000) }
        if value >= 1_000_000 { return String(format: "%.2fM", value / 1_000_000) }
        if value >= 1_000 { return String(format: "%.1fK", value / 1_000) }
        return String(format: "%.0f", value)
    }
}

// MARK: - Button Style

enum TradeButtonKind { case buy, sell }

struct TradeButtonStyle: ButtonStyle {
    let kind: TradeButtonKind

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.subheadline.bold())
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(kind == .buy ? Color.green.opacity(0.72) : Color.red.opacity(0.72))
            .foregroundColor(.white)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
    }
}

#Preview {
    TradingCenterView()
}
