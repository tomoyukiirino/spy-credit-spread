"""
取引ログAPIルーター
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
import pytz
import io
import csv

router = APIRouter()


@router.get("/trades")
async def get_trades():
    """
    取引ログを取得

    Returns:
        dict: 取引ログのリスト
    """
    from main import app_state

    position_manager = app_state.get('position_manager')
    if not position_manager:
        # ポジションマネージャーがない場合はモックデータを返す
        return _get_mock_trades()

    try:
        # 実際の実装ではposition_managerから取引履歴を取得
        # 現時点ではモックデータを返す
        return _get_mock_trades()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {str(e)}")


@router.get("/trades/export-csv")
async def export_trades_csv():
    """
    取引ログをCSV形式でエクスポート

    Returns:
        StreamingResponse: CSVファイル
    """
    try:
        trades_data = _get_mock_trades()
        trades = trades_data.get('trades', [])

        # CSVデータを生成
        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow([
            '取引ID', '日時(JST)', '銘柄', 'アクション', 'タイプ',
            'ストライク', '期限', '数量', 'プレミアム/契約', '総プレミアム(USD)',
            '手数料(USD)', '純額(USD)', '為替レート', '純額(JPY)',
            'スプレッドID', 'レグ', 'ステータス', '備考'
        ])

        # データ行
        for trade in trades:
            writer.writerow([
                trade['trade_id'],
                trade['timestamp_jst'],
                trade['symbol'],
                trade['action'],
                trade['option_type'],
                trade['strike'],
                trade['expiry'],
                trade['quantity'],
                f"{trade['premium_per_contract']:.2f}",
                f"{trade['total_premium_usd']:.2f}",
                f"{trade['commission_usd']:.2f}",
                f"{trade['net_amount_usd']:.2f}",
                f"{trade['fx_rate_usd_jpy']:.2f}" if trade['fx_rate_usd_jpy'] else '',
                f"{trade['net_amount_jpy']:.0f}" if trade['net_amount_jpy'] else '',
                trade['spread_id'],
                trade['leg'],
                trade['position_status'],
                trade['notes']
            ])

        output.seek(0)

        # CSVレスポンスを返す
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=trades_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@router.get("/trades/tax-summary")
async def get_tax_summary(year: int = None):
    """
    税務サマリーを取得

    Args:
        year: 対象年（デフォルトは現在の年）

    Returns:
        dict: 税務サマリー
    """
    if year is None:
        year = datetime.now().year

    try:
        # モックデータを返す（実際の実装ではDBから集計）
        return {
            "year": year,
            "total_premium_received_usd": 1250.00,
            "total_premium_paid_usd": 200.00,
            "total_commission_usd": 50.00,
            "net_profit_usd": 1000.00,
            "net_profit_jpy": 155000,  # 155円換算
            "total_trades": 24,
            "win_count": 20,
            "loss_count": 4,
            "win_rate": 0.833
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tax summary: {str(e)}")


@router.get("/trades/export-tax-csv")
async def export_tax_csv(year: int = None):
    """
    税務申告用CSVをエクスポート

    Args:
        year: 対象年（デフォルトは現在の年）

    Returns:
        StreamingResponse: 税務申告用CSVファイル
    """
    if year is None:
        year = datetime.now().year

    try:
        summary = await get_tax_summary(year)

        # CSVデータを生成
        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー（国税庁様式に準拠）
        writer.writerow(['【雑所得】オプション取引損益計算書'])
        writer.writerow([f'対象年: {year}年'])
        writer.writerow([])

        # サマリー
        writer.writerow(['項目', '金額（USD）', '金額（JPY）'])
        writer.writerow(['総受取プレミアム', f"{summary['total_premium_received_usd']:.2f}", ''])
        writer.writerow(['総支払プレミアム', f"{summary['total_premium_paid_usd']:.2f}", ''])
        writer.writerow(['総手数料', f"{summary['total_commission_usd']:.2f}", ''])
        writer.writerow(['純利益（課税所得）', f"{summary['net_profit_usd']:.2f}", f"{summary['net_profit_jpy']:.0f}"])
        writer.writerow([])

        # 統計
        writer.writerow(['統計情報', ''])
        writer.writerow(['総取引数', summary['total_trades']])
        writer.writerow(['利益取引数', summary['win_count']])
        writer.writerow(['損失取引数', summary['loss_count']])
        writer.writerow(['勝率', f"{summary['win_rate']*100:.1f}%"])
        writer.writerow([])

        # 注記
        writer.writerow(['注記'])
        writer.writerow(['※ 為替レートは各取引時のTTSレートを使用'])
        writer.writerow(['※ 手数料は必要経費として計上可能'])
        writer.writerow(['※ 詳細は税理士にご相談ください'])

        output.seek(0)

        # CSVレスポンスを返す
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tax_report_{year}.csv"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export tax CSV: {str(e)}")


def _get_mock_trades():
    """モック取引データを生成"""
    now = datetime.now(pytz.UTC)
    jst = pytz.timezone('Asia/Tokyo')
    et = pytz.timezone('US/Eastern')

    trades = []

    # モックデータ: 最近の2つのスプレッド取引
    for i in range(2):
        spread_id = f"SPREAD_{(now - timedelta(days=i*7)).strftime('%Y%m%d_%H%M%S')}"
        entry_time = now - timedelta(days=i*7, hours=10)
        exit_time = now - timedelta(days=i*7-3, hours=14)

        # エントリー: Short Put
        trades.append({
            'trade_id': f"{spread_id}_SHORT",
            'timestamp_utc': entry_time.isoformat(),
            'timestamp_et': entry_time.astimezone(et).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timestamp_jst': entry_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S'),
            'trade_date_jst': entry_time.astimezone(jst).strftime('%Y-%m-%d'),
            'symbol': 'SPY',
            'action': 'SELL',
            'option_type': 'PUT',
            'strike': 580.0 - i*5,
            'expiry': (entry_time + timedelta(days=5)).strftime('%Y-%m-%d'),
            'quantity': 2,
            'premium_per_contract': 3.25,
            'total_premium_usd': 650.0,
            'commission_usd': 2.60,
            'net_amount_usd': 647.40,
            'fx_rate_usd_jpy': 155.0,
            'fx_rate_tts': 156.0,
            'net_amount_jpy': 100995,
            'spread_id': spread_id,
            'leg': 'short',
            'position_status': 'closed',
            'notes': 'Bull Put Credit Spread - Short Leg'
        })

        # エントリー: Long Put (保護)
        trades.append({
            'trade_id': f"{spread_id}_LONG",
            'timestamp_utc': entry_time.isoformat(),
            'timestamp_et': entry_time.astimezone(et).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timestamp_jst': entry_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S'),
            'trade_date_jst': entry_time.astimezone(jst).strftime('%Y-%m-%d'),
            'symbol': 'SPY',
            'action': 'BUY',
            'option_type': 'PUT',
            'strike': 575.0 - i*5,
            'expiry': (entry_time + timedelta(days=5)).strftime('%Y-%m-%d'),
            'quantity': 2,
            'premium_per_contract': 0.50,
            'total_premium_usd': 100.0,
            'commission_usd': 2.60,
            'net_amount_usd': -102.60,
            'fx_rate_usd_jpy': 155.0,
            'fx_rate_tts': 156.0,
            'net_amount_jpy': -16006,
            'spread_id': spread_id,
            'leg': 'long',
            'position_status': 'closed',
            'notes': 'Bull Put Credit Spread - Long Leg (保護)'
        })

        # エグジット: Buy to Close Short Put
        trades.append({
            'trade_id': f"{spread_id}_CLOSE_SHORT",
            'timestamp_utc': exit_time.isoformat(),
            'timestamp_et': exit_time.astimezone(et).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timestamp_jst': exit_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S'),
            'trade_date_jst': exit_time.astimezone(jst).strftime('%Y-%m-%d'),
            'symbol': 'SPY',
            'action': 'BUY',
            'option_type': 'PUT',
            'strike': 580.0 - i*5,
            'expiry': (entry_time + timedelta(days=5)).strftime('%Y-%m-%d'),
            'quantity': 2,
            'premium_per_contract': 0.50,
            'total_premium_usd': 100.0,
            'commission_usd': 2.60,
            'net_amount_usd': -102.60,
            'fx_rate_usd_jpy': 154.5,
            'fx_rate_tts': 155.5,
            'net_amount_jpy': -15954,
            'spread_id': spread_id,
            'leg': 'short',
            'position_status': 'closed',
            'notes': 'ポジションクローズ - 利益確定'
        })

        # エグジット: Sell to Close Long Put
        trades.append({
            'trade_id': f"{spread_id}_CLOSE_LONG",
            'timestamp_utc': exit_time.isoformat(),
            'timestamp_et': exit_time.astimezone(et).strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timestamp_jst': exit_time.astimezone(jst).strftime('%Y-%m-%d %H:%M:%S'),
            'trade_date_jst': exit_time.astimezone(jst).strftime('%Y-%m-%d'),
            'symbol': 'SPY',
            'action': 'SELL',
            'option_type': 'PUT',
            'strike': 575.0 - i*5,
            'expiry': (entry_time + timedelta(days=5)).strftime('%Y-%m-%d'),
            'quantity': 2,
            'premium_per_contract': 0.10,
            'total_premium_usd': 20.0,
            'commission_usd': 2.60,
            'net_amount_usd': 17.40,
            'fx_rate_usd_jpy': 154.5,
            'fx_rate_tts': 155.5,
            'net_amount_jpy': 2706,
            'spread_id': spread_id,
            'leg': 'long',
            'position_status': 'closed',
            'notes': 'ポジションクローズ'
        })

    return {
        'trades': trades,
        'total_count': len(trades)
    }
