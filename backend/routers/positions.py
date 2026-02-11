"""
ポジションAPIルーター
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()


class ClosePositionRequest(BaseModel):
    """ポジションクローズリクエスト"""
    exit_premium: float
    fx_rate: Optional[float] = None


@router.get("/positions")
async def get_positions(status: Optional[str] = None):
    """
    ポジション一覧を取得

    Args:
        status: フィルター（open/closed/expired）

    Returns:
        list: ポジションのリスト
    """
    from main import app_state

    position_manager = app_state.get('position_manager')
    if not position_manager:
        raise HTTPException(status_code=503, detail="Position manager not available")

    try:
        from services.position_service import PositionService

        position_service = PositionService(position_manager)

        if status == 'open':
            positions = position_service.get_open_positions()
        else:
            positions = position_service.get_all_positions()
            if status:
                positions = [p for p in positions if p['status'] == status]

        return {
            "positions_count": len(positions),
            "positions": positions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@router.get("/positions/{spread_id}")
async def get_position_by_id(spread_id: str):
    """
    特定のポジションを取得

    Args:
        spread_id: スプレッドID

    Returns:
        dict: ポジション情報
    """
    from main import app_state

    position_manager = app_state.get('position_manager')
    if not position_manager:
        raise HTTPException(status_code=503, detail="Position manager not available")

    try:
        from services.position_service import PositionService

        position_service = PositionService(position_manager)
        position = position_service.get_position_by_id(spread_id)

        if not position:
            raise HTTPException(status_code=404, detail=f"Position {spread_id} not found")

        return position

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get position: {str(e)}")


@router.post("/positions/{spread_id}/close")
async def close_position(spread_id: str, request: ClosePositionRequest):
    """
    ポジションをクローズ

    Args:
        spread_id: スプレッドID
        request: クローズリクエスト

    Returns:
        dict: 結果
    """
    from main import app_state

    position_manager = app_state.get('position_manager')
    if not position_manager:
        raise HTTPException(status_code=503, detail="Position manager not available")

    try:
        from services.position_service import PositionService

        position_service = PositionService(position_manager)

        # ポジションが存在するか確認
        position = position_service.get_position_by_id(spread_id)
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {spread_id} not found")

        if position['status'] != 'open':
            raise HTTPException(status_code=400, detail=f"Position {spread_id} is not open")

        # ポジションをクローズ
        success = position_service.close_position(
            spread_id=spread_id,
            exit_premium=request.exit_premium,
            fx_rate=request.fx_rate
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to close position")

        # 更新されたポジションを取得
        updated_position = position_service.get_position_by_id(spread_id)

        return {
            "message": "Position closed successfully",
            "position": updated_position
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")


@router.get("/positions/{spread_id}/unrealized-pnl")
async def get_unrealized_pnl(spread_id: str, current_premium: float):
    """
    未実現損益を計算

    Args:
        spread_id: スプレッドID
        current_premium: 現在のプレミアム

    Returns:
        dict: 未実現損益
    """
    from main import app_state

    position_manager = app_state.get('position_manager')
    if not position_manager:
        raise HTTPException(status_code=503, detail="Position manager not available")

    try:
        from services.position_service import PositionService

        position_service = PositionService(position_manager)
        pnl = position_service.calculate_unrealized_pnl(spread_id, current_premium)

        if pnl is None:
            raise HTTPException(status_code=404, detail=f"Position {spread_id} not found or not open")

        return {
            "spread_id": spread_id,
            "unrealized_pnl_usd": pnl,
            "current_premium": current_premium
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate unrealized P&L: {str(e)}")
