"""
注文管理モジュール: Bull Put Spreadの発注と追跡
"""

from ib_insync import IB, Option, Order, MarketOrder, LimitOrder
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import pytz
import config
from logger import get_logger, get_trading_logger


class OrderManager:
    """注文の発注と管理を行うクラス"""

    def __init__(self, ib: IB):
        """
        Args:
            ib: 接続済みのIBインスタンス
        """
        self.ib = ib
        self.logger = get_logger()
        self.trading_logger = get_trading_logger()

    def place_bull_put_spread(
        self,
        spread: Dict,
        quantity: int,
        limit_price: Optional[float] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Bull Put Spreadを発注

        Args:
            spread: スプレッド情報
            quantity: 契約数
            limit_price: 指値価格（Noneの場合はmid価格を使用）

        Returns:
            (成功フラグ, メッセージ, 注文情報)
        """
        self.logger.info('=== Bull Put Spread 発注開始 ===')
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

        try:
            # 1. オプションコントラクトを作成
            short_put_contract = self._create_option_contract(
                spread['expiration'],
                spread['short_strike'],
                'P'
            )

            long_put_contract = self._create_option_contract(
                spread['expiration'],
                spread['long_strike'],
                'P'
            )

            # コントラクトを検証
            qualified_short = self.ib.qualifyContracts(short_put_contract)
            qualified_long = self.ib.qualifyContracts(long_put_contract)

            if not qualified_short or not qualified_long:
                return False, 'オプションコントラクトの検証に失敗', {}

            short_put_contract = qualified_short[0]
            long_put_contract = qualified_long[0]

            self.logger.info('✓ コントラクト検証完了')

            # 2. Combo Order (Spread Order) を作成
            # Bull Put Spread = 売りプット + 買いプット
            combo_order = self._create_spread_order(
                short_put_contract,
                long_put_contract,
                quantity,
                limit_price
            )

            self.logger.info('✓ スプレッド注文作成完了')

            # 3. 注文を発注
            self.logger.info('注文を送信中...')

            # 売りプットの注文
            short_trade = self.ib.placeOrder(short_put_contract, combo_order['short'])

            # 買いプットの注文
            long_trade = self.ib.placeOrder(long_put_contract, combo_order['long'])

            # 注文の約定を待機
            self.ib.sleep(2)

            # 注文ステータスを確認
            short_status = short_trade.orderStatus.status
            long_status = long_trade.orderStatus.status

            self.logger.info(f'売りプット注文ステータス: {short_status}')
            self.logger.info(f'買いプット注文ステータス: {long_status}')

            # 注文情報を返す
            order_info = {
                'short_trade': short_trade,
                'long_trade': long_trade,
                'short_contract': short_put_contract,
                'long_contract': long_put_contract,
                'quantity': quantity,
                'limit_price': limit_price,
                'timestamp': datetime.now(pytz.UTC)
            }

            # ステータスが Submitted または Filled なら成功
            if short_status in ['Submitted', 'Filled', 'PreSubmitted'] and \
               long_status in ['Submitted', 'Filled', 'PreSubmitted']:
                self.logger.info('✓ 注文が正常に送信されました')
                return True, '注文送信成功', order_info
            else:
                self.logger.warning(f'注文送信に問題がある可能性: {short_status}, {long_status}')
                return False, f'注文ステータス異常: {short_status}, {long_status}', order_info

        except Exception as e:
            self.logger.error(f'注文発注エラー: {str(e)}', exc_info=True)
            return False, f'注文エラー: {str(e)}', {}

    def _create_option_contract(
        self,
        expiration: str,
        strike: float,
        right: str
    ) -> Option:
        """
        オプションコントラクトを作成

        Args:
            expiration: 満期日（YYYYMMDD）
            strike: 行使価格
            right: 'C' or 'P'

        Returns:
            Optionコントラクト
        """
        return Option(
            symbol=config.SYMBOL,
            lastTradeDateOrContractMonth=expiration,
            strike=strike,
            right=right,
            exchange=config.EXCHANGE,
            currency=config.CURRENCY
        )

    def _create_spread_order(
        self,
        short_contract: Option,
        long_contract: Option,
        quantity: int,
        limit_price: float
    ) -> Dict:
        """
        スプレッド注文を作成

        Args:
            short_contract: 売りプットコントラクト
            long_contract: 買いプットコントラクト
            quantity: 契約数
            limit_price: ネットプレミアム（スプレッド全体の指値）

        Returns:
            {'short': 売り注文, 'long': 買い注文}
        """
        # 売りプット: SELL
        short_order = LimitOrder(
            action='SELL',
            totalQuantity=quantity,
            lmtPrice=limit_price + 0.05,  # 少し余裕を持たせる
            transmit=False  # まだ送信しない
        )

        # 買いプット: BUY
        long_order = LimitOrder(
            action='BUY',
            totalQuantity=quantity,
            lmtPrice=limit_price - 0.05,  # 少し余裕を持たせる
            transmit=True  # 両方同時に送信
        )

        return {
            'short': short_order,
            'long': long_order
        }

    def check_order_status(self, trade) -> str:
        """
        注文ステータスを確認

        Args:
            trade: Trade object

        Returns:
            ステータス文字列
        """
        if trade and hasattr(trade, 'orderStatus'):
            return trade.orderStatus.status
        return 'Unknown'

    def cancel_order(self, trade) -> bool:
        """
        注文をキャンセル

        Args:
            trade: Trade object

        Returns:
            キャンセル成功フラグ
        """
        try:
            self.ib.cancelOrder(trade.order)
            self.logger.info(f'注文をキャンセルしました: {trade.order.orderId}')
            return True
        except Exception as e:
            self.logger.error(f'注文キャンセルエラー: {str(e)}')
            return False

    def get_fill_info(self, trade) -> Optional[Dict]:
        """
        約定情報を取得

        Args:
            trade: Trade object

        Returns:
            約定情報の辞書
        """
        if not trade or not trade.fills:
            return None

        fills = trade.fills
        if not fills:
            return None

        # 最初のfillを取得
        fill = fills[0]

        return {
            'execution_time': fill.time,
            'price': fill.execution.price,
            'quantity': fill.execution.shares,
            'commission': fill.commissionReport.commission if fill.commissionReport else 0,
            'realized_pnl': fill.commissionReport.realizedPNL if fill.commissionReport else 0
        }
