"""
戦略APIルーター
エントリー判断、自動発注制御
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.models.schemas import EntryPreview, StrategyStatus
from backend.services.strategy_service import evaluate_entry

router = APIRouter()


@router.get("/strategy/next-entry", response_model=EntryPreview)
async def get_next_entry_preview():
    """
    次回エントリーのプレビュー（発注はしない）

    VIX、Fear & Greed、イベントカレンダーをチェックして
    推奨エントリーを表示

    Returns:
        EntryPreview: エントリー推奨情報
    """
    try:
        # app_stateから必要なサービスインスタンスを取得
        from main import app_state
        import config

        if config.USE_MOCK_DATA:
            # モックモード
            conn = app_state.get('ibkr_connection')
            market_data_manager = app_state.get('market_data_manager')

            if not conn:
                raise HTTPException(
                    status_code=503,
                    detail="IBKR接続が確立されていません"
                )

            # エントリー評価を実行
            result = evaluate_entry(conn, market_data_manager, None)

        else:
            # リアルモード
            service = app_state.get('ibkr_service')

            if not service or not service.is_connected:
                raise HTTPException(
                    status_code=503,
                    detail="IBKR接続が確立されていません"
                )

            # エントリー評価を実行（リアルモードでは直接IBKRServiceを渡す）
            result = evaluate_entry(service, None, None)

        return EntryPreview(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"エントリー評価失敗: {str(e)}"
        )


@router.get("/strategy/status", response_model=StrategyStatus)
async def get_strategy_status():
    """
    現在の戦略ステータスを取得

    Returns:
        StrategyStatus: 自動発注の現在の状態
    """
    try:
        # TODO: 実際のステータスを取得
        # 現在は仮のステータスを返す

        status = StrategyStatus(
            is_active=False,
            next_entry_date=None,
            next_entry_time=None,
            current_vix=None,
            adjusted_delta=None,
            position_size_factor=1.0,
            fear_greed_score=None,
            fear_greed_rating=None,
            open_positions_count=0,
            skip_reason=None
        )

        return status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ステータス取得失敗: {str(e)}"
        )


@router.get("/strategy/event-calendar")
async def get_event_calendar():
    """
    イベントカレンダー一覧を取得

    Returns:
        dict: イベントカレンダー
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import config

    return {
        'events': config.ECONOMIC_EVENTS,
        'year': 2026
    }
