"""
Step 4 メインスクリプト: Bull Put Spreadの自動選択と発注
"""

from datetime import datetime
import pytz
import config
from logger import get_trading_logger, get_logger
from strategy import SpreadStrategy
from position import PositionManager
from monitor import RiskMonitor

# モックデータモードの判定
if config.USE_MOCK_DATA:
    from mock_data import MockIBKRConnection as IBKRConnection
    from mock_data import MockMarketDataManager as MarketDataManager
    from mock_data import MockFXRateManager as FXRateManager
    from mock_order import MockOrderManager as OrderManager
else:
    from connection import IBKRConnection
    from data import MarketDataManager
    from fx_rate import FXRateManager
    from order import OrderManager


def main():
    """Step 4のメイン処理フロー"""
    logger = get_logger()
    trading_logger = get_trading_logger()

    logger.info('=' * 60)
    logger.info('SPY Bull Put Credit Spread - Step 4: 自動取引実行')
    if config.USE_MOCK_DATA:
        logger.info('🎭 モード: モックデータ + モック注文（開発・テスト用）')
    else:
        logger.info('📡 モード: リアルデータ + リアル注文（本番）')
    logger.info('=' * 60)

    try:
        # IBKR接続
        with IBKRConnection(use_paper=config.USE_PAPER_ACCOUNT) as conn:
            logger.info('')

            # 口座情報取得
            account_summary = conn.get_account_summary()
            conn.print_account_info()
            logger.info('')

            # IBインスタンスを取得
            ib = conn.get_ib()

            # 各マネージャーを初期化
            market_data = MarketDataManager(ib)
            strategy = SpreadStrategy(market_data)
            order_manager = OrderManager(ib)
            position_manager = PositionManager()
            risk_monitor = RiskMonitor(position_manager)

            # ポジションサマリーを表示
            position_manager.print_summary()
            logger.info('')

            # 1. SPY価格取得
            logger.info('--- SPY価格取得 ---')
            spy_price_data = market_data.get_spy_price()

            if not spy_price_data:
                logger.error('SPY価格の取得に失敗しました')
                return

            spy_price = spy_price_data['last']
            logger.info('')

            # 2. 最適スプレッド選択
            logger.info('--- 最適スプレッド選択 ---')
            best_spread = strategy.select_best_spread(spy_price, account_summary)

            if not best_spread:
                logger.error('適切なスプレッドが見つかりませんでした')
                return

            logger.info('')

            # 3. スプレッド検証
            logger.info('--- スプレッド検証 ---')
            is_valid, validation_msg = strategy.validate_spread(best_spread)

            if not is_valid:
                logger.error(f'スプレッド検証失敗: {validation_msg}')
                return

            logger.info(f'✓ スプレッド検証OK: {validation_msg}')
            logger.info('')

            # 4. ポジションサイズ計算
            logger.info('--- ポジションサイズ計算 ---')
            quantity = strategy.calculate_position_size(best_spread, account_summary)
            total_risk = best_spread['max_loss'] * quantity
            total_profit_potential = best_spread['max_profit'] * quantity

            logger.info(f'推奨契約数: {quantity}')
            logger.info(f'総リスク: ${total_risk:.2f}')
            logger.info(f'総利益可能性: ${total_profit_potential:.2f}')
            logger.info('')

            # 5. ポートフォリオリスクチェック
            logger.info('--- ポートフォリオリスクチェック ---')
            if not risk_monitor.can_open_new_position(total_risk, account_summary):
                logger.error('ポートフォリオリスク上限のため、発注を中止します')
                return

            logger.info('')

            # 6. 為替レート取得
            logger.info('--- USD/JPY為替レート取得 ---')
            fx_manager = FXRateManager(ib)
            fx_rate, tts_rate = fx_manager.get_rates_for_trade()

            if fx_rate:
                logger.info(f'USD/JPYレート: {fx_rate:.2f}円')
            logger.info('')

            # 7. 注文確認プロンプト
            logger.info('=' * 60)
            logger.info('📋 注文内容確認')
            logger.info('=' * 60)
            logger.info(f'銘柄: {config.SYMBOL}')
            logger.info(f'満期: {best_spread["exp_date"]} (DTE: {best_spread["dte"]}日)')
            logger.info(f'売りプット: ${best_spread["short_strike"]:.2f} (Δ: {best_spread["short_delta"]:.3f})')
            logger.info(f'買いプット: ${best_spread["long_strike"]:.2f} (Δ: {best_spread["long_delta"]:.3f})')
            logger.info(f'契約数: {quantity}')
            logger.info(f'ネットプレミアム: ${best_spread["net_premium"]:.2f}/契約')
            logger.info(f'最大利益: ${total_profit_potential:.2f}')
            logger.info(f'最大損失: ${total_risk:.2f}')
            logger.info(f'R/R比: {best_spread["risk_reward_ratio"]:.2f}')
            logger.info('=' * 60)

            # ユーザー確認（AUTO_EXECUTEがFalseの場合のみ）
            if not config.AUTO_EXECUTE and not config.USE_MOCK_DATA:
                confirmation = input('\n注文を実行しますか？ (yes/no): ')
                if confirmation.lower() != 'yes':
                    logger.info('注文をキャンセルしました')
                    return
            elif config.AUTO_EXECUTE:
                logger.info('🤖 自動実行モード: 注文を自動的に実行します')
            else:
                logger.info('🎭 モックモード: 自動的に注文を実行します')

            logger.info('')

            # 8. 注文発注
            logger.info('--- 注文発注 ---')
            success, message, order_info = order_manager.place_bull_put_spread(
                best_spread,
                quantity,
                limit_price=best_spread['net_premium']
            )

            if not success:
                logger.error(f'注文失敗: {message}')
                return

            logger.info(f'✓ {message}')
            logger.info('')

            # 9. ポジション記録
            logger.info('--- ポジション記録 ---')

            # スプレッドIDを生成
            timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
            spread_id = f'SPR-{timestamp.strftime("%Y%m%d-%H%M%S")}'

            # 約定価格を取得（モックの場合はfill_price、リアルの場合は約定情報から）
            if config.USE_MOCK_DATA and 'fill_price' in order_info:
                actual_premium = order_info['fill_price']
            else:
                actual_premium = best_spread['net_premium']

            # ポジションを追加
            position_manager.add_position(
                spread_id=spread_id,
                spread=best_spread,
                quantity=quantity,
                entry_premium=actual_premium,
                fx_rate=fx_rate
            )

            logger.info(f'✓ ポジション記録完了: {spread_id}')
            logger.info('')

            # 10. 取引ログ記録（税務対応）
            logger.info('--- 取引ログ記録 ---')

            timestamp_utc = datetime.now(pytz.UTC)
            timestamp_et = timestamp_utc.astimezone(pytz.timezone('US/Eastern'))
            timestamp_jst = timestamp_utc.astimezone(pytz.timezone('Asia/Tokyo'))

            # 手数料（モックまたはリアル）
            commission = order_info.get('commission', 1.30 * quantity * 2)

            # 売りプットの記録
            short_trade_data = {
                'trade_id': f'{spread_id}-SHORT',
                'timestamp_utc': timestamp_utc.isoformat(),
                'timestamp_et': timestamp_et.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_jst': timestamp_jst.strftime('%Y-%m-%d %H:%M:%S'),
                'trade_date_jst': timestamp_jst.strftime('%Y-%m-%d'),
                'symbol': config.SYMBOL,
                'action': 'SELL',
                'option_type': 'PUT',
                'strike': best_spread['short_strike'],
                'expiry': best_spread['exp_date'],
                'quantity': quantity,
                'premium_per_contract': best_spread['short_premium'],
                'total_premium_usd': best_spread['short_premium'] * quantity * 100,
                'commission_usd': commission / 2,
                'net_amount_usd': (best_spread['short_premium'] * quantity * 100) - (commission / 2),
                'fx_rate_usd_jpy': fx_rate,
                'fx_rate_tts': tts_rate,
                'net_amount_jpy': ((best_spread['short_premium'] * quantity * 100) - (commission / 2)) * fx_rate if fx_rate else None,
                'spread_id': spread_id,
                'leg': 'short',
                'position_status': 'open',
                'notes': 'Auto-trade by Step 4'
            }

            # 買いプットの記録
            long_trade_data = {
                'trade_id': f'{spread_id}-LONG',
                'timestamp_utc': timestamp_utc.isoformat(),
                'timestamp_et': timestamp_et.strftime('%Y-%m-%d %H:%M:%S'),
                'timestamp_jst': timestamp_jst.strftime('%Y-%m-%d %H:%M:%S'),
                'trade_date_jst': timestamp_jst.strftime('%Y-%m-%d'),
                'symbol': config.SYMBOL,
                'action': 'BUY',
                'option_type': 'PUT',
                'strike': best_spread['long_strike'],
                'expiry': best_spread['exp_date'],
                'quantity': quantity,
                'premium_per_contract': best_spread['long_premium'],
                'total_premium_usd': best_spread['long_premium'] * quantity * 100,
                'commission_usd': commission / 2,
                'net_amount_usd': -((best_spread['long_premium'] * quantity * 100) + (commission / 2)),
                'fx_rate_usd_jpy': fx_rate,
                'fx_rate_tts': tts_rate,
                'net_amount_jpy': -((best_spread['long_premium'] * quantity * 100) + (commission / 2)) * fx_rate if fx_rate else None,
                'spread_id': spread_id,
                'leg': 'long',
                'position_status': 'open',
                'notes': 'Auto-trade by Step 4'
            }

            # ログに記録
            trading_logger.log_trade(short_trade_data)
            trading_logger.log_trade(long_trade_data)

            logger.info(f'✓ 取引ログ記録完了: {config.TRADE_LOG_FILE}')
            logger.info('')

            # 11. 完了メッセージ
            logger.info('=' * 60)
            logger.info('Step 4 完了: Bull Put Spreadの自動取引が完了しました')
            logger.info('=' * 60)
            logger.info('')
            logger.info('📊 取引サマリー:')
            logger.info(f'  スプレッドID: {spread_id}')
            logger.info(f'  契約数: {quantity}')
            logger.info(f'  ネットプレミアム: ${actual_premium:.2f}/契約')
            logger.info(f'  総プレミアム受取: ${actual_premium * quantity * 100:.2f}')
            logger.info(f'  手数料: ${commission:.2f}')
            logger.info(f'  ネット受取額: ${(actual_premium * quantity * 100) - commission:.2f}')
            if fx_rate:
                logger.info(f'  円換算: ¥{((actual_premium * quantity * 100) - commission) * fx_rate:,.0f}')
            logger.info('')
            logger.info('次のステップ:')
            logger.info('  - logs/positions.json でポジションを確認')
            logger.info('  - logs/trades.csv で取引履歴を確認')
            logger.info('  - ポジション監視機能の実装（Step 5）')

    except KeyboardInterrupt:
        logger.info('\n処理を中断しました')
    except Exception as e:
        logger.error(f'エラーが発生しました: {str(e)}', exc_info=True)


if __name__ == '__main__':
    main()
