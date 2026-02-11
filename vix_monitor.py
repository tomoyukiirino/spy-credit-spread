"""
VIX監視モジュール
ボラティリティの急上昇を監視してアラート送信
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv
import config
from logger import get_logger
from email_notification import get_email_notifier

# .envファイルを読み込み
load_dotenv()

# モックデータモードの判定
if config.USE_MOCK_DATA:
    from mock_data import MockMarketDataManager as MarketDataManager
else:
    from data import MarketDataManager


class VIXMonitor:
    """VIX監視クラス"""

    def __init__(self, market_data_manager=None):
        """
        Args:
            market_data_manager: MarketDataManagerインスタンス（Noneの場合は新規作成）
        """
        self.logger = get_logger()
        self.email_notifier = get_email_notifier()
        self.market_data = market_data_manager

        # VIX履歴ファイル
        self.vix_history_file = 'logs/vix_history.json'
        self._ensure_vix_history_file()

    def _ensure_vix_history_file(self):
        """VIX履歴ファイルが存在することを確認"""
        if not os.path.exists(self.vix_history_file):
            os.makedirs(os.path.dirname(self.vix_history_file), exist_ok=True)
            self._save_vix_history({})

    def _load_vix_history(self) -> Dict:
        """VIX履歴を読み込み"""
        try:
            with open(self.vix_history_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_vix_history(self, history: Dict):
        """VIX履歴を保存"""
        try:
            with open(self.vix_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            self.logger.error(f'VIX履歴保存エラー: {str(e)}')

    def get_current_vix(self) -> Optional[float]:
        """
        現在のVIX指数を取得

        Returns:
            VIX値、取得失敗時はNone
        """
        try:
            if self.market_data is None:
                self.logger.warning('MarketDataManagerが初期化されていません')
                return None

            vix_data = self.market_data.get_vix()

            if vix_data and 'vix' in vix_data:
                vix = vix_data['vix']
                self.logger.info(f'現在のVIX: {vix:.2f}')
                return vix
            else:
                self.logger.warning('VIXデータの取得に失敗しました')
                return None

        except Exception as e:
            self.logger.error(f'VIX取得エラー: {str(e)}')
            return None

    def record_vix(self, vix: float):
        """
        VIX値を履歴に記録

        Args:
            vix: VIX値
        """
        history = self._load_vix_history()
        today = datetime.now().strftime('%Y-%m-%d')

        history[today] = {
            'vix': vix,
            'timestamp': datetime.now().isoformat()
        }

        # 古い履歴を削除（30日分のみ保持）
        if len(history) > 30:
            sorted_dates = sorted(history.keys())
            for date in sorted_dates[:-30]:
                del history[date]

        self._save_vix_history(history)
        self.logger.debug(f'VIX記録: {vix:.2f} ({today})')

    def get_previous_vix(self) -> Optional[float]:
        """
        前回記録したVIX値を取得

        Returns:
            前回のVIX値、履歴がない場合はNone
        """
        history = self._load_vix_history()

        if not history:
            return None

        # 最新の日付のVIXを取得
        sorted_dates = sorted(history.keys(), reverse=True)

        if len(sorted_dates) > 0:
            latest_date = sorted_dates[0]
            return history[latest_date]['vix']

        return None

    def check_vix_spike(self, current_vix: float, previous_vix: float) -> tuple:
        """
        VIX急上昇をチェック

        Args:
            current_vix: 現在のVIX
            previous_vix: 前回のVIX

        Returns:
            (is_spike, change_percent)
        """
        if previous_vix == 0:
            return False, 0.0

        # 変化率を計算
        change_percent = ((current_vix - previous_vix) / previous_vix) * 100

        # 閾値チェック
        is_absolute_high = current_vix >= config.VIX_ALERT_THRESHOLD
        is_spike = change_percent >= config.VIX_SPIKE_PERCENT

        if is_absolute_high or is_spike:
            self.logger.warning(f'⚠️ VIX急上昇検出!')
            self.logger.warning(f'  現在値: {current_vix:.2f}')
            self.logger.warning(f'  前回値: {previous_vix:.2f}')
            self.logger.warning(f'  変化率: +{change_percent:.1f}%')
            return True, change_percent

        return False, change_percent

    def monitor_and_alert(self) -> bool:
        """
        VIXを監視してアラートを送信

        Returns:
            アラートが送信されたかどうか
        """
        self.logger.info('--- VIX監視チェック ---')

        try:
            # 現在のVIXを取得
            current_vix = self.get_current_vix()

            if current_vix is None:
                self.logger.warning('VIX値の取得に失敗しました')
                return False

            # 前回のVIXを取得
            previous_vix = self.get_previous_vix()

            # VIXを記録
            self.record_vix(current_vix)

            if previous_vix is None:
                self.logger.info('前回のVIX履歴なし。今回から記録開始。')
                return False

            # VIX急上昇チェック
            is_spike, change_percent = self.check_vix_spike(current_vix, previous_vix)

            if is_spike:
                # アラートメール送信
                success = self.email_notifier.send_vix_alert(
                    vix_current=current_vix,
                    vix_previous=previous_vix,
                    change_percent=change_percent
                )

                if success:
                    self.logger.info('✓ VIXアラートメール送信成功')
                else:
                    self.logger.warning('VIXアラートメール送信失敗またはスキップ')

                return success
            else:
                self.logger.info(f'VIX正常範囲: {current_vix:.2f} (変化: {change_percent:+.1f}%)')
                return False

        except Exception as e:
            self.logger.error(f'VIX監視エラー: {str(e)}')
            return False


def main():
    """VIX監視スクリプト（cron等から定期実行）"""
    logger = get_logger()

    logger.info('=' * 60)
    logger.info('VIX監視スクリプト')
    logger.info('=' * 60)

    # モックデータモードの判定
    if config.USE_MOCK_DATA:
        from mock_data import MockIBKRConnection as IBKRConnection
        from mock_data import MockMarketDataManager as MarketDataManager
        logger.info('🎭 モード: モックデータ')
    else:
        from connection import IBKRConnection
        from data import MarketDataManager
        logger.info('📡 モード: リアルデータ')

    try:
        with IBKRConnection(use_paper=config.USE_PAPER_ACCOUNT) as conn:
            ib = conn.get_ib()
            market_data = MarketDataManager(ib)

            # VIXモニター作成
            vix_monitor = VIXMonitor(market_data)

            # 監視実行
            vix_monitor.monitor_and_alert()

    except Exception as e:
        logger.error(f'処理エラー: {str(e)}')


if __name__ == '__main__':
    main()
