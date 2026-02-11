"""
メール通知モジュール
トレード結果、VIXアラート、損切り通知をメールで送信
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv
import config
from logger import get_logger

# .envファイルを読み込み
load_dotenv()


class EmailNotifier:
    """メール通知管理クラス"""

    def __init__(self):
        """初期化"""
        self.logger = get_logger()

        # 環境変数から設定を読み込み
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.username = os.getenv('EMAIL_USERNAME', config.SMTP_USERNAME)
        self.password = os.getenv('EMAIL_PASSWORD', config.SMTP_PASSWORD)
        self.from_email = os.getenv('EMAIL_FROM', config.EMAIL_FROM)
        self.to_email = os.getenv('EMAIL_TO', config.EMAIL_TO)
        self.enabled = config.EMAIL_ENABLED

        # 設定検証
        if not self._validate_config():
            self.logger.warning('メール設定が不完全です。通知は無効化されます。')
            self.enabled = False

    def _validate_config(self) -> bool:
        """メール設定の検証"""
        if not self.username or not self.password:
            self.logger.warning('EMAIL_USERNAME または EMAIL_PASSWORD が設定されていません')
            return False

        if not self.from_email or not self.to_email:
            self.logger.warning('EMAIL_FROM または EMAIL_TO が設定されていません')
            return False

        return True

    def send_email(
        self,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """
        メールを送信

        Args:
            subject: 件名
            body: 本文
            is_html: HTML形式かどうか

        Returns:
            送信成功かどうか
        """
        if not self.enabled:
            self.logger.info(f'メール送信がスキップされました（無効化）: {subject}')
            return False

        try:
            # メッセージ作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # 本文を追加
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, mime_type, 'utf-8'))

            # SMTP接続
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f'✓ メール送信成功: {subject}')
            return True

        except Exception as e:
            self.logger.error(f'✗ メール送信失敗: {subject} - {str(e)}')
            return False

    def send_weekly_report(
        self,
        week_summary: Dict,
        trades: List[Dict]
    ) -> bool:
        """
        週次レポートを送信

        Args:
            week_summary: 週次サマリー
            trades: 今週の取引リスト

        Returns:
            送信成功かどうか
        """
        subject = f"📊 週次トレードレポート - {week_summary['week_start']} 〜 {week_summary['week_end']}"

        # HTML本文を作成
        body = self._create_weekly_report_html(week_summary, trades)

        return self.send_email(subject, body, is_html=True)

    def send_vix_alert(
        self,
        vix_current: float,
        vix_previous: float,
        change_percent: float
    ) -> bool:
        """
        VIX急上昇アラートを送信

        Args:
            vix_current: 現在のVIX
            vix_previous: 前回のVIX
            change_percent: 変化率（%）

        Returns:
            送信成功かどうか
        """
        subject = f"⚠️ VIX急上昇アラート - 現在値: {vix_current:.2f}"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background-color: #fee; padding: 20px; border-left: 5px solid #f44; }}
                .stats {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; }}
                .warning {{ color: #d00; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h2>⚠️ VIX急上昇アラート</h2>
                <p class="warning">ボラティリティが急激に上昇しています。</p>
            </div>

            <div class="stats">
                <h3>VIX指数</h3>
                <ul>
                    <li><strong>現在値:</strong> {vix_current:.2f}</li>
                    <li><strong>前回値:</strong> {vix_previous:.2f}</li>
                    <li><strong>変化率:</strong> <span style="color: #d00;">+{change_percent:.1f}%</span></li>
                </ul>
            </div>

            <h3>推奨アクション</h3>
            <ul>
                <li>新規ポジションのオープンを控える</li>
                <li>既存ポジションのリスクを確認</li>
                <li>損切りラインを見直す</li>
                <li>市場の動向を注視</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                送信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body, is_html=True)

    def send_stop_loss_alert(
        self,
        position: Dict,
        estimated_loss: float,
        reason: str
    ) -> bool:
        """
        損切り通知を送信

        Args:
            position: ポジション情報
            estimated_loss: 想定損失額
            reason: 損切り理由

        Returns:
            送信成功かどうか
        """
        subject = f"🚨 損切り実行通知 - 想定損失: ${estimated_loss:.2f}"

        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ background-color: #fee; padding: 20px; border-left: 5px solid #f44; }}
                .position {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; }}
                .loss {{ color: #d00; font-weight: bold; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="alert">
                <h2>🚨 損切り実行通知</h2>
                <p><strong>理由:</strong> {reason}</p>
            </div>

            <div class="position">
                <h3>ポジション詳細</h3>
                <ul>
                    <li><strong>銘柄:</strong> {position.get('symbol', 'SPY')}</li>
                    <li><strong>満期日:</strong> {position.get('expiry', 'N/A')}</li>
                    <li><strong>売りストライク:</strong> ${position.get('short_strike', 0):.2f}</li>
                    <li><strong>買いストライク:</strong> ${position.get('long_strike', 0):.2f}</li>
                    <li><strong>契約数:</strong> {position.get('quantity', 0)}</li>
                </ul>
            </div>

            <div class="position">
                <h3>損失情報</h3>
                <p class="loss">想定損失: ${estimated_loss:.2f} USD</p>
                <p>日本円換算: 約 ¥{estimated_loss * 150:.0f} （為替レート150円想定）</p>
            </div>

            <h3>次のステップ</h3>
            <ul>
                <li>ダッシュボードで実際の約定価格を確認</li>
                <li>取引ログを確認</li>
                <li>今後の戦略を見直す</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                送信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """

        return self.send_email(subject, body, is_html=True)

    def _create_weekly_report_html(
        self,
        summary: Dict,
        trades: List[Dict]
    ) -> str:
        """週次レポートのHTML本文を生成"""

        # 損益の色を決定
        net_pnl = summary.get('net_pnl', 0)
        pnl_color = '#0a0' if net_pnl >= 0 else '#d00'
        pnl_sign = '+' if net_pnl >= 0 else ''

        # 取引履歴のHTML生成
        trades_html = ''
        for trade in trades:
            trade_pnl = trade.get('pnl', 0)
            trade_color = '#0a0' if trade_pnl >= 0 else '#d00'

            trades_html += f"""
            <tr>
                <td>{trade.get('date', 'N/A')}</td>
                <td>{trade.get('action', 'N/A')}</td>
                <td>${trade.get('strike', 0):.2f}</td>
                <td style="color: {trade_color}; font-weight: bold;">${trade_pnl:+.2f}</td>
            </tr>
            """

        if not trades_html:
            trades_html = '<tr><td colspan="4" style="text-align: center; color: #999;">今週の取引はありません</td></tr>'

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #2c5aa0; color: white; padding: 20px; }}
                .summary {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; }}
                .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
                .stat-box {{ background: white; padding: 15px; border-left: 4px solid #2c5aa0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #2c5aa0; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 SPY クレジットスプレッド 週次レポート</h1>
                <p>{summary.get('week_start', 'N/A')} 〜 {summary.get('week_end', 'N/A')}</p>
            </div>

            <div class="summary">
                <h2>週間サマリー</h2>
                <div class="stats">
                    <div class="stat-box">
                        <h3>純損益（USD）</h3>
                        <p style="font-size: 24px; color: {pnl_color}; font-weight: bold;">
                            {pnl_sign}${net_pnl:.2f}
                        </p>
                    </div>
                    <div class="stat-box">
                        <h3>純損益（JPY）</h3>
                        <p style="font-size: 24px; color: {pnl_color}; font-weight: bold;">
                            {pnl_sign}¥{summary.get('net_pnl_jpy', 0):.0f}
                        </p>
                    </div>
                    <div class="stat-box">
                        <h3>取引回数</h3>
                        <p style="font-size: 24px;">{summary.get('total_trades', 0)}</p>
                    </div>
                    <div class="stat-box">
                        <h3>勝率</h3>
                        <p style="font-size: 24px;">{summary.get('win_rate', 0):.1f}%</p>
                    </div>
                </div>
            </div>

            <h2>取引履歴</h2>
            <table>
                <thead>
                    <tr>
                        <th>日付</th>
                        <th>アクション</th>
                        <th>ストライク</th>
                        <th>損益</th>
                    </tr>
                </thead>
                <tbody>
                    {trades_html}
                </tbody>
            </table>

            <div class="summary">
                <h2>統計情報</h2>
                <ul>
                    <li><strong>総プレミアム受取:</strong> ${summary.get('total_premium_received', 0):.2f}</li>
                    <li><strong>総手数料:</strong> ${summary.get('total_commission', 0):.2f}</li>
                    <li><strong>オープンポジション:</strong> {summary.get('open_positions', 0)}件</li>
                    <li><strong>平均USD/JPYレート:</strong> ¥{summary.get('avg_fx_rate', 150):.2f}</li>
                </ul>
            </div>

            <div class="footer">
                <p>このレポートは自動生成されました。</p>
                <p>送信日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>© 2026 SPY Bull Put Credit Spread Dashboard</p>
            </div>
        </body>
        </html>
        """

        return html


# グローバルインスタンス
_email_notifier = None


def get_email_notifier() -> EmailNotifier:
    """EmailNotifierのシングルトンインスタンスを取得"""
    global _email_notifier
    if _email_notifier is None:
        _email_notifier = EmailNotifier()
    return _email_notifier
