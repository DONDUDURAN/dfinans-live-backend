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
