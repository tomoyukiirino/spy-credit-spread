"""
IBKR接続管理モジュール: 接続の確立・切断・再接続をハンドリング
"""

from ib_insync import IB, util
import time
from typing import Dict, List, Optional
import config
from logger import get_logger

# FastAPIとの互換性のためにasyncioをパッチ
util.patchAsyncio()


class IBKRConnection:
    """IBKR接続を管理するクラス（コンテキストマネージャー対応）"""

    def __init__(self, use_paper: bool = True, max_retries: int = 3):
        """
        Args:
            use_paper: Trueでペーパー口座、Falseでリアル口座
            max_retries: 接続リトライの最大回数
        """
        self.ib = IB()
        self.use_paper = use_paper
        self.max_retries = max_retries
        self.logger = get_logger()
        self.connected = False

        # 接続パラメータ
        self.host = config.TWS_HOST
        self.port = config.TWS_PORT_PAPER if use_paper else config.TWS_PORT_LIVE
        self.client_id = config.CLIENT_ID

    def __enter__(self):
        """コンテキストマネージャーのエントリー（with文で使用）"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了（with文で使用）"""
        self.disconnect()
        return False

    def connect(self):
        """
        TWSに接続（リトライロジック付き）

        Raises:
            ConnectionError: 最大リトライ回数を超えても接続できない場合
        """
        account_type = 'ペーパー' if self.use_paper else 'リアル'
        self.logger.info(f'IBKR {account_type}口座への接続を開始...')
        self.logger.info(f'接続先: {self.host}:{self.port} (ClientID: {self.client_id})')

        for attempt in range(1, self.max_retries + 1):
            try:
                self.ib.connect(
                    self.host,
                    self.port,
                    clientId=self.client_id,
                    timeout=config.REQUEST_TIMEOUT
                )
                self.connected = True

                # 接続成功
                accounts = self.ib.managedAccounts()
                self.logger.info(f'✓ 接続成功 (試行 {attempt}/{self.max_retries})')
                self.logger.info(f'管理口座: {accounts}')

                # マーケットデータタイプを設定（遅延データを許可）
                self.ib.reqMarketDataType(config.MARKET_DATA_TYPE)

                return

            except Exception as e:
                self.logger.warning(f'✗ 接続失敗 (試行 {attempt}/{self.max_retries}): {str(e)}')

                if attempt < self.max_retries:
                    # 指数バックオフで待機
                    wait_time = 2 ** attempt
                    self.logger.info(f'{wait_time}秒後に再試行...')
                    time.sleep(wait_time)
                else:
                    # 最大リトライ回数を超えた
                    error_msg = f'IBKR接続に失敗しました（{self.max_retries}回試行）'
                    self.logger.error(error_msg)
                    raise ConnectionError(error_msg) from e

    async def connect_async(self):
        """
        TWSに接続（非同期版、FastAPIのlifespan等で使用）
        バックグラウンドスレッドで同期的に接続を実行

        Raises:
            ConnectionError: 最大リトライ回数を超えても接続できない場合
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # バックグラウンドスレッドで同期的な接続を実行
        # これによりib_insyncの独自イベントループとFastAPIのイベントループの衝突を回避
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, self.connect)

    def disconnect(self):
        """TWSから切断"""
        if self.connected and self.ib.isConnected():
            self.logger.info('IBKR接続を切断中...')
            self.ib.disconnect()
            self.connected = False
            self.logger.info('✓ 切断完了')

    def get_account_summary(self) -> Dict[str, Dict[str, str]]:
        """
        口座サマリー情報を取得

        Returns:
            口座情報の辞書 {tag: {value, currency}}
        """
        if not self.connected:
            raise ConnectionError('IBKRに接続されていません')

        summary = {}
        important_tags = ['NetLiquidation', 'TotalCashValue', 'BuyingPower']

        for item in self.ib.accountSummary():
            if item.tag in important_tags:
                summary[item.tag] = {
                    'value': item.value,
                    'currency': item.currency
                }

        return summary

    def print_account_info(self):
        """口座情報をコンソールに表示"""
        try:
            summary = self.get_account_summary()

            self.logger.info('=== 口座情報 ===')
            for tag, data in summary.items():
                self.logger.info(f'  {tag}: {data["value"]} {data["currency"]}')

        except Exception as e:
            self.logger.error(f'口座情報の取得に失敗: {str(e)}')

    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self.connected and self.ib.isConnected()

    def get_ib(self) -> IB:
        """IBインスタンスを取得（外部からの直接アクセス用）"""
        if not self.connected:
            raise ConnectionError('IBKRに接続されていません')
        return self.ib
