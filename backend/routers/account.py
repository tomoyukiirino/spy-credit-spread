"""
口座情報APIルーター
"""

from fastapi import APIRouter, HTTPException, Depends
from models.schemas import AccountInfo
import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

router = APIRouter()


@router.get("/account", response_model=AccountInfo)
async def get_account_info():
    """
    口座情報を取得

    Returns:
        AccountInfo: 口座サマリー
    """
    from main import app_state

    if config.USE_MOCK_DATA:
        # モックモード: 従来のパターン
        conn = app_state.get('ibkr_connection')
        if not conn or not conn.is_connected():
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            summary = conn.get_account_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get account info: {str(e)}")

    else:
        # リアルモード: 新しいIBKRServiceパターン
        from backend.services.ibkr_service import IBKRService

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            # accountSummary()を専用スレッドで実行
            summary_list = await service.run(service.ib.accountSummary)

            # リスト形式の結果を辞書に変換
            summary = {}
            for item in summary_list:
                summary[item.tag] = {
                    'value': item.value,
                    'currency': item.currency
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get account info: {str(e)}")

    return AccountInfo(
        net_liquidation=float(summary.get('NetLiquidation', {}).get('value', '0')),
        total_cash=float(summary.get('TotalCashValue', {}).get('value', '0')),
        buying_power=float(summary.get('BuyingPower', {}).get('value', '0')),
        currency=summary.get('NetLiquidation', {}).get('currency', 'USD')
    )


@router.get("/account/summary")
async def get_account_summary():
    """
    口座サマリー + 戦略パラメータを取得

    Returns:
        dict: 詳細なサマリー
    """
    from main import app_state

    position_manager = app_state.get('position_manager')

    if config.USE_MOCK_DATA:
        # モックモード
        conn = app_state.get('ibkr_connection')
        if not conn or not conn.is_connected():
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            account_summary = conn.get_account_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get account summary: {str(e)}")

    else:
        # リアルモード
        from backend.services.ibkr_service import IBKRService

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            summary_list = await service.run(service.ib.accountSummary)

            # リスト形式を辞書に変換
            account_summary = {}
            for item in summary_list:
                account_summary[item.tag] = {
                    'value': item.value,
                    'currency': item.currency
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get account summary: {str(e)}")

    position_summary = position_manager.get_position_summary() if position_manager else {}

    net_liq = float(account_summary.get('NetLiquidation', {}).get('value', '0'))
    max_risk_per_trade = net_liq * config.RISK_PER_TRADE
    max_portfolio_risk = net_liq * 0.30

    return {
        "account": {
            "net_liquidation": net_liq,
            "total_cash": float(account_summary.get('TotalCashValue', {}).get('value', '0')),
            "buying_power": float(account_summary.get('BuyingPower', {}).get('value', '0')),
        },
        "strategy_params": {
            "symbol": config.SYMBOL,
            "spread_width": config.SPREAD_WIDTH,
            "target_delta": config.TARGET_DELTA,
            "delta_range": config.DELTA_RANGE,
            "risk_per_trade": config.RISK_PER_TRADE,
            "min_dte": config.MIN_DTE,
            "max_dte": config.MAX_DTE
        },
        "risk_limits": {
            "max_risk_per_trade": max_risk_per_trade,
            "max_portfolio_risk": max_portfolio_risk,
            "current_portfolio_risk": position_summary.get('total_open_risk', 0),
            "available_risk": max_portfolio_risk - position_summary.get('total_open_risk', 0)
        },
        "positions": position_summary
    }
