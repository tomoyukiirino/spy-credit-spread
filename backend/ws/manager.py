"""
WebSocket接続マネージャー: リアルタイム価格配信
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import asyncio
import json
from datetime import datetime
import pytz


class ConnectionManager:
    """WebSocket接続を管理するクラス"""

    def __init__(self):
        """初期化"""
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}  # WebSocket -> {channel1, channel2, ...}

    async def connect(self, websocket: WebSocket):
        """
        WebSocket接続を受け入れる

        Args:
            websocket: WebSocketインスタンス
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        """
        WebSocket接続を切断

        Args:
            websocket: WebSocketインスタンス
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def subscribe(self, websocket: WebSocket, channel: str):
        """
        チャンネルを購読

        Args:
            websocket: WebSocketインスタンス
            channel: チャンネル名 ("spy", "options", "fx", "all")
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)

    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """
        チャンネルの購読を解除

        Args:
            websocket: WebSocketインスタンス
            channel: チャンネル名
        """
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        特定のWebSocketにメッセージを送信

        Args:
            message: 送信するメッセージ
            websocket: WebSocketインスタンス
        """
        try:
            await websocket.send_json(message)
        except:
            # 送信失敗時は接続を切断
            self.disconnect(websocket)

    async def broadcast(self, message: dict, channel: str = "all"):
        """
        チャンネルを購読している全接続にブロードキャスト

        Args:
            message: 送信するメッセージ
            channel: チャンネル名
        """
        disconnected = []

        for connection in self.active_connections:
            # 購読チェック
            if connection in self.subscriptions:
                subscribed_channels = self.subscriptions[connection]
                if "all" in subscribed_channels or channel in subscribed_channels:
                    try:
                        await connection.send_json(message)
                    except:
                        disconnected.append(connection)

        # 切断された接続を削除
        for connection in disconnected:
            self.disconnect(connection)

    def get_connection_count(self) -> int:
        """
        アクティブな接続数を取得

        Returns:
            int: 接続数
        """
        return len(self.active_connections)


# グローバルインスタンス
manager = ConnectionManager()


async def broadcast_spy_price(market_data_manager):
    """
    SPY価格を定期的にブロードキャスト（1秒ごと）

    Args:
        market_data_manager: MarketDataManager インスタンス
    """
    while True:
        try:
            if manager.get_connection_count() > 0:
                price_data = market_data_manager.get_spy_price()

                if price_data:
                    message = {
                        "type": "spy_price",
                        "data": price_data,
                        "timestamp": datetime.now(pytz.UTC).isoformat()
                    }
                    await manager.broadcast(message, channel="spy")

        except Exception as e:
            print(f"Error broadcasting SPY price: {e}")

        await asyncio.sleep(1)  # 1秒待機


async def broadcast_options_data(market_data_manager):
    """
    オプションデータを定期的にブロードキャスト（5秒ごと）

    Args:
        market_data_manager: MarketDataManager インスタンス
    """
    while True:
        try:
            if manager.get_connection_count() > 0:
                # オプションデータ取得（簡略版）
                # 実際にはスプレッド候補などを含める
                message = {
                    "type": "options_update",
                    "data": {"status": "available"},
                    "timestamp": datetime.now(pytz.UTC).isoformat()
                }
                await manager.broadcast(message, channel="options")

        except Exception as e:
            print(f"Error broadcasting options data: {e}")

        await asyncio.sleep(5)  # 5秒待機


async def broadcast_fx_rate(fx_rate_manager):
    """
    為替レートを定期的にブロードキャスト（30秒ごと）

    Args:
        fx_rate_manager: FXRateManager インスタンス
    """
    while True:
        try:
            if manager.get_connection_count() > 0 and fx_rate_manager:
                rate_data = fx_rate_manager.get_usd_jpy_rate()

                if rate_data:
                    message = {
                        "type": "fx_rate",
                        "data": rate_data,
                        "timestamp": datetime.now(pytz.UTC).isoformat()
                    }
                    await manager.broadcast(message, channel="fx")

        except Exception as e:
            print(f"Error broadcasting FX rate: {e}")

        await asyncio.sleep(30)  # 30秒待機
