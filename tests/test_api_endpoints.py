"""
API エンドポイントのユニットテスト

使用方法:
    pytest tests/test_api_endpoints.py -v

必要なパッケージ:
    pip install pytest pytest-asyncio httpx
"""

import pytest
from httpx import AsyncClient
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# モックモードを強制
os.environ['USE_MOCK_DATA'] = 'True'


@pytest.fixture
async def client():
    """テスト用クライアントを作成"""
    from backend.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """ヘルスチェックエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """正常なヘルスチェック"""
        response = await client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "ibkr_connected" in data
        assert "mode" in data
        assert "timestamp" in data


class TestMarketEndpoints:
    """マーケットデータエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_get_spy_price(self, client):
        """SPY価格取得"""
        response = await client.get("/api/market/spy")
        assert response.status_code == 200

        data = response.json()
        assert "last" in data
        assert "bid" in data
        assert "ask" in data
        assert "mid" in data
        assert "timestamp" in data
        assert "is_delayed" in data

        # 価格が正の値であることを確認
        assert data["last"] > 0
        assert data["bid"] > 0
        assert data["ask"] > 0

        # ビッド <= ミッド <= アスク
        assert data["bid"] <= data["mid"] <= data["ask"]

    @pytest.mark.asyncio
    async def test_get_vix(self, client):
        """VIX取得"""
        response = await client.get("/api/market/vix")
        assert response.status_code == 200

        data = response.json()
        assert "vix" in data
        assert "timestamp" in data

        # VIXが正の値であることを確認
        assert data["vix"] > 0
        # 通常のVIX範囲内（5-80）
        assert 5 <= data["vix"] <= 80


class TestOptionsEndpoints:
    """オプションエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_get_options_chain(self, client):
        """オプションチェーン取得"""
        response = await client.get("/api/options/chain?dte_min=1&dte_max=7")
        assert response.status_code == 200

        data = response.json()
        assert "symbol" in data
        assert "dte_range" in data
        assert "options_count" in data
        assert "options" in data

        # 複数のオプションが返されることを確認
        assert data["options_count"] > 0
        assert len(data["options"]) > 0

        # オプションデータの構造を確認
        option = data["options"][0]
        assert "strike" in option
        assert "expiry" in option
        assert "dte" in option
        assert "bid" in option
        assert "ask" in option
        assert "mid" in option
        assert "delta" in option

    @pytest.mark.asyncio
    async def test_get_spread_candidates(self, client):
        """スプレッド候補取得"""
        response = await client.get("/api/options/spreads")
        assert response.status_code == 200

        data = response.json()
        assert "candidates_count" in data
        assert "candidates" in data

        if data["candidates_count"] > 0:
            spread = data["candidates"][0]
            assert "short_strike" in spread
            assert "long_strike" in spread
            assert "spread_width" in spread
            assert "net_premium" in spread
            assert "max_loss" in spread
            assert "max_profit" in spread

            # スプレッド幅が正の値
            assert spread["spread_width"] > 0
            # ショートストライク > ロングストライク
            assert spread["short_strike"] > spread["long_strike"]

    @pytest.mark.asyncio
    async def test_calculate_spread(self, client):
        """スプレッド計算"""
        payload = {
            "short_strike": 520.0,
            "long_strike": 515.0,
            "short_premium": 2.53,
            "long_premium": 2.15
        }

        response = await client.post("/api/options/calculate-spread", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "spread_width" in data
        assert "net_premium" in data
        assert "max_loss" in data
        assert "max_profit" in data
        assert "breakeven" in data
        assert "risk_reward_ratio" in data

        # スプレッド幅の検証
        assert data["spread_width"] == 5.0
        # ネットプレミアムの検証
        assert abs(data["net_premium"] - 0.38) < 0.01


class TestStrategyEndpoints:
    """戦略エンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_next_entry_preview(self, client):
        """次回エントリープレビュー"""
        response = await client.get("/api/strategy/next-entry")
        assert response.status_code == 200

        data = response.json()
        assert "recommended" in data
        assert "vix" in data
        assert "adjusted_delta" in data
        assert "selected_expiry" in data
        assert "event_warnings" in data

        # VIXが妥当な範囲
        assert 5 <= data["vix"] <= 80

        # デルタが妥当な範囲
        if data["adjusted_delta"]:
            assert 0 < data["adjusted_delta"] < 1

    @pytest.mark.asyncio
    async def test_strategy_status(self, client):
        """戦略ステータス取得"""
        response = await client.get("/api/strategy/status")
        assert response.status_code == 200

        data = response.json()
        assert "is_active" in data
        assert "open_positions_count" in data

    @pytest.mark.asyncio
    async def test_event_calendar(self, client):
        """イベントカレンダー取得"""
        response = await client.get("/api/strategy/event-calendar")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "year" in data

        # 主要イベントが含まれていることを確認
        assert "FOMC" in data["events"]
        assert "NFP" in data["events"]
        assert "CPI" in data["events"]


class TestAccountEndpoints:
    """アカウントエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_account_summary(self, client):
        """アカウント概要取得"""
        response = await client.get("/api/account/summary")
        assert response.status_code == 200

        data = response.json()
        assert "account" in data
        assert "strategy_params" in data
        assert "risk_limits" in data
        assert "positions" in data

        # アカウント情報の検証
        account = data["account"]
        assert "net_liquidation" in account
        assert account["net_liquidation"] > 0

        # 戦略パラメータの検証
        params = data["strategy_params"]
        assert params["symbol"] == "SPY"
        assert params["spread_width"] == 5

    @pytest.mark.asyncio
    async def test_account_positions(self, client):
        """ポジション一覧取得"""
        response = await client.get("/api/account/positions")
        assert response.status_code == 200

        data = response.json()
        assert "positions" in data
        assert "count" in data
        assert isinstance(data["positions"], list)


class TestFXEndpoints:
    """為替レートエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_get_fx_rate(self, client):
        """為替レート取得"""
        response = await client.get("/api/fx/rate")
        assert response.status_code == 200

        data = response.json()
        assert "usd_jpy" in data

        # USD/JPYが妥当な範囲（100-200円）
        assert 100 <= data["usd_jpy"] <= 200

    @pytest.mark.asyncio
    async def test_calculate_tts_rate(self, client):
        """TTSレート計算"""
        response = await client.get("/api/fx/rate/tts?spot_rate=155.5&margin=1.0")
        assert response.status_code == 200

        data = response.json()
        assert "spot_rate" in data
        assert "margin" in data
        assert "tts_rate" in data

        # TTSレート = スポット + マージン
        assert data["tts_rate"] == data["spot_rate"] + data["margin"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
