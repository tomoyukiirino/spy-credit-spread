"""
戦略サービス: エントリー判断ロジック

VIX連動デルタ調整、イベントカレンダー回避、Fear & Greed Index取得
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import requests
import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from backend.services import market_service as market_svc


def get_adjusted_delta(vix: float) -> Tuple[Optional[float], float]:
    """
    VIX水準に応じたデルタとポジションサイズ係数を返す

    Args:
        vix: 現在のVIX値

    Returns:
        (adjusted_delta, position_size_factor)
        - adjusted_delta: 調整後のデルタ（Noneの場合はエントリー見送り）
        - position_size_factor: 1.0（通常） or 0.5（リスク削減）
    """
    if vix < 15:
        # 低ボラ: デルタ大きめ、通常サイズ
        return 0.25, 1.0
    elif vix < 25:
        # 通常: デフォルト
        return 0.20, 1.0
    elif vix < 35:
        # 高ボラ: 安全重視、サイズ半減
        return 0.15, 0.5
    else:
        # 超高ボラ: エントリー見送り
        return None, 0.0


def get_fear_greed_index() -> Optional[dict]:
    """
    CNN Fear & Greed Indexを取得

    取得失敗時はモック値を返す（開発用）
    本番環境では別のデータソース使用を推奨

    Returns:
        {'score': 45, 'rating': 'Fear', 'timestamp': '...'} or mock data
    """
    try:
        response = requests.get(
            config.FEAR_GREED_API_URL,
            timeout=config.FEAR_GREED_TIMEOUT,
            headers={'User-Agent': 'Mozilla/5.0'}  # User-Agentを追加
        )

        if response.status_code == 200:
            data = response.json()

            # APIレスポンスの構造に合わせて解析
            if 'fear_and_greed' in data:
                current = data['fear_and_greed']
                return {
                    'score': int(current.get('score', 50)),
                    'rating': current.get('rating', 'Neutral'),
                    'timestamp': current.get('timestamp', datetime.now().isoformat())
                }

        # API取得失敗時はモック値を返す（開発用）
        print(f"Fear & Greed Index API利用不可（status={response.status_code}）、モック値を使用")
        return {
            'score': 50,
            'rating': 'Neutral',
            'timestamp': datetime.now().isoformat(),
            'is_mock': True
        }

    except Exception as e:
        print(f"Fear & Greed Index取得エラー: {str(e)}、モック値を使用")
        return {
            'score': 50,
            'rating': 'Neutral',
            'timestamp': datetime.now().isoformat(),
            'is_mock': True
        }


def select_entry_date(
    target_day: str = 'monday',
    avoid_events: bool = True
) -> Tuple[datetime, str]:
    """
    エントリー日を自動選択

    基本ルール: 月曜エントリー → 金曜満期（DTE 4）
    イベント回避ルール:
      - 金曜にイベント（雇用統計/CPI等）→ 水曜満期
      - 水曜にFOMC → 金曜満期
      - イベント日に満期が重なる → 別の満期日 or 見送り

    Args:
        target_day: エントリー曜日（'monday', 'tuesday', etc.）
        avoid_events: イベント回避するかどうか

    Returns:
        (entry_date, selected_expiry_str)
    """
    today = datetime.now().date()

    # 次の月曜日を取得
    days_ahead = 0 - today.weekday()  # 0=月曜
    if days_ahead <= 0:
        days_ahead += 7

    entry_date = today + timedelta(days=days_ahead)

    # デフォルト: 金曜満期（DTE 4）
    expiry_date = entry_date + timedelta(days=4)

    if avoid_events:
        # イベント日チェック
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        is_event, event_name = config.is_event_day(expiry_str)

        if is_event:
            # 金曜にイベント → 水曜満期に変更
            print(f"⚠️ {expiry_str}（金）に{event_name} → 水曜満期に変更")
            expiry_date = entry_date + timedelta(days=2)

    expiry_str = expiry_date.strftime('%Y%m%d')

    return entry_date, expiry_str


def check_event_warnings(
    expiry_date: str,
    check_range_days: int = 2
) -> list[str]:
    """
    満期日の前後にイベントがあるか警告

    Args:
        expiry_date: 満期日（YYYYMMDD）
        check_range_days: チェック範囲（前後N日）

    Returns:
        警告メッセージのリスト
    """
    warnings = []

    try:
        expiry_dt = datetime.strptime(expiry_date, '%Y%m%d').date()

        # 前後N日をチェック
        for offset in range(-check_range_days, check_range_days + 1):
            check_date = expiry_dt + timedelta(days=offset)
            check_str = check_date.strftime('%Y-%m-%d')

            is_event, event_name = config.is_event_day(check_str)

            if is_event:
                if offset == 0:
                    warnings.append(f"⚠️ 満期日当日に{event_name}")
                elif offset > 0:
                    warnings.append(f"⚠️ 満期{offset}日後に{event_name}（{check_str}）")
                else:
                    warnings.append(f"⚠️ 満期{-offset}日前に{event_name}（{check_str}）")

    except Exception as e:
        print(f"イベント警告チェックエラー: {str(e)}")

    return warnings


def evaluate_entry(
    ibkr_connection,
    market_data_manager,
    options_service
) -> dict:
    """
    エントリー判断を実行

    Args:
        ibkr_connection: IBKRConnection または MockIBKRConnection
        market_data_manager: MarketDataManager または MockMarketDataManager
        options_service: オプションサービスインスタンス（未実装の場合None）

    Returns:
        EntryPreviewに相当する辞書
    """
    result = {
        'recommended': False,
        'skip_reason': None,
        'vix': 0.0,
        'adjusted_delta': 0.0,
        'fear_greed': None,
        'selected_expiry': '',
        'spread': None,
        'max_loss': None,
        'within_risk_limit': False,
        'event_warnings': []
    }

    try:
        # 1. VIX取得
        try:
            if hasattr(market_data_manager, 'get_vix_level'):
                vix_data = market_data_manager.get_vix_level()
                vix = vix_data.get('vix', 18.5)
            else:
                # フォールバック: デフォルト値
                vix = 18.5
        except Exception as e:
            print(f"VIX取得エラー: {e}、デフォルト値を使用")
            vix = 18.5

        result['vix'] = vix

        # 2. VIX連動デルタ調整
        adjusted_delta, position_size_factor = get_adjusted_delta(vix)

        if adjusted_delta is None:
            result['skip_reason'] = 'VIX_TOO_HIGH'
            result['vix'] = vix
            return result

        result['adjusted_delta'] = adjusted_delta

        # 3. Fear & Greed Index取得（オプション）
        fear_greed = get_fear_greed_index()
        result['fear_greed'] = fear_greed

        # 4. 満期日自動選択
        entry_date, selected_expiry = select_entry_date()
        result['selected_expiry'] = selected_expiry

        # 5. イベント警告チェック
        event_warnings = check_event_warnings(selected_expiry)
        result['event_warnings'] = event_warnings

        # 6. スプレッド候補取得（options_serviceを使用）
        if options_service:
            try:
                spread_candidates = options_service.get_spread_candidates(
                    target_delta=adjusted_delta,
                    expiry=selected_expiry
                )
                if spread_candidates:
                    # 最適なスプレッドを選択（最初の候補）
                    best_spread = spread_candidates[0]
                    result['spread'] = best_spread
                    result['max_loss'] = best_spread.get('max_loss')
            except Exception as e:
                print(f"スプレッド候補取得エラー: {e}")

        # 7. リスク限度チェック
        if ibkr_connection and hasattr(ibkr_connection, 'get_account_summary'):
            try:
                account_summary = ibkr_connection.get_account_summary()
                max_risk_per_trade = float(account_summary.get('NetLiquidation', 10000)) * config.RISK_PER_TRADE

                if result.get('max_loss'):
                    current_risk = abs(result['max_loss'])
                    result['within_risk_limit'] = current_risk <= max_risk_per_trade
                else:
                    # スプレッド情報がない場合は保守的にFalse
                    result['within_risk_limit'] = False
            except Exception as e:
                print(f"リスク計算エラー: {e}")

        result['recommended'] = True

    except Exception as e:
        print(f"エントリー評価エラー: {str(e)}")
        result['skip_reason'] = 'ERROR'

    return result
