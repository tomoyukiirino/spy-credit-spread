"""
ポジション監視モジュール
オープンポジションを監視し、損切り条件に達した場合にクローズしてメール通知
"""

from datetime import datetime
import pytz
from dotenv import load_dotenv
import config
from logger import get_logger, get_trading_logger
from position import PositionManager
from email_notification import get_email_notifier

# .envファイルを読み込み
load_dotenv()

# モックデータモードの判定
if config.USE_MOCK_DATA:
    from mock_data import MockIBKRConnection as IBKRConnection
    from mock_data import MockMarketDataManager as MarketDataManager
    from mock_order import MockOrderManager as OrderManager
else:
    from connection import IBKRConnection
    from data import MarketDataManager
    from order import OrderManager


class PositionMonitor:
    """ポジション監視クラス"""

    def __init__(
        self,
        position_manager: PositionManager,
        market_data_manager: MarketDataManager,
        order_manager: OrderManager
    ):
        """
        Args:
            position_manager: PositionManagerインスタンス
            market_data_manager: MarketDataManagerインスタンス
            order_manager: OrderManagerインスタンス
        """
        self.position_manager = position_manager
        self.market_data = market_data_manager
        self.order_manager = order_manager
        self.logger = get_logger()
        self.trading_logger = get_trading_logger()
        self.email_notifier = get_email_notifier()

        # 損切り閾値（プレミアムが投資額の2倍になったら損切り）
        self.stop_loss_multiplier = 2.0

    def check_position_for_stop_loss(self, spread_id: str, position: dict) -> tuple:
        """
        ポジションが損切り条件に達しているかチェック

        Args:
            spread_id: スプレッドID
            position: ポジション情報

        Returns:
            (should_close, reason, current_premium, estimated_loss)
        """
        try:
            # 現在のオプション価格を取得
            expiration = position['expiry'].replace('-', '')
            spy_price = self.market_data.get_spy_price()

            if not spy_price:
                self.logger.warning(f'{spread_id}: SPY価格の取得に失敗')
                return False, '', 0.0, 0.0

            # 現在のプレミアム（スプレッド価格）を計算
            # 注: 実際の実装では、両足のオプション価格を取得して計算
            # ここでは簡易的に、エントリープレミアムの倍率で判定
            entry_premium = position['entry_premium']
            quantity = position['quantity']

            # 実際のマーケットデータからプレミアムを取得する実装は複雑なため
            # ここではシンプルな例として記載
            # TODO: 実際のオプション価格取得ロジックを実装

            # 損切り判定の例:
            # 1. プレミアムが2倍以上になった場合
            # 2. 満期まで残り1日で損失ポジション
            # 3. SPY価格がショートストライクを下回った場合

            # 仮の現在プレミアム（実際にはマーケットデータから取得）
            current_premium = entry_premium  # TODO: 実際の値を取得

            # 損切り条件1: プレミアムが2倍以上
            if current_premium >= entry_premium * self.stop_loss_multiplier:
                estimated_loss = (current_premium - entry_premium) * quantity * 100
                return True, 'プレミアムが投資額の2倍に達しました', current_premium, estimated_loss

            # 損切り条件2: SPY価格がショートストライクを下回った
            short_strike = position['short_strike']
            current_spy = spy_price.get('last', 0)

            if current_spy > 0 and current_spy < short_strike * 0.98:  # 2%のマージン
                estimated_loss = position['max_loss'] * quantity
                return True, f'SPY価格がショートストライク${short_strike:.2f}の98%を下回りました', current_premium, estimated_loss

            # 正常範囲
            return False, '', current_premium, 0.0

        except Exception as e:
            self.logger.error(f'{spread_id}: 損切りチェックエラー - {str(e)}')
            return False, '', 0.0, 0.0

    def close_position_with_notification(
        self,
        spread_id: str,
        position: dict,
        reason: str,
        current_premium: float,
        estimated_loss: float
    ) -> bool:
        """
        ポジションをクローズしてメール通知

        Args:
            spread_id: スプレッドID
            position: ポジション情報
            reason: 損切り理由
            current_premium: 現在のプレミアム
            estimated_loss: 想定損失額

        Returns:
            成功フラグ
        """
        self.logger.warning(f'🚨 損切り実行: {spread_id}')
        self.logger.warning(f'   理由: {reason}')
        self.logger.warning(f'   想定損失: ${estimated_loss:.2f}')

        try:
            # メール通知を先に送信
            self.email_notifier.send_stop_loss_alert(
                position=position,
                estimated_loss=estimated_loss,
                reason=reason
            )

            # ポジションクローズ注文を発注
            # TODO: 実際のクローズ注文ロジックを実装
            # order_manager.close_bull_put_spread(...) のような関数が必要

            # 簡易的な実装として、position_managerでポジションをクローズ
            fx_rate = 150.0  # TODO: 実際の為替レートを取得

            success = self.position_manager.close_position(
                spread_id=spread_id,
                exit_premium=current_premium,
                fx_rate=fx_rate
            )

            if success:
                self.logger.info(f'✓ {spread_id}: ポジションクローズ完了')

                # 取引ログに記録
                self.trading_logger.info(
                    f'STOP_LOSS,{spread_id},{reason},'
                    f'${estimated_loss:.2f},{datetime.now().isoformat()}'
                )

                return True
            else:
                self.logger.error(f'✗ {spread_id}: ポジションクローズ失敗')
                return False

        except Exception as e:
            self.logger.error(f'{spread_id}: ポジションクローズエラー - {str(e)}')
            return False

    def monitor_all_positions(self) -> dict:
        """
        すべてのオープンポジションを監視

        Returns:
            監視結果のサマリー
        """
        self.logger.info('=' * 60)
        self.logger.info('ポジション監視開始')
        self.logger.info('=' * 60)

        summary = {
            'total_positions': 0,
            'closed_positions': 0,
            'errors': 0
        }

        # オープンポジションを取得
        open_positions = self.position_manager.get_open_positions()
        summary['total_positions'] = len(open_positions)

        if not open_positions:
            self.logger.info('オープンポジションなし')
            return summary

        self.logger.info(f'オープンポジション数: {len(open_positions)}')

        # 各ポジションをチェック
        for spread_id, position in open_positions.items():
            self.logger.info(f'\n--- {spread_id} チェック ---')

            # 損切りチェック
            should_close, reason, current_premium, estimated_loss = \
                self.check_position_for_stop_loss(spread_id, position)

            if should_close:
                # 損切り実行
                success = self.close_position_with_notification(
                    spread_id=spread_id,
                    position=position,
                    reason=reason,
                    current_premium=current_premium,
                    estimated_loss=estimated_loss
                )

                if success:
                    summary['closed_positions'] += 1
                else:
                    summary['errors'] += 1
            else:
                self.logger.info(f'{spread_id}: 正常範囲')

        self.logger.info('')
        self.logger.info('=' * 60)
        self.logger.info('ポジション監視完了')
        self.logger.info(f'監視数: {summary["total_positions"]}')
        self.logger.info(f'損切り実行: {summary["closed_positions"]}')
        self.logger.info(f'エラー: {summary["errors"]}')
        self.logger.info('=' * 60)

        return summary


def main():
    """ポジション監視スクリプト（cron等から定期実行）"""
    logger = get_logger()

    logger.info('=' * 60)
    logger.info('ポジション監視スクリプト')
    if config.USE_MOCK_DATA:
        logger.info('🎭 モード: モックデータ')
    else:
        logger.info('📡 モード: リアルデータ')
    logger.info('=' * 60)

    try:
        with IBKRConnection(use_paper=config.USE_PAPER_ACCOUNT) as conn:
            ib = conn.get_ib()

            # 各マネージャーを初期化
            market_data = MarketDataManager(ib)
            order_manager = OrderManager(ib)
            position_manager = PositionManager()

            # ポジション監視を実行
            monitor = PositionMonitor(
                position_manager=position_manager,
                market_data_manager=market_data,
                order_manager=order_manager
            )

            summary = monitor.monitor_all_positions()

            logger.info('✓ 処理完了')

    except Exception as e:
        logger.error(f'処理エラー: {str(e)}')


if __name__ == '__main__':
    main()
