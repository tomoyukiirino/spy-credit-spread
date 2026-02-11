"""
為替レートAPIルーター
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()


class ManualFxRateRequest(BaseModel):
    """手動為替レート設定リクエスト"""
    usd_jpy: float
    tts_rate: Optional[float] = None


@router.get("/fx/rate")
async def get_fx_rate():
    """
    現在のUSD/JPY為替レートを取得

    Returns:
        dict: 為替レート情報
    """
    from main import app_state

    try:
        # FXRateManagerを取得（存在しない場合もある）
        fx_manager = app_state.get('fx_rate_manager')

        from services.fx_service import FxService

        fx_service = FxService(fx_manager)
        rate_data = fx_service.get_current_rate()

        return rate_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get FX rate: {str(e)}")


@router.post("/fx/rate/manual")
async def set_manual_fx_rate(request: ManualFxRateRequest):
    """
    手動で為替レートを設定

    Args:
        request: 為替レート設定リクエスト

    Returns:
        dict: 設定されたレート情報
    """
    try:
        from services.fx_service import FxService

        fx_service = FxService(None)  # 手動設定なのでfx_managerは不要
        rate_data = fx_service.set_manual_rate(
            usd_jpy=request.usd_jpy,
            tts_rate=request.tts_rate
        )

        return {
            "message": "FX rate set successfully",
            "rate": rate_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set manual FX rate: {str(e)}")


@router.get("/fx/rate/tts")
async def calculate_tts_rate(spot_rate: float, margin: float = 1.0):
    """
    スポットレートからTTSレートを計算

    Args:
        spot_rate: スポットレート
        margin: マージン（円、デフォルト1円）

    Returns:
        dict: TTSレート
    """
    try:
        from services.fx_service import FxService

        fx_service = FxService(None)
        tts_rate = fx_service.calculate_tts_rate(spot_rate, margin)

        return {
            "spot_rate": spot_rate,
            "margin": margin,
            "tts_rate": tts_rate
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate TTS rate: {str(e)}")
