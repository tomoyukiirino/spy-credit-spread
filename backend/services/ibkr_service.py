"""
IBKR接続をシングルトンで管理
ib_insyncを専用スレッドで実行（キューベース）
"""

import threading
import asyncio
import queue
from concurrent.futures import Future
from typing import Any, Callable, Optional, Tuple
from ib_insync import IB, util
import logging
import sys
import os

# FastAPIとの互換性のためにasyncioをパッチ
util.patchAsyncio()

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

logger = logging.getLogger(__name__)


class IBKRService:
    """
    ib_insyncを専用スレッドで動かすシングルトンサービス

    仕組み:
    1. 専用スレッド起動
    2. そのスレッド内で ib.connect()（同期的）を呼ぶ
    3. FastAPI側から execute() で関数とargsをキューに投げる
    4. 専用スレッドがキューから取り出して実行し、Futureに結果を入れる
    5. FastAPI側は await で Future の結果を待つ

    これにより ib_insync の同期メソッドが自分のスレッドで素直に動く。
    イベントループの二重実行問題は発生しない。
    """

    _instance: Optional['IBKRService'] = None
    _lock = threading.Lock()

    def __init__(self):
        self.ib = IB()
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._running = False
        self._task_queue: queue.Queue[Tuple[Callable, tuple, dict, Future]] = queue.Queue()

    @classmethod
    def get_instance(cls) -> 'IBKRService':
        """シングルトンインスタンス取得"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 1):
        """
        専用スレッドを起動してIBKRに接続。
        FastAPIのlifespan startup時に呼ぶ。
        """
        self._running = True
        connect_done = threading.Event()
        connect_error: list = []

        def _worker():
            # イベントループを作成してセット（ib_insyncが必要とするため）
            # ただし、run_forever()は呼ばず、ib_insyncに制御を任せる
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 1. 専用スレッド内で「同期的に」接続
                self.ib.connect(host, port, clientId=client_id)
                self._connected = True
                self.ib.reqMarketDataType(config.MARKET_DATA_TYPE)
                logger.info(f"IBKR接続完了: {host}:{port} (clientId={client_id})")
            except Exception as e:
                connect_error.append(e)
                logger.error(f"IBKR接続失敗: {e}")
            finally:
                connect_done.set()

            # 2. メインループ: キューからタスクを取り出して実行
            while self._running:
                try:
                    # 短いタイムアウトでタスクを待機
                    func, args, kwargs, future = self._task_queue.get(timeout=0.1)
                    try:
                        result = func(*args, **kwargs)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                except queue.Empty:
                    # 3. 重要：タスクがない間、ib.sleepでIBKRの内部イベント（Ticker更新等）を処理
                    # これにより asyncio のループ競合を避けつつ、データを更新し続けられる
                    if self._connected:
                        self.ib.sleep(0.01)
                except Exception as e:
                    logger.error(f"ワーカーエラー: {e}")

        self._thread = threading.Thread(target=_worker, daemon=True, name="ibkr-worker")
        self._thread.start()

        # 接続完了を待つ
        connect_done.wait(timeout=30)
        if connect_error:
            raise connect_error[0]

    def stop(self):
        """接続切断とスレッド停止。FastAPIのlifespan shutdown時に呼ぶ。"""
        self._running = False
        if self._connected:
            try:
                # 切断もキュー経由で専用スレッドで実行
                future = Future()
                self._task_queue.put((self.ib.disconnect, (), {}, future))
                future.result(timeout=5)
            except Exception as e:
                logger.warning(f"IBKR切断時エラー: {e}")
            self._connected = False

        if self._thread:
            self._thread.join(timeout=5)
        logger.info("IBKRサービス停止")

    @property
    def is_connected(self) -> bool:
        return self._connected and self.ib.isConnected()

    def execute_sync(self, func: Callable, *args, **kwargs) -> Future:
        """
        専用スレッドで同期関数を実行し、Futureを返す。
        内部用。通常は execute() を使う。
        """
        future = Future()
        self._task_queue.put((func, args, kwargs, future))
        return future

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        FastAPIのasyncコンテキストから呼ぶメインメソッド。
        ib_insyncの同期メソッドを専用スレッドで実行し、結果を返す。

        使い方:
            ibkr = IBKRService.get_instance()

            # 口座情報
            summary = await ibkr.execute(ibkr.ib.accountSummary)

            # マーケットデータ（ib.sleep()での待機込み）
            def get_spy_price(ib):
                from ib_insync import Stock
                contract = Stock('SPY', 'SMART', 'USD')
                ib.qualifyContracts(contract)
                ib.reqMktData(contract, '', False, False)
                ib.sleep(2)  # データ到着を待つ
                ticker = ib.ticker(contract)
                ib.cancelMktData(contract)
                return {'last': ticker.last, 'bid': ticker.bid, 'ask': ticker.ask}

            price = await ibkr.execute(get_spy_price, ibkr.ib)
        """
        future = self.execute_sync(func, *args, **kwargs)
        # FastAPIのイベントループをブロックしないように待機
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, future.result, 30)  # 30秒タイムアウト

    async def run(self, func: Callable, *args, **kwargs) -> Any:
        """execute()のエイリアス（後方互換性用）"""
        return await self.execute(func, *args, **kwargs)


# --- Depends用のヘルパー関数 ---

def get_ibkr_service() -> IBKRService:
    """
    FastAPIのDependsで使用するヘルパー関数

    使い方:
        from fastapi import Depends
        from backend.services.ibkr_service import get_ibkr_service

        @router.get("/endpoint")
        async def endpoint(ibkr: IBKRService = Depends(get_ibkr_service)):
            result = await ibkr.execute(...)
    """
    from fastapi import HTTPException

    service = IBKRService.get_instance()
    if not service.is_connected:
        raise HTTPException(status_code=503, detail="IBKR未接続")
    return service
