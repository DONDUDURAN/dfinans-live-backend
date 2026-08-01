import math
from unittest import mock

import pytest


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        (None, 1.5, 1.5),
        ("12.34", 0.0, 12.34),
        ("not-a-number", 9.9, 9.9),
    ],
)
def test_safe_float_handles_invalid_values(backend_module, value, default, expected):
    assert backend_module.safe_float(value, default) == expected


def test_normalize_symbol_removes_common_separators(backend_module):
    assert backend_module.normalize_symbol(" eth/usdt- ") == "ETHUSDT"


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        (
            {"entry_price": 100, "mark_price": 110, "pnl": 20, "size": 1, "leverage": 10, "side": "LONG"},
            200.0,
        ),
        (
            {"entry_price": 100, "mark_price": 90, "pnl": 0, "size": 2, "leverage": 5, "side": "SHORT"},
            50.0,
        ),
        (
            {"entry_price": 100, "mark_price": 110, "pnl": 0, "size": 2, "leverage": 5, "side": "SHORT"},
            -50.0,
        ),
        (
            {"entry_price": 0, "mark_price": 110, "pnl": 10, "size": 1, "leverage": 2, "side": "LONG"},
            0.0,
        ),
    ],
)
def test_binance_position_profit_pct_handles_long_short_and_invalid_input(backend_module, position, expected):
    assert backend_module.binance_position_profit_pct(position) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        ({"avgCost": 100, "pnl": 10, "position": 2, "side": "LONG"}, 5.0),
        ({"avgCost": 100, "mark_price": 90, "size": 0, "side": "SHORT"}, 10.0),
        ({"avgCost": 100, "mark_price": 90, "size": 0, "side": "LONG"}, -10.0),
        ({"avgCost": 0, "mark_price": 90, "size": 1, "side": "LONG"}, 0.0),
        # market_value/pnl IBKR'in kendi portfolio() kaydindan geldigi icin
        # avgCost yanlis/tutarsiz olsa bile (ornegin HSBA'da gorulen eski/
        # harmanlanmis maliyet bazi) dogru sonucu verir - bu yuzden artik
        # oncelikli yol: cost_basis = market_value - pnl.
        ({"avgCost": 1849.308, "mark_price": 1527.0, "pnl": -0.9, "market_value": 89.1, "position": 1, "side": "LONG"}, -1.0),
    ],
)
def test_ibkr_position_profit_pct_handles_cost_basis_and_fallback(backend_module, position, expected):
    assert backend_module.ibkr_position_profit_pct(position) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("position", "current_price", "expected"),
    [
        ({"avg_cost": 100}, 110, 10.0),
        ({"avg_cost": 100}, 95, -5.0),
        ({"avg_cost": 0}, 110, 0.0),
        ({"avg_cost": 100}, 0, 0.0),
    ],
)
def test_spot_position_profit_pct_handles_gain_loss_and_zero_basis(backend_module, position, current_price, expected):
    assert backend_module.spot_position_profit_pct(position, current_price) == pytest.approx(expected)


def test_round_quantity_to_step_rounds_down_to_exchange_step(backend_module, monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "get_symbol_filters",
        lambda symbol, market: {"step_size": 0.001, "min_qty": 0.001, "min_notional": 5.0},
    )

    rounded, error = backend_module.round_quantity_to_step("ETHUSDT", "FUTURES", 0.123456, price=3000)

    assert rounded == pytest.approx(0.123)
    assert error is None


def test_get_symbol_filters_uses_mocked_exchange_info_offline(backend_module):
    backend_module._SYMBOL_FILTERS_CACHE.clear()
    mocked_exchange_info = {
        "symbols": [
            {
                "filters": [
                    {"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.01"},
                    {"filterType": "MIN_NOTIONAL", "minNotional": "50"},
                ]
            }
        ]
    }

    with mock.patch.object(backend_module, "public_get", return_value=mocked_exchange_info) as public_get:
        first = backend_module.get_symbol_filters("ETHUSDT", "FUTURES")
        second = backend_module.get_symbol_filters("ETHUSDT", "FUTURES")

    assert first["step_size"] == pytest.approx(0.001)
    assert first["min_qty"] == pytest.approx(0.01)
    assert first["min_notional"] == pytest.approx(50.0)
    assert second == first
    public_get.assert_called_once()


def test_round_quantity_to_step_rejects_below_min_qty(backend_module, monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "get_symbol_filters",
        lambda symbol, market: {"step_size": 0.001, "min_qty": 0.01, "min_notional": 0.0},
    )

    rounded, error = backend_module.round_quantity_to_step("ETHUSDT", "FUTURES", 0.0099, price=3000)

    assert rounded == 0.0
    assert "minimum miktar" in error


def test_round_quantity_to_step_rejects_below_min_notional_for_open_orders(backend_module, monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "get_symbol_filters",
        lambda symbol, market: {"step_size": 0.001, "min_qty": 0.001, "min_notional": 50.0},
    )

    rounded, error = backend_module.round_quantity_to_step("ETHUSDT", "FUTURES", 0.0059, price=4000)

    assert rounded == 0.0
    assert "minimum işlem büyüklüğünün" in error


def test_round_quantity_to_step_allows_reduce_only_below_min_notional_regression(backend_module, monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "get_symbol_filters",
        lambda symbol, market: {"step_size": 0.001, "min_qty": 0.001, "min_notional": 50.0},
    )

    rounded, error = backend_module.round_quantity_to_step(
        "ETHUSDT",
        "FUTURES",
        0.0059,
        price=4000,
        skip_min_notional=True,
    )

    assert rounded == pytest.approx(0.005)
    assert error is None


def test_round_quantity_to_step_handles_floating_point_step_edges(backend_module, monkeypatch):
    monkeypatch.setattr(
        backend_module,
        "get_symbol_filters",
        lambda symbol, market: {"step_size": 0.1, "min_qty": 0.1, "min_notional": 0.0},
    )

    rounded, error = backend_module.round_quantity_to_step("BTCUSDT", "SPOT", 0.1 + 0.2, price=1)

    assert rounded == pytest.approx(0.3)
    assert error is None
    assert math.isclose(rounded, 0.3)


def test_db_position_add_log_tracks_once_per_day(backend_module, isolated_runtime_db, runtime_db_connection, monkeypatch):
    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-12 09:00:00")

    assert backend_module.db_position_added_today("BINANCE", "ETHUSDT") is False

    backend_module.db_log_position_add("BINANCE", "ETHUSDT")

    assert backend_module.db_position_added_today("BINANCE", "ETHUSDT") is True
    row = runtime_db_connection.execute(
        "SELECT broker, symbol, add_date, last_add_at FROM position_add_log"
    ).fetchone()
    assert row == ("BINANCE", "ETHUSDT", "2026-07-12", "2026-07-12 09:00:00")


def test_db_log_position_add_updates_existing_same_day_row(backend_module, isolated_runtime_db, runtime_db_connection, monkeypatch):
    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-12 09:00:00")
    backend_module.db_log_position_add("IBKR", "AAPL")

    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-12 11:30:00")
    backend_module.db_log_position_add("IBKR", "AAPL")

    count = runtime_db_connection.execute(
        "SELECT COUNT(*) FROM position_add_log WHERE broker = ? AND symbol = ? AND add_date = ?",
        ("IBKR", "AAPL", "2026-07-12"),
    ).fetchone()[0]
    last_add_at = runtime_db_connection.execute(
        "SELECT last_add_at FROM position_add_log WHERE broker = ? AND symbol = ? AND add_date = ?",
        ("IBKR", "AAPL", "2026-07-12"),
    ).fetchone()[0]

    assert count == 1
    assert last_add_at == "2026-07-12 11:30:00"


def test_db_position_added_today_resets_on_next_day(backend_module, isolated_runtime_db, monkeypatch):
    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-12 09:00:00")
    backend_module.db_log_position_add("BINANCE", "SOLUSDT")

    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-13 08:00:00")

    assert backend_module.db_position_added_today("BINANCE", "SOLUSDT") is False


def _insert_position_closure(conn, broker, symbol, close_reason, created_at):
    conn.execute(
        """
        INSERT INTO position_closures
            (id, created_at, broker, symbol, side, qty, entry_price, exit_price,
             realized_pnl, realized_pnl_pct, close_reason, detail)
        VALUES (?, ?, ?, ?, 'LONG', 1, 10, 9, -1, -10, ?, '{}')
        """,
        (f"{broker}-{symbol}-{created_at}", created_at, broker, symbol, close_reason),
    )
    conn.commit()


def test_symbol_in_stop_loss_cooldown_blocks_within_window(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    from datetime import datetime, timedelta

    recent = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    _insert_position_closure(runtime_db_connection, "IBKR", "SHEL", "STOP_LOSS", recent)

    remaining = backend_module._symbol_in_stop_loss_cooldown("IBKR", "SHEL", 8.0)

    assert remaining is not None
    assert 5.5 < remaining < 6.5


def test_symbol_in_stop_loss_cooldown_clears_after_window(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    from datetime import datetime, timedelta

    old = (datetime.now() - timedelta(hours=20)).strftime("%Y-%m-%d %H:%M:%S")
    _insert_position_closure(runtime_db_connection, "IBKR", "HSBA", "STOP_LOSS", old)

    assert backend_module._symbol_in_stop_loss_cooldown("IBKR", "HSBA", 8.0) is None


def test_symbol_in_stop_loss_cooldown_ignores_non_stop_loss_and_disabled(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    from datetime import datetime, timedelta

    recent = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    _insert_position_closure(runtime_db_connection, "IBKR", "USO", "TAKE_PROFIT", recent)

    assert backend_module._symbol_in_stop_loss_cooldown("IBKR", "USO", 8.0) is None
    assert backend_module._symbol_in_stop_loss_cooldown("IBKR", "SHEL", 0.0) is None


def test_lse_grandfather_exempts_existing_position_from_tight_threshold(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    backend_module.db_grandfather_lse_symbol("SHEL")

    assert backend_module.db_is_lse_symbol_grandfathered("SHEL") is True
    assert backend_module.db_is_lse_symbol_grandfathered("HSBA") is False


def test_lse_grandfather_cleared_on_full_position_closure(
    backend_module, isolated_runtime_db, runtime_db_connection, monkeypatch
):
    monkeypatch.setattr(backend_module, "now_text", lambda: "2026-07-26 13:00:00")
    backend_module.db_grandfather_lse_symbol("HSBA")
    assert backend_module.db_is_lse_symbol_grandfathered("HSBA") is True

    backend_module.db_record_position_closure(
        "IBKR", "HSBA", "LONG", 10, 18.49, 15.28, -32.1, -16.06, "STOP_LOSS", "{}"
    )

    assert backend_module.db_is_lse_symbol_grandfathered("HSBA") is False


def test_technical_signal_bias_hard_blocks_sell_on_confirmed_reversal_up(
    backend_module, monkeypatch
):
    """Kullanicinin talebi: 'BTC dustu, artik donus yapacak yukari dogru
    SHORT acmisiz' - RSI asiri satimda (<=25) VE MACD histogram zaten
    pozitife donmusse, trend-yonundeki (chasing) SELL sert engellenmeli."""
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {
            "rsi_14": 18.0,
            "macd_histogram": 41.3,
            "sma_20": None,
            "sma_50": None,
            "last_close": None,
            "volume_ratio": None,
        },
    )

    result = backend_module.get_technical_signal_bias("BTCUSDT", "Futures", "BINANCE_FUTURES", "SELL")

    assert result["hard_block"] is True
    assert any("SERT ENGEL" in note for note in result["notes"])


def test_technical_signal_bias_hard_blocks_buy_on_confirmed_reversal_down(
    backend_module, monkeypatch
):
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {
            "rsi_14": 82.0,
            "macd_histogram": -12.5,
            "sma_20": None,
            "sma_50": None,
            "last_close": None,
            "volume_ratio": None,
        },
    )

    result = backend_module.get_technical_signal_bias("BTCUSDT", "Futures", "BINANCE_FUTURES", "BUY")

    assert result["hard_block"] is True
    assert any("SERT ENGEL" in note for note in result["notes"])


def test_technical_signal_bias_no_hard_block_when_macd_not_yet_reversed(
    backend_module, monkeypatch
):
    """RSI asiri uc bolgede olsa bile MACD histogram HENUZ ters yone
    donmemisse (donus teyitli degil), sadece yumusak bias uygulanir - sert
    engel devreye girmez."""
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {
            "rsi_14": 18.0,
            "macd_histogram": -5.0,
            "sma_20": None,
            "sma_50": None,
            "last_close": None,
            "volume_ratio": None,
        },
    )

    result = backend_module.get_technical_signal_bias("BTCUSDT", "Futures", "BINANCE_FUTURES", "SELL")

    assert result["hard_block"] is False
    assert result["bias"] < 0


def test_resolve_trailing_take_profit_not_armed_below_target(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Kar hedefine henuz ulasilmadiysa (peak < take_profit_pct), trailing
    ARMED degildir - islem kapanmamali."""
    hit = backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "BTCUSDT", 60000.0, 1.0, 2.0)
    assert hit is False


def test_resolve_trailing_take_profit_arms_and_lets_winner_run(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Kullanicinin talebi: 'trailing stop ekle, kazananlari uzatalim'. Fiyat
    sabit hedefi (%2) gectiginde HEMEN KAPANMAMALI - zirve %5'e kadar
    yukselirse (armed), sadece zirveden belirgin bir geri cekilme
    (TRAILING_GIVEBACK_PCT) olunca kapanmali."""
    # Zirveye dogru tirmanma: hicbiri kapanmamali (hala zirvenin en yuksek noktasi).
    assert backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "BTCUSDT", 60000.0, 2.5, 2.0) is False
    assert backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "BTCUSDT", 60000.0, 5.0, 2.0) is False
    # Zirve %5 iken, kar %5 - giveback (1.2) = %3.8'in USTUNDE kaldigi surece kapanmamali.
    assert backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "BTCUSDT", 60000.0, 4.0, 2.0) is False
    # Zirveden giveback kadar geri cekilince (>=%1.2 dusus) artik kapanmali.
    assert backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "BTCUSDT", 60000.0, 3.5, 2.0) is True


def test_resolve_trailing_take_profit_resets_on_new_entry_price(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Pozisyon kapanip ayni sembolde YENI bir giris fiyatiyla acildiginda,
    eski zirveden miras kalmamali - sifirdan bir dongu olarak izlenmeli."""
    backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "ETHUSDT", 2000.0, 5.0, 2.0)
    # Ayni giris fiyatiyla devam - hala armed, giveback esigi ayni.
    assert backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "ETHUSDT", 2000.0, 4.5, 2.0) is False

    # Yeni pozisyon dongusu (farkli giris fiyati) - zirve sifirlanmali, %1
    # kar hemen kapanmaya yol acmamali (henuz hedefe bile ulasmadi).
    hit = backend_module.resolve_trailing_take_profit("BINANCE_FUTURES", "ETHUSDT", 2100.0, 1.0, 2.0)
    assert hit is False


def test_compute_dynamic_take_profit_pct_never_shrinks_base_target(
    backend_module, monkeypatch
):
    """ATR/Odul-Risk hesaplamalari hicbir zaman orijinal sabit hedeften
    KUCUK bir sonuc uretmemeli - sadece buyutur."""
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {"atr_pct": 0.1},
    )
    result = backend_module.compute_dynamic_take_profit_pct("AAPL", "STK", "IBKR", 2.0, 4.0)
    assert result["take_profit_pct"] >= 2.0


def test_compute_dynamic_take_profit_pct_enforces_minimum_reward_risk_ratio(
    backend_module, monkeypatch
):
    """Kullanicinin talebi: 30 gunluk analizde ort. kazanc %1.86 iken ort.
    kayip %9.79 idi - kar hedefi artik kullanilan zarar-kes esiginin
    MIN_REWARD_RISK_RATIO kati kadarindan asla kucuk olamaz."""
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {"atr_pct": None},
    )
    # base_take_profit_pct=2.0 ama stop_loss_pct=20.0 -> min hedef 20*1.5=30.0 olmali.
    result = backend_module.compute_dynamic_take_profit_pct("HSBA", "STK", "IBKR", 2.0, 20.0)
    assert result["take_profit_pct"] == pytest.approx(20.0 * backend_module.MIN_REWARD_RISK_RATIO)


def test_compute_dynamic_take_profit_pct_widens_with_atr_and_leverage(
    backend_module, monkeypatch
):
    """Volatilite (ATR%) yuksekse ve kaldirac varsa, hedef bunlara gore
    olceklenerek buyutulmeli."""
    monkeypatch.setattr(
        backend_module,
        "get_technical_indicator_snapshot",
        lambda symbol, market, broker: {"atr_pct": 1.0},
    )
    result = backend_module.compute_dynamic_take_profit_pct(
        "BTCUSDT", "FUTURES", "BINANCE_FUTURES", 2.0, 6.0, leverage_multiplier=2.0,
    )
    expected_atr_target = 1.0 * backend_module.ATR_TARGET_MULTIPLIER * 2.0
    assert result["take_profit_pct"] >= expected_atr_target


def _seed_closures(backend_module, broker, symbol, pnl_pcts):
    for pct in pnl_pcts:
        backend_module.db_record_position_closure(
            broker=broker,
            symbol=symbol,
            side="LONG",
            qty=1.0,
            entry_price=100.0,
            exit_price=100.0 * (1.0 + pct / 100.0),
            realized_pnl=pct,
            realized_pnl_pct=pct,
            close_reason="TAKE_PROFIT" if pct > 0 else "STOP_LOSS",
            detail="test",
        )


def test_kelly_position_size_scale_fails_open_below_min_trades(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Kullanicinin talebi: 'pozisyon boyutlandirma yapalim' (Kelly-kriteri).
    Yeterli gecmis islem (KELLY_MIN_TRADES) yoksa fail-open olmali - boyut
    degismemeli (x1.0)."""
    _seed_closures(backend_module, "BINANCE_FUTURES", "ADAUSDT", [2.0, -1.0])
    result = backend_module.get_kelly_position_size_scale("ADAUSDT", "BINANCE_FUTURES")
    assert result["qty_scale"] == 1.0


def test_kelly_position_size_scale_shrinks_for_losing_symbol(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Kullanicinin talebi: surekli zarar eden bir sembolde (dusuk kazanma
    orani, kucuk kazanc/buyuk kayip) pozisyon boyutu otomatik olarak
    kuculmeli."""
    _seed_closures(
        backend_module,
        "IBKR",
        "HSBA",
        [1.0, -8.0, 1.0, -9.0, -7.0, 1.0, -8.0],
    )
    result = backend_module.get_kelly_position_size_scale("HSBA", "IBKR")
    assert result["qty_scale"] < 1.0
    assert result["qty_scale"] >= backend_module.KELLY_MIN_SCALE


def test_kelly_position_size_scale_grows_for_winning_symbol(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Kullanicinin talebi: surekli kazanan bir sembolde (yuksek kazanma
    orani, buyuk kazanc/kucuk kayip) pozisyon boyutu otomatik olarak
    buyumeli."""
    _seed_closures(
        backend_module,
        "BINANCE_FUTURES",
        "BTCUSDT",
        [5.0, 4.0, 6.0, -1.0, 5.0, -1.0, 4.0],
    )
    result = backend_module.get_kelly_position_size_scale("BTCUSDT", "BINANCE_FUTURES")
    assert result["qty_scale"] > 1.0
    assert result["qty_scale"] <= backend_module.KELLY_MAX_SCALE


def test_kelly_position_size_scale_isolated_per_broker(
    backend_module, isolated_runtime_db, runtime_db_connection
):
    """Ayni sembolun farkli broker'lardaki (ör. IBKR vs BINANCE_FUTURES)
    gecmisi birbirine karismamali."""
    _seed_closures(backend_module, "IBKR", "BTCUSDT", [1.0, -8.0, 1.0, -9.0, -7.0, 1.0, -8.0])
    result = backend_module.get_kelly_position_size_scale("BTCUSDT", "BINANCE_FUTURES")
    assert result["trades"] == 0
    assert result["qty_scale"] == 1.0
