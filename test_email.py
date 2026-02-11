"""
メール送信テストスクリプト
各種メール通知が正しく送信されるかテスト
"""

from datetime import datetime
from dotenv import load_dotenv
from email_notification import get_email_notifier
from logger import get_logger

# .envファイルを読み込み
load_dotenv()


def test_weekly_report():
    """週次レポートのテスト"""
    print('\n' + '=' * 60)
    print('週次レポートのテスト')
    print('=' * 60)

    notifier = get_email_notifier()

    # テストデータ
    week_summary = {
        'week_start': '2026-02-10',
        'week_end': '2026-02-14',
        'total_trades': 5,
        'net_pnl': 125.50,
        'net_pnl_jpy': 18825,
        'total_premium_received': 200.00,
        'total_premium_paid': 50.00,
        'total_commission': 24.50,
        'win_count': 4,
        'loss_count': 1,
        'win_rate': 80.0,
        'open_positions': 2,
        'avg_fx_rate': 150.0
    }

    trades = [
        {
            'date': '2026-02-10',
            'action': 'OPEN Bull Put Spread',
            'strike': 580.0,
            'pnl': 45.00
        },
        {
            'date': '2026-02-11',
            'action': 'CLOSE Bull Put Spread',
            'strike': 575.0,
            'pnl': 35.50
        },
        {
            'date': '2026-02-12',
            'action': 'OPEN Bull Put Spread',
            'strike': 582.0,
            'pnl': 40.00
        },
        {
            'date': '2026-02-13',
            'action': 'CLOSE Bull Put Spread',
            'strike': 578.0,
            'pnl': -20.00
        },
        {
            'date': '2026-02-14',
            'action': 'OPEN Bull Put Spread',
            'strike': 585.0,
            'pnl': 25.00
        },
    ]

    success = notifier.send_weekly_report(week_summary, trades)

    if success:
        print('✓ 週次レポート送信成功')
    else:
        print('✗ 週次レポート送信失敗')

    return success


def test_vix_alert():
    """VIXアラートのテスト"""
    print('\n' + '=' * 60)
    print('VIXアラートのテスト')
    print('=' * 60)

    notifier = get_email_notifier()

    # テストデータ
    vix_current = 28.5
    vix_previous = 18.2
    change_percent = ((vix_current - vix_previous) / vix_previous) * 100

    success = notifier.send_vix_alert(
        vix_current=vix_current,
        vix_previous=vix_previous,
        change_percent=change_percent
    )

    if success:
        print('✓ VIXアラート送信成功')
    else:
        print('✗ VIXアラート送信失敗')

    return success


def test_stop_loss_alert():
    """損切りアラートのテスト"""
    print('\n' + '=' * 60)
    print('損切りアラートのテスト')
    print('=' * 60)

    notifier = get_email_notifier()

    # テストデータ
    position = {
        'symbol': 'SPY',
        'expiry': '2026-02-21',
        'short_strike': 580.0,
        'long_strike': 575.0,
        'quantity': 10
    }

    estimated_loss = 425.50

    success = notifier.send_stop_loss_alert(
        position=position,
        estimated_loss=estimated_loss,
        reason='SPY価格がショートストライク$580.00の98%を下回りました'
    )

    if success:
        print('✓ 損切りアラート送信成功')
    else:
        print('✗ 損切りアラート送信失敗')

    return success


def main():
    """すべてのメール通知をテスト"""
    logger = get_logger()

    print('=' * 60)
    print('メール通知機能テスト')
    print('=' * 60)
    print(f'実行時刻: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # 環境変数チェック
    import os
    print('\n環境変数チェック:')
    print(f'  EMAIL_USERNAME: {"設定済み" if os.getenv("EMAIL_USERNAME") else "未設定"}')
    print(f'  EMAIL_PASSWORD: {"設定済み" if os.getenv("EMAIL_PASSWORD") else "未設定"}')
    print(f'  EMAIL_FROM: {"設定済み" if os.getenv("EMAIL_FROM") else "未設定"}')
    print(f'  EMAIL_TO: {"設定済み" if os.getenv("EMAIL_TO") else "未設定"}')

    if not all([
        os.getenv('EMAIL_USERNAME'),
        os.getenv('EMAIL_PASSWORD'),
        os.getenv('EMAIL_FROM'),
        os.getenv('EMAIL_TO')
    ]):
        print('\n⚠️ 環境変数が設定されていません。')
        print('.envファイルを作成して、以下の環境変数を設定してください:')
        print('  EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_TO')
        print('\n.env.exampleを参考にしてください。')
        return

    # テスト実行
    results = {
        '週次レポート': test_weekly_report(),
        'VIXアラート': test_vix_alert(),
        '損切りアラート': test_stop_loss_alert()
    }

    # 結果サマリー
    print('\n' + '=' * 60)
    print('テスト結果サマリー')
    print('=' * 60)

    for test_name, success in results.items():
        status = '✓ 成功' if success else '✗ 失敗'
        print(f'{test_name}: {status}')

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f'\n合計: {passed_tests}/{total_tests} 成功')

    if passed_tests == total_tests:
        print('\n🎉 すべてのテストに合格しました！')
    else:
        print('\n⚠️ 一部のテストが失敗しました。ログを確認してください。')


if __name__ == '__main__':
    main()
