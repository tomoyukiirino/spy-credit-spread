"""
ログ管理モジュール: システムログ、取引ログ、マーケットデータログを管理
"""

import logging
import csv
import os
from datetime import datetime
from typing import Dict, Any, Optional
import pytz
import config


class TradingLogger:
    """取引ログとマーケットデータログを管理するクラス"""

    def __init__(self):
        """ログディレクトリとファイルを初期化"""
        # ログディレクトリを作成
        os.makedirs(config.LOG_DIR, exist_ok=True)

        # システムログの設定
        self._setup_system_logger()

        # CSVファイルの初期化
        self._init_trade_log()
        self._init_market_data_log()

    def _setup_system_logger(self):
        """システムログ（ファイル+コンソール）を設定"""
        self.logger = logging.getLogger('SPYCreditSpread')
        self.logger.setLevel(logging.DEBUG)

        # 既存のハンドラーをクリア
        if self.logger.handlers:
            self.logger.handlers.clear()

        # ファイルハンドラー
        file_handler = logging.FileHandler(config.SYSTEM_LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # ハンドラーを追加
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _init_trade_log(self):
        """取引ログCSVを初期化（ヘッダー作成）"""
        if not os.path.exists(config.TRADE_LOG_FILE):
            with open(config.TRADE_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'trade_id',
                    'timestamp_utc',
                    'timestamp_et',
                    'timestamp_jst',
                    'trade_date_jst',
                    'symbol',
                    'action',
                    'option_type',
                    'strike',
                    'expiry',
                    'quantity',
                    'premium_per_contract',
                    'total_premium_usd',
                    'commission_usd',
                    'net_amount_usd',
                    'fx_rate_usd_jpy',
                    'fx_rate_tts',
                    'net_amount_jpy',
                    'spread_id',
                    'leg',
                    'position_status',
                    'notes'
                ])
            self.logger.info(f'取引ログファイルを作成: {config.TRADE_LOG_FILE}')

    def _init_market_data_log(self):
        """マーケットデータログCSVを初期化（ヘッダー作成）"""
        if not os.path.exists(config.MARKET_DATA_LOG):
            with open(config.MARKET_DATA_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp_utc',
                    'spy_price',
                    'spy_bid',
                    'spy_ask',
                    'vix_level',
                    'selected_strike_short',
                    'selected_strike_long',
                    'short_put_delta',
                    'short_put_iv',
                    'spread_premium_mid',
                    'max_profit',
                    'max_loss',
                    'risk_reward_ratio',
                    'fx_rate_usd_jpy'
                ])
            self.logger.info(f'マーケットデータログファイルを作成: {config.MARKET_DATA_LOG}')

    def log_trade(self, trade_data: Dict[str, Any]):
        """
        取引をCSVログに記録

        Args:
            trade_data: 取引データの辞書
        """
        with open(config.TRADE_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                trade_data.get('trade_id', ''),
                trade_data.get('timestamp_utc', ''),
                trade_data.get('timestamp_et', ''),
                trade_data.get('timestamp_jst', ''),
                trade_data.get('trade_date_jst', ''),
                trade_data.get('symbol', ''),
                trade_data.get('action', ''),
                trade_data.get('option_type', ''),
                trade_data.get('strike', ''),
                trade_data.get('expiry', ''),
                trade_data.get('quantity', ''),
                trade_data.get('premium_per_contract', ''),
                trade_data.get('total_premium_usd', ''),
                trade_data.get('commission_usd', ''),
                trade_data.get('net_amount_usd', ''),
                trade_data.get('fx_rate_usd_jpy', ''),
                trade_data.get('fx_rate_tts', ''),
                trade_data.get('net_amount_jpy', ''),
                trade_data.get('spread_id', ''),
                trade_data.get('leg', ''),
                trade_data.get('position_status', ''),
                trade_data.get('notes', '')
            ])

        self.logger.info(f'取引を記録: {trade_data.get("trade_id", "")} - {trade_data.get("action", "")} {trade_data.get("quantity", "")}x {trade_data.get("symbol", "")} @ ${trade_data.get("strike", "")}')

    def log_market_data(self, market_data: Dict[str, Any]):
        """
        マーケットデータをCSVログに記録

        Args:
            market_data: マーケットデータの辞書
        """
        with open(config.MARKET_DATA_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                market_data.get('timestamp_utc', ''),
                market_data.get('spy_price', ''),
                market_data.get('spy_bid', ''),
                market_data.get('spy_ask', ''),
                market_data.get('vix_level', ''),
                market_data.get('selected_strike_short', ''),
                market_data.get('selected_strike_long', ''),
                market_data.get('short_put_delta', ''),
                market_data.get('short_put_iv', ''),
                market_data.get('spread_premium_mid', ''),
                market_data.get('max_profit', ''),
                market_data.get('max_loss', ''),
                market_data.get('risk_reward_ratio', ''),
                market_data.get('fx_rate_usd_jpy', '')
            ])

        self.logger.debug(f'マーケットデータを記録: SPY ${market_data.get("spy_price", "")}')

    def get_logger(self) -> logging.Logger:
        """システムロガーを取得"""
        return self.logger


# グローバルインスタンス
_trading_logger = None

def get_trading_logger() -> TradingLogger:
    """TradingLoggerのシングルトンインスタンスを取得"""
    global _trading_logger
    if _trading_logger is None:
        _trading_logger = TradingLogger()
    return _trading_logger


def get_logger() -> logging.Logger:
    """システムロガーを取得（簡易アクセス用）"""
    return get_trading_logger().get_logger()
