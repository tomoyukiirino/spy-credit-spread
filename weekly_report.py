"""
週次レポート生成モジュール
毎週金曜日にトレード結果をまとめてメール送信
"""

import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from dotenv import load_dotenv
import config
from logger import get_logger
from email_notification import get_email_notifier

# .envファイルを読み込み
load_dotenv()


class WeeklyReportGenerator:
    """週次レポート生成クラス"""

    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self.email_notifier = get_email_notifier()
        self.trade_log_file = config.TRADE_LOG_FILE

    def get_week_range(self, target_date: Optional[datetime] = None) -> tuple:
        """
        週の開始日と終了日を取得（月曜日〜金曜日）

        Args:
            target_date: 基準日（Noneの場合は今日）

        Returns:
            (week_start, week_end) のタプル
        """
        if target_date is None:
            target_date = datetime.now()

        # 今週の月曜日を取得
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)

        # 今週の金曜日を取得
        week_end = week_start + timedelta(days=4)

        return week_start.date(), week_end.date()

    def load_trades_for_week(
        self,
        week_start: datetime.date,
        week_end: datetime.date
    ) -> List[Dict]:
        """
        指定週の取引を取得

        Args:
            week_start: 週の開始日
            week_end: 週の終了日

        Returns:
            取引リスト
        """
        if not os.path.exists(self.trade_log_file):
            self.logger.warning(f'取引ログファイルが見つかりません: {self.trade_log_file}')
            return []

        try:
            # CSVを読み込み
            df = pd.read_csv(self.trade_log_file)

            if df.empty:
                return []

            # 日付列をdatetime型に変換
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # 週の範囲でフィルタリング
            mask = (df['timestamp'].dt.date >= week_start) & (df['timestamp'].dt.date <= week_end)
            week_df = df[mask]

            # 辞書のリストに変換
            trades = week_df.to_dict('records')

            self.logger.info(f'{week_start} 〜 {week_end} の取引: {len(trades)}件')
            return trades

        except Exception as e:
            self.logger.error(f'取引ログの読み込みエラー: {str(e)}')
            return []

    def calculate_week_summary(
        self,
        trades: List[Dict],
        week_start: datetime.date,
        week_end: datetime.date
    ) -> Dict:
        """
        週次サマリーを計算

        Args:
            trades: 取引リスト
            week_start: 週の開始日
            week_end: 週の終了日

        Returns:
            サマリー辞書
        """
        summary = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'total_trades': len(trades),
            'net_pnl': 0.0,
            'net_pnl_jpy': 0.0,
            'total_premium_received': 0.0,
            'total_premium_paid': 0.0,
            'total_commission': 0.0,
            'win_count': 0,
            'loss_count': 0,
            'win_rate': 0.0,
            'open_positions': 0,
            'avg_fx_rate': 150.0  # デフォルト
        }

        if not trades:
            return summary

        try:
            # DataFrameに変換して計算
            df = pd.DataFrame(trades)

            # 損益計算
            if 'pnl_usd' in df.columns:
                summary['net_pnl'] = df['pnl_usd'].sum()

            if 'pnl_jpy' in df.columns:
                summary['net_pnl_jpy'] = df['pnl_jpy'].sum()

            # プレミアム計算
            if 'premium_received' in df.columns:
                summary['total_premium_received'] = df['premium_received'].sum()

            if 'premium_paid' in df.columns:
                summary['total_premium_paid'] = df['premium_paid'].sum()

            # 手数料計算
            if 'commission' in df.columns:
                summary['total_commission'] = df['commission'].sum()

            # 勝敗カウント
            if 'pnl_usd' in df.columns:
                summary['win_count'] = (df['pnl_usd'] > 0).sum()
                summary['loss_count'] = (df['pnl_usd'] < 0).sum()

            # 勝率計算
            if summary['total_trades'] > 0:
                summary['win_rate'] = (summary['win_count'] / summary['total_trades']) * 100

            # 平均為替レート
            if 'fx_rate' in df.columns:
                summary['avg_fx_rate'] = df['fx_rate'].mean()

            # オープンポジションのカウント（'OPEN'ステータス）
            if 'status' in df.columns:
                summary['open_positions'] = (df['status'] == 'OPEN').sum()

        except Exception as e:
            self.logger.error(f'サマリー計算エラー: {str(e)}')

        return summary

    def format_trades_for_report(self, trades: List[Dict]) -> List[Dict]:
        """
        レポート用に取引をフォーマット

        Args:
            trades: 取引リスト

        Returns:
            フォーマット済み取引リスト
        """
        formatted_trades = []

        for trade in trades:
            formatted = {
                'date': trade.get('timestamp', ''),
                'action': trade.get('action', 'N/A'),
                'strike': trade.get('strike', 0.0),
                'pnl': trade.get('pnl_usd', 0.0)
            }

            # 日付をフォーマット
            if isinstance(formatted['date'], str):
                try:
                    dt = pd.to_datetime(formatted['date'])
                    formatted['date'] = dt.strftime('%Y-%m-%d')
                except:
                    formatted['date'] = 'N/A'

            formatted_trades.append(formatted)

        return formatted_trades

    def generate_and_send_report(self, target_date: Optional[datetime] = None) -> bool:
        """
        週次レポートを生成して送信

        Args:
            target_date: 基準日（Noneの場合は今日）

        Returns:
            送信成功かどうか
        """
        self.logger.info('=' * 60)
        self.logger.info('週次レポート生成開始')
        self.logger.info('=' * 60)

        try:
            # 週の範囲を取得
            week_start, week_end = self.get_week_range(target_date)
            self.logger.info(f'対象期間: {week_start} 〜 {week_end}')

            # 取引を読み込み
            trades = self.load_trades_for_week(week_start, week_end)

            # サマリーを計算
            summary = self.calculate_week_summary(trades, week_start, week_end)

            # 取引をフォーマット
            formatted_trades = self.format_trades_for_report(trades)

            # メール送信
            success = self.email_notifier.send_weekly_report(summary, formatted_trades)

            if success:
                self.logger.info('✓ 週次レポート送信成功')
            else:
                self.logger.warning('週次レポート送信失敗またはスキップされました')

            return success

        except Exception as e:
            self.logger.error(f'週次レポート生成エラー: {str(e)}')
            return False

    def should_send_today(self) -> bool:
        """
        今日がレポート送信日かどうかをチェック

        Returns:
            送信すべきかどうか
        """
        today = datetime.now()

        # 金曜日かどうか
        is_friday = today.weekday() == config.WEEKLY_REPORT_DAY

        if not is_friday:
            return False

        # 時刻チェック（米国東部時間を想定）
        current_time = today.strftime('%H:%M')
        target_time = config.WEEKLY_REPORT_TIME

        # 簡易的な時刻チェック（実際にはタイムゾーン変換が必要）
        return current_time >= target_time


def main():
    """週次レポート生成スクリプト（cron等から実行）"""
    logger = get_logger()

    logger.info('=' * 60)
    logger.info('週次レポート生成スクリプト')
    logger.info('=' * 60)

    generator = WeeklyReportGenerator()

    # レポート生成と送信
    success = generator.generate_and_send_report()

    if success:
        logger.info('✓ 処理完了')
    else:
        logger.error('✗ 処理失敗')


if __name__ == '__main__':
    main()
