"""
モック注文モジュール: 実際には発注せずにテスト用にシミュレート
"""

from typing import Optional, Dict, Tuple
from datetime import datetime
import pytz
import random
from logger import get_logger, get_trading_logger


class MockOrderManager:
    """モック注文管理クラス（order.pyと同じインターフェース）"""

    def __init__(self, ib=None):
        """
        Args:
            ib: 互換性のため受け取るが使用しない
        """
        self.logger = get_logger()
        self.trading_logger = get_trading_logger()
        self.logger.info('🎭 モック注文モードで動作中')

    def place_bull_put_spread(
        self,
        spread: Dict,
        quantity: int,
        limit_price: Optional[float] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Bull Put Spreadを発注（モック）

        Args:
            spread: スプレッド情報
            quantity: 契約数
            limit_price: 指値価格

        Returns:
            (成功フラグ, メッセージ, 注文情報)
        """
        self.logger.info('=== Bull Put Spread 発注開始（モック）===')
        self.logger.info(f'売りプット: ${spread["short_strike"]:.2f}')
        self.logger.info(f'買いプット: ${spread["long_strike"]:.2f}')
        self.logger.info(f'満期: {spread["exp_date"]}')
        self.logger.info(f'契約数: {quantity}')

        # 指値価格の決定
        if limit_price is None:
            limit_price = spread['net_premium']
            self.logger.info(f'指値価格: ${limit_price:.2f} (mid価格)')
        else:
            self.logger.info(f'指値価格: ${limit_price:.2f} (カスタム)')

        # モックで約定をシミュレート（90%の確率で成功）
        success = random.random() < 0.90

        if success:
            # 約定価格は指値価格の±2%以内でランダム
            fill_price = limit_price * (1 + random.uniform(-0.02, 0.02))

            # モック注文情報
            order_info = {
                'short_trade': {
                    'orderStatus': {'status': 'Filled'},
                    'orderId': random.randint(1000, 9999)
                },
                'long_trade': {
                    'orderStatus': {'status': 'Filled'},
                    'orderId': random.randint(1000, 9999)
                },
                'short_contract': None,  # モック
                'long_contract': None,  # モック
                'quantity': quantity,
                'limit_price': limit_price,
                'fill_price': fill_price,
                'timestamp': datetime.now(pytz.UTC),
                'commission': 1.30 * quantity * 2,  # $1.30/契約 x 2レッグ
                'mock': True
            }

            self.logger.info(f'✓ 注文約定（モック）')
            self.logger.info(f'  約定価格: ${fill_price:.2f}')
            self.logger.info(f'  手数料: ${order_info["commission"]:.2f}')

            return True, '注文約定（モック）', order_info

        else:
            self.logger.warning('✗ 注文未約定（モック）')
            order_info = {
                'short_trade': {
                    'orderStatus': {'status': 'Cancelled'},
                },
                'long_trade': {
                    'orderStatus': {'status': 'Cancelled'},
                },
                'quantity': quantity,
                'limit_price': limit_price,
                'timestamp': datetime.now(pytz.UTC),
                'mock': True
            }
            return False, '注文未約定（モック）', order_info

    def check_order_status(self, trade) -> str:
        """注文ステータスを確認（モック）"""
        if trade and isinstance(trade, dict) and 'orderStatus' in trade:
            return trade['orderStatus'].get('status', 'Unknown')
        return 'Unknown'

    def cancel_order(self, trade) -> bool:
        """注文をキャンセル（モック）"""
        self.logger.info('注文をキャンセルしました（モック）')
        return True

    def get_fill_info(self, trade) -> Optional[Dict]:
        """約定情報を取得（モック）"""
        if not trade or not isinstance(trade, dict):
            return None

        # モック約定情報を生成
        return {
            'execution_time': datetime.now(pytz.UTC),
            'price': trade.get('fill_price', trade.get('limit_price', 0)),
            'quantity': trade.get('quantity', 1),
            'commission': trade.get('commission', 2.60),
            'realized_pnl': 0
        }
