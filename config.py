"""
設定ファイル: 戦略パラメータとシステム設定
"""

# 接続設定
TWS_HOST = '127.0.0.1'
TWS_PORT_PAPER = 7497  # ペーパー口座
TWS_PORT_LIVE = 7496   # リアル口座
CLIENT_ID = 1

# デフォルトはペーパー口座を使用
USE_PAPER_ACCOUNT = True
TWS_PORT = TWS_PORT_PAPER if USE_PAPER_ACCOUNT else TWS_PORT_LIVE

# 戦略パラメータ
SYMBOL = 'SPY'
EXCHANGE = 'SMART'
CURRENCY = 'USD'
SPREAD_WIDTH = 5          # $5スプレッド
TARGET_DELTA = 0.20       # 売りプットのデルタ目標
DELTA_RANGE = (0.15, 0.25)  # 許容デルタ範囲
RISK_PER_TRADE = 0.08     # 1取引あたり資金の8%

# 満期設定
# SPYは月・水・金に週次満期がある
# DTE(Days to Expiration)の範囲でフィルタリング
MIN_DTE = 1
MAX_DTE = 7

# ログ設定
LOG_DIR = 'logs/'
TRADE_LOG_FILE = 'logs/trades.csv'
MARKET_DATA_LOG = 'logs/market_data.csv'
SYSTEM_LOG_FILE = 'logs/system.log'

# 為替レート取得設定（税務用）
FX_RATE_SOURCE = 'IBKR'  # IBKRから取得、フォールバックあり
EXCHANGERATE_API_KEY = '10d7371bade6881b469228b4'  # exchangerate-api.com APIキー

# マーケットデータ設定
MARKET_DATA_TYPE = 3  # 1=Live, 2=Frozen, 3=Delayed, 4=Delayed-Frozen
REQUEST_TIMEOUT = 10  # タイムアウト秒数

# モックデータ設定（開発・テスト用）
USE_MOCK_DATA = True  # Falseの場合、実際のIBKR接続を使用（TWSが必要）

# 自動実行設定
AUTO_EXECUTE = True  # Trueの場合、注文前の確認プロンプトをスキップ（完全自動売買）

# メール通知設定
EMAIL_ENABLED = True  # メール通知を有効化
SMTP_SERVER = 'smtp.gmail.com'  # SMTPサーバー（Gmail推奨）
SMTP_PORT = 587  # SMTPポート（TLS）
SMTP_USERNAME = ''  # 環境変数 EMAIL_USERNAME で設定
SMTP_PASSWORD = ''  # 環境変数 EMAIL_PASSWORD で設定（Gmailの場合はアプリパスワード）
EMAIL_FROM = ''  # 送信元メールアドレス（環境変数 EMAIL_FROM で設定）
EMAIL_TO = ''  # 送信先メールアドレス（環境変数 EMAIL_TO で設定）

# VIX急上昇の閾値
VIX_ALERT_THRESHOLD = 25  # VIXがこの値を超えたらアラート
VIX_SPIKE_PERCENT = 20  # VIXが前日比でこの%以上上昇したらアラート

# 週次レポート設定
WEEKLY_REPORT_DAY = 4  # 金曜日（0=月曜, 4=金曜）
WEEKLY_REPORT_TIME = '16:00'  # 米国東部時間（マーケット終了時刻）

# === Step 4 追加設定: 自動発注 ===

# 自動発注スケジュール（US Eastern Time）
ENTRY_TIME = '09:35'           # マーケット開始5分後
ENTRY_DAY = 'monday'           # 月曜エントリー
WEEKLY_SUMMARY_TIME = '16:05'  # 金曜マーケット終了5分後

# 注文設定
ORDER_TIMEOUT_SEC = 300        # 5分で約定しなければキャンセル
LIMIT_PRICE_OFFSET = 0.02     # midpointから$0.02有利に指値
MAX_SLIPPAGE = 0.10            # 許容スリッページ

# 損切り設定
STOP_LOSS_MULTIPLIER = 2.0    # エントリープレミアムの2倍で損切り
# 例: $1.50で入った場合、スプレッドプレミアムが$3.00に届いたら損切り

# Fear & Greed Index
FEAR_GREED_API_URL = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
FEAR_GREED_TIMEOUT = 10        # 取得タイムアウト（秒）

# メール通知（環境変数から読み込み）
import os
NOTIFICATION_EMAIL = os.getenv('EMAIL_TO', os.getenv('NOTIFICATION_EMAIL', ''))
SMTP_HOST = os.getenv('SMTP_HOST', SMTP_SERVER)
SMTP_PORT_NUM = int(os.getenv('SMTP_PORT_NUM', str(SMTP_PORT)))
SMTP_USER = os.getenv('EMAIL_USERNAME', os.getenv('SMTP_USER', ''))
SMTP_PASSWORD_VAR = os.getenv('EMAIL_PASSWORD', os.getenv('SMTP_PASSWORD', ''))

# イベントカレンダー（2026年）
ECONOMIC_EVENTS = {
    # FOMC（水曜14:00 ET発表）
    'FOMC': [
        '2026-01-28', '2026-03-18', '2026-05-06', '2026-06-17',
        '2026-07-29', '2026-09-16', '2026-11-04', '2026-12-16',
    ],
    # 雇用統計（毎月第1金曜 8:30 ET）
    'NFP': [
        '2026-01-02', '2026-02-06', '2026-03-06', '2026-04-03',
        '2026-05-01', '2026-06-05', '2026-07-02', '2026-08-07',
        '2026-09-04', '2026-10-02', '2026-11-06', '2026-12-04',
    ],
    # CPI（毎月中旬）— 発表日は事前に確認して追加
    'CPI': [
        '2026-01-13', '2026-02-11', '2026-03-11', '2026-04-10',
        '2026-05-13', '2026-06-10', '2026-07-14', '2026-08-12',
        '2026-09-14', '2026-10-13', '2026-11-12', '2026-12-10',
    ],
}

# イベント日を跨ぐ満期は避ける
def is_event_day(date_str: str) -> tuple[bool, str]:
    """
    指定日がイベント日かチェック。(True/False, イベント名)を返す

    Args:
        date_str: 'YYYY-MM-DD' 形式の日付文字列

    Returns:
        (is_event, event_name): イベント日の場合True、イベント名を返す
    """
    for event_name, dates in ECONOMIC_EVENTS.items():
        if date_str in dates:
            return True, event_name
    return False, ''
