"""
Step 3 動作確認用メインスクリプト
マーケットデータ取得とBull Put Spread候補の表示
"""

from datetime import datetime
import pytz
import config
from logger import get_trading_logger, get_logger

# モックデータモードの判定
if config.USE_MOCK_DATA:
    from mock_data import MockIBKRConnection as IBKRConnection
    from mock_data import MockMarketDataManager as MarketDataManager
    from mock_data import MockFXRateManager as FXRateManager
else:
    from connection import IBKRConnection
    from data import MarketDataManager
    from fx_rate import FXRateManager


def main():
    """Step 3のメイン処理フロー"""
    logger = get_logger()
    trading_logger = get_trading_logger()

    logger.info('=' * 60)
    logger.info('SPY Bull Put Credit Spread - Step 3: マーケットデータ取得')
    if config.USE_MOCK_DATA:
        logger.info('🎭 モード: モックデータ（開発・テスト用）')
    else:
        logger.info('📡 モード: リアルデータ（IBKR TWS接続）')
    logger.info('=' * 60)

    try:
        # 1. IBKR接続
        with IBKRConnection(use_paper=config.USE_PAPER_ACCOUNT) as conn:
            logger.info('')

            # 2. 口座情報表示
            conn.print_account_info()
            logger.info('')

            # IBインスタンスを取得
            ib = conn.get_ib()

            # MarketDataManagerを初期化
            market_data = MarketDataManager(ib)

            # 3. SPY現在価格取得・表示
            logger.info('--- SPY価格取得 ---')
            spy_price_data = market_data.get_spy_price()

            if not spy_price_data:
                logger.error('SPY価格の取得に失敗しました')
                return

            spy_price = spy_price_data['last']
            logger.info('')

            # 4. オプションチェーン取得
            logger.info('--- オプションチェーン取得 ---')
            expirations = market_data.get_option_chain_params()

            if not expirations:
                logger.error('満期日の取得に失敗しました')
                return

            logger.info('')

            # 最も近い満期日を選択
            selected_expiration = expirations[0]
            exp_date = datetime.strptime(selected_expiration, '%Y%m%d').date()
            logger.info(f'選択された満期日: {exp_date.strftime("%Y-%m-%d")} ({selected_expiration})')
            logger.info('')

            # 5. Putオプション一覧取得・表示（デルタ、IV、Bid/Ask付き）
            logger.info('--- Putオプション取得（Greeks付き）---')
            logger.info('※ データ取得に時間がかかります...')
            options_df = market_data.get_put_options_with_greeks(
                selected_expiration,
                spy_price
            )

            if options_df.empty:
                logger.error('Putオプションの取得に失敗しました')
                return

            # オプション一覧を表示
            market_data.display_options_table(options_df, f'Putオプション一覧（満期: {exp_date}）')
            logger.info('')

            # 6. デルタ≒0.20のBull Put Spread候補表示
            logger.info('--- Bull Put Spread候補の特定 ---')

            # 目標デルタに最も近い売りプットを見つける
            short_put = market_data.find_target_delta_strike(options_df)

            if not short_put:
                logger.error('目標デルタの売りプットが見つかりませんでした')
                return

            logger.info(f'売りプット候補: ${short_put["strike"]:.2f} (デルタ: {short_put["delta"]:.3f})')

            # スプレッドペアを見つける
            spread_info = market_data.find_spread_pair(short_put, options_df)

            if not spread_info:
                logger.error('スプレッドペアが見つかりませんでした')
                return

            # スプレッド情報を表示
            market_data.display_spread_info(spread_info)
            logger.info('')

            # 7. USD/JPYレート取得・表示
            logger.info('--- USD/JPY為替レート取得 ---')
            fx_manager = FXRateManager(ib)
            fx_rate, tts_rate = fx_manager.get_rates_for_trade()

            if fx_rate:
                logger.info(f'USD/JPYレート: {fx_rate:.2f}円')
            else:
                logger.warning('USD/JPYレートを取得できませんでした')

            if tts_rate:
                logger.info(f'TTSレート: {tts_rate:.2f}円')
            else:
                logger.info('TTSレートは手動入力が必要です')

            logger.info('')

            # 8. マーケットデータをCSVログに記録
            logger.info('--- マーケットデータをログに記録 ---')

            # 現在時刻（UTC）
            timestamp_utc = datetime.now(pytz.UTC).isoformat()

            market_log_data = {
                'timestamp_utc': timestamp_utc,
                'spy_price': spy_price,
                'spy_bid': spy_price_data['bid'],
                'spy_ask': spy_price_data['ask'],
                'vix_level': '',  # VIXは将来実装
                'selected_strike_short': spread_info['short_strike'],
                'selected_strike_long': spread_info['long_strike'],
                'short_put_delta': spread_info['short_delta'],
                'short_put_iv': spread_info['short_iv'],
                'spread_premium_mid': spread_info['net_premium'],
                'max_profit': spread_info['max_profit'],
                'max_loss': spread_info['max_loss'],
                'risk_reward_ratio': spread_info['risk_reward_ratio'],
                'fx_rate_usd_jpy': fx_rate if fx_rate else ''
            }

            trading_logger.log_market_data(market_log_data)
            logger.info(f'マーケットデータを記録: {config.MARKET_DATA_LOG}')
            logger.info('')

            # 9. 完了メッセージ
            logger.info('=' * 60)
            logger.info('Step 3 完了: マーケットデータ取得が正常に動作しました')
            logger.info('=' * 60)
            logger.info('')
            logger.info('次のステップ:')
            logger.info('  - Step 4: 注文執行機能の実装')
            logger.info('  - logs/market_data.csv でマーケットデータを確認')
            logger.info('  - logs/system.log でシステムログを確認')

    except KeyboardInterrupt:
        logger.info('\n処理を中断しました')
    except Exception as e:
        logger.error(f'エラーが発生しました: {str(e)}', exc_info=True)


if __name__ == '__main__':
    main()
