"""
オプションAPIルーター
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

router = APIRouter()


@router.get("/options/chain")
async def get_options_chain(
    symbol: str = Query(default="SPY", description="シンボル"),
    dte_min: int = Query(default=1, description="最小DTE"),
    dte_max: int = Query(default=7, description="最大DTE")
):
    """
    オプションチェーンを取得

    Args:
        symbol: シンボル
        dte_min: 最小DTE
        dte_max: 最大DTE

    Returns:
        list: オプションデータ
    """
    from main import app_state

    if config.USE_MOCK_DATA:
        # モックモード
        market_data = app_state.get('market_data_manager')
        if not market_data:
            raise HTTPException(status_code=503, detail="Market data manager not available")

        try:
            from services.options_service import OptionsService

            options_service = OptionsService(market_data)
            options_data = options_service.get_options_chain(
                symbol=symbol,
                dte_min=dte_min,
                dte_max=dte_max
            )

            return {
                "symbol": symbol,
                "dte_range": [dte_min, dte_max],
                "options_count": len(options_data),
                "options": options_data
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get options chain: {str(e)}")

    else:
        # リアルモード: IBKRServiceを使用
        from backend.services.ibkr_service import IBKRService
        from ib_insync import Stock
        from datetime import datetime, timedelta

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            # SPY契約を作成
            contract = Stock(symbol, 'SMART', 'USD')

            # 契約を検証
            await service.run(service.ib.qualifyContracts, contract)

            # オプションパラメータを取得
            chains = await service.run(service.ib.reqSecDefOptParams,
                                      contract.symbol, '', contract.secType, contract.conId)

            if not chains:
                raise HTTPException(status_code=404, detail="No option chains found")

            # 最初のチェーンを使用
            chain = chains[0]

            # 満期日フィルタリング
            today = datetime.now().date()
            filtered_expirations = []
            for exp_str in sorted(chain.expirations):
                exp_date = datetime.strptime(exp_str, '%Y%m%d').date()
                dte = (exp_date - today).days

                if dte_min <= dte <= dte_max:
                    filtered_expirations.append(exp_str)

            # 簡易的なオプションデータを返す（詳細取得は別途実装）
            return {
                "symbol": symbol,
                "dte_range": [dte_min, dte_max],
                "expirations": filtered_expirations,
                "strikes_count": len(chain.strikes),
                "note": "Real mode - detailed option data requires additional implementation"
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get options chain: {str(e)}")


@router.get("/options/spreads")
async def get_spread_candidates():
    """
    スプレッド候補を取得

    Returns:
        list: スプレッド候補のリスト
    """
    from main import app_state

    if config.USE_MOCK_DATA:
        # モックモード
        market_data = app_state.get('market_data_manager')
        if not market_data:
            raise HTTPException(status_code=503, detail="Market data manager not available")

        try:
            from services.options_service import OptionsService

            options_service = OptionsService(market_data)
            candidates = options_service.get_spread_candidates()

            return {
                "candidates_count": len(candidates),
                "candidates": candidates
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get spread candidates: {str(e)}")

    else:
        # リアルモード: 簡易実装（後で詳細実装）
        return {
            "candidates_count": 0,
            "candidates": [],
            "note": "Real mode spread calculation requires additional implementation"
        }


@router.post("/options/calculate-spread")
async def calculate_spread_metrics(
    short_strike: float,
    long_strike: float,
    short_premium: float,
    long_premium: float
):
    """
    スプレッド指標を計算

    Args:
        short_strike: ショートストライク
        long_strike: ロングストライク
        short_premium: ショートプレミアム
        long_premium: ロングプレミアム

    Returns:
        dict: スプレッド指標
    """
    try:
        spread_width = short_strike - long_strike
        net_premium = short_premium - long_premium
        max_loss = spread_width - net_premium
        max_profit = net_premium
        breakeven = short_strike - net_premium
        risk_reward_ratio = max_loss / max_profit if max_profit > 0 else 0
        pop = (max_profit / spread_width) * 100 if spread_width > 0 else 0

        return {
            "spread_width": spread_width,
            "net_premium": net_premium,
            "max_loss": max_loss,
            "max_profit": max_profit,
            "breakeven": breakeven,
            "risk_reward_ratio": risk_reward_ratio,
            "probability_of_profit": pop
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate spread: {str(e)}")
