"""
為替レート取得モジュール: USD/JPYレートを取得（税務対応）
"""

from ib_insync import IB, Forex
import requests
from typing import Optional, Tuple
from datetime import datetime
import config
from logger import get_logger


class FXRateManager:
    """為替レート取得を管理するクラス"""

    def __init__(self, ib: Optional[IB] = None):
        """
        Args:
            ib: IBインスタンス（IBKRから為替レートを取得する場合）
        """
        self.ib = ib
        self.logger = get_logger()

    def get_usd_jpy_rate(self) -> Optional[float]:
        """
        USD/JPY為替レートを取得（優先順位順に試行）

        1. IBKR APIから取得
        2. 無料為替APIから取得（フォールバック）
        3. 手動入力を促す

        Returns:
            USD/JPYレート、取得できない場合はNone
        """
        # 1. IBKRから取得を試行
        if self.ib is not None:
            rate = self._get_rate_from_ibkr()
            if rate is not None:
                self.logger.info(f'✓ IBKR経由でUSD/JPYレート取得: {rate:.2f}')
                return rate

        # 2. 無料APIから取得を試行
        rate = self._get_rate_from_api()
        if rate is not None:
            self.logger.info(f'✓ API経由でUSD/JPYレート取得: {rate:.2f}')
            return rate

        # 3. すべて失敗
        self.logger.warning('⚠ USD/JPYレートの取得に失敗しました')
        self.logger.warning('手動でレートを入力するか、後で更新してください')
        return None

    def _get_rate_from_ibkr(self) -> Optional[float]:
        """
        IBKRからUSD/JPY為替レートを取得

        Returns:
            USD/JPYレート、取得できない場合はNone
        """
        try:
            if self.ib is None or not self.ib.isConnected():
                self.logger.debug('IBKRに接続されていません')
                return None

            # USD.JPYのForexペアを作成
            contract = Forex('USDJPY')

            # コントラクトを検証
            qualified = self.ib.qualifyContracts(contract)
            if not qualified:
                self.logger.warning('USD.JPYのコントラクト検証に失敗')
                return None

            contract = qualified[0]

            # マーケットデータをリクエスト
            ticker = self.ib.reqMktData(contract, '', False, False)

            # データが返ってくるまで待機
            self.ib.sleep(2)

            # レートを取得（Bid/Askの中間値を使用）
            if ticker.bid and ticker.ask and ticker.bid > 0 and ticker.ask > 0:
                rate = (ticker.bid + ticker.ask) / 2
                self.logger.debug(f'IBKR USD/JPY - Bid: {ticker.bid:.2f}, Ask: {ticker.ask:.2f}, Mid: {rate:.2f}')

                # マーケットデータのサブスクリプションを解除
                self.ib.cancelMktData(contract)

                return rate
            else:
                self.logger.debug(f'IBKR USD/JPY データ不完全 - Bid: {ticker.bid}, Ask: {ticker.ask}')

                # マーケットデータのサブスクリプションを解除
                self.ib.cancelMktData(contract)

                return None

        except Exception as e:
            self.logger.debug(f'IBKR経由の為替レート取得エラー: {str(e)}')
            return None

    def _get_rate_from_api(self) -> Optional[float]:
        """
        exchangerate-api.comからUSD/JPY為替レートを取得

        Returns:
            USD/JPYレート、取得できない場合はNone
        """
        try:
            url = f'https://v6.exchangerate-api.com/v6/{config.EXCHANGERATE_API_KEY}/latest/USD'
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 'success':
                    rates = data.get('conversion_rates', {})
                    jpy_rate = rates.get('JPY')

                    if jpy_rate:
                        self.logger.debug(f'API USD/JPY: {jpy_rate:.2f}')
                        return float(jpy_rate)

            self.logger.debug(f'API応答エラー: ステータスコード {response.status_code}')
            return None

        except requests.exceptions.Timeout:
            self.logger.debug('APIタイムアウト')
            return None
        except Exception as e:
            self.logger.debug(f'API経由の為替レート取得エラー: {str(e)}')
            return None

    def get_tts_rate(self, trade_date: Optional[str] = None) -> Optional[float]:
        """
        TTSレート（対顧客電信売相場）を取得

        NOTE: 現在は手動入力を想定。将来的には前営業日のレートをログから取得、
        または三菱UFJのTTSレートをスクレイピングする実装も可能。

        Args:
            trade_date: 取引日（YYYY-MM-DD形式）

        Returns:
            TTSレート、取得できない場合はNone
        """
        self.logger.info('TTSレートは手動で入力してください')
        self.logger.info('（例: 三菱UFJ銀行のTTSレート https://www.bk.mufg.jp/gdocs/kinri/list_j/kinri/kawase.html）')

        # 将来的な実装: ログファイルから前営業日のレートを取得
        # 将来的な実装: 三菱UFJのウェブサイトからスクレイピング

        return None

    def get_rates_for_trade(self) -> Tuple[Optional[float], Optional[float]]:
        """
        取引記録用の為替レートを取得

        Returns:
            (実勢レート, TTSレート)のタプル
        """
        spot_rate = self.get_usd_jpy_rate()
        tts_rate = self.get_tts_rate()

        return spot_rate, tts_rate


def get_fx_rate(ib: Optional[IB] = None) -> Optional[float]:
    """
    USD/JPY為替レートを取得（簡易アクセス用）

    Args:
        ib: IBインスタンス（オプション）

    Returns:
        USD/JPYレート
    """
    manager = FXRateManager(ib)
    return manager.get_usd_jpy_rate()
