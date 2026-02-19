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
    現在の戦略ステータスを取得（スケジューラー状態を含む）

    Returns:
        StrategyStatus: 自動発注の現在の状態
    """
    try:
        from backend.services.auto_trader import get_auto_trader_status
        from backend.services.strategy_service import get_adjusted_delta
        from main import app_state, scheduler
        import config

        auto_state = get_auto_trader_status()

        # VIX取得（利用可能な場合）
        current_vix = None
        adjusted_delta = None
        position_size_factor = 1.0

        if not config.USE_MOCK_DATA:
            service = app_state.get('ibkr_service')
            if service and service.is_connected:
                # ストリーミングデータからVIXを取得（実装されていれば）
                # 現時点では None のまま（VIXはオンデマンド取得）
                pass

        if current_vix:
            adjusted_delta, position_size_factor = get_adjusted_delta(current_vix)

        # 次回実行時刻（APSchedulerから取得）
        next_run_time = auto_state.get('next_run_time')
        if scheduler.running:
            job = scheduler.get_job('auto_entry')
            if job and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()

        # 次回エントリー日時をパース
        next_entry_date = None
        next_entry_time = None
        if next_run_time:
            try:
                import pytz
                dt = datetime.fromisoformat(next_run_time)
                next_entry_date = dt.strftime('%Y-%m-%d')
                next_entry_time = dt.strftime('%H:%M')
            except Exception:
                pass

        # オープンポジション数
        open_positions_count = 0
        position_manager = app_state.get('position_manager')
        if position_manager:
            try:
                positions = position_manager.get_open_positions()
                open_positions_count = len(positions)
            except Exception:
                pass

        status = StrategyStatus(
            is_active=auto_state.get('is_active', False),
            next_entry_date=next_entry_date,
            next_entry_time=next_entry_time,
            current_vix=current_vix,
            adjusted_delta=adjusted_delta,
            position_size_factor=position_size_factor,
            fear_greed_score=None,
            fear_greed_rating=None,
            open_positions_count=open_positions_count,
            skip_reason=auto_state.get('last_error')
        )

        return status

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ステータス取得失敗: {str(e)}"
        )


@router.post("/strategy/execute-now")
async def execute_entry_now():
    """
    手動で今すぐエントリーを実行（テスト・緊急用）

    Returns:
        dict: 実行結果
    """
    from main import app_state
    import config

    if config.USE_MOCK_DATA:
        raise HTTPException(status_code=400, detail="モックモードでは手動実行できません")

    service = app_state.get('ibkr_service')
    if not service or not service.is_connected:
        raise HTTPException(status_code=503, detail="IBKR未接続")

    try:
        from backend.services.auto_trader import run_auto_entry
        result = await run_auto_entry(service)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実行失敗: {str(e)}")


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
