"""
マーケットデータAPIルーター
"""

from fastapi import APIRouter, HTTPException
from models.schemas import SpyPrice
from datetime import datetime
import pytz
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config

router = APIRouter()


@router.get("/market/spy", response_model=SpyPrice)
async def get_spy_price():
    """
    SPY現在価格を取得

    Returns:
        SpyPrice: SPY価格情報
    """
    from main import app_state

    if config.USE_MOCK_DATA:
        # モックモード: MarketDataManagerを使用
        market_data = app_state.get('market_data_manager')
        if not market_data:
            raise HTTPException(status_code=503, detail="Market data manager not available")

        try:
            price_data = market_data.get_spy_price()

            if not price_data:
                raise HTTPException(status_code=500, detail="Failed to get SPY price")

            return SpyPrice(
                last=price_data.get('last'),
                bid=price_data.get('bid'),
                ask=price_data.get('ask'),
                mid=price_data.get('mid'),
                timestamp=datetime.now(pytz.UTC),
                is_delayed=True
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get SPY price: {str(e)}")

    else:
        # リアルモード: IBKRServiceを使用（新パターン）
        from backend.services.ibkr_service import IBKRService
        from ib_insync import Stock

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            # 一連の処理を1つの関数にまとめて execute() に渡す
            def _fetch_spy_price(ib):
                contract = Stock('SPY', 'SMART', 'USD')
                ib.qualifyContracts(contract)
                ib.reqMktData(contract, '', False, False)
                ib.sleep(2)  # データ到着を待つ
                ticker = ib.ticker(contract)
                ib.cancelMktData(contract)

                # データ整形
                last = ticker.last if ticker.last == ticker.last else None  # NaNチェック
                bid = ticker.bid if ticker.bid == ticker.bid else None
                ask = ticker.ask if ticker.ask == ticker.ask else None

                if not last and bid and ask:
                    last = (bid + ask) / 2

                mid = (bid + ask) / 2 if (bid and ask) else last

                return {
                    'last': last or 0,
                    'bid': bid or last or 0,
                    'ask': ask or last or 0,
                    'mid': mid or last or 0,
                }

            data = await service.execute(_fetch_spy_price, service.ib)

            return SpyPrice(
                last=data['last'],
                bid=data['bid'],
                ask=data['ask'],
                mid=data['mid'],
                timestamp=datetime.now(pytz.UTC),
                is_delayed=(config.MARKET_DATA_TYPE == 3 or config.MARKET_DATA_TYPE == 4)
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get SPY price: {str(e)}")


@router.get("/market/vix")
async def get_vix_level():
    """
    VIX水準を取得

    Returns:
        dict: VIX情報
    """
    from main import app_state

    if config.USE_MOCK_DATA:
        # モックモードではダミーデータ
        return {
            "vix": 18.5,
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "is_mock": True
        }

    else:
        # リアルモード: VIX取得（インデックスとして）
        from backend.services.ibkr_service import IBKRService
        from ib_insync import Index

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            def _fetch_vix(ib):
                contract = Index('VIX', 'CBOE')
                ib.qualifyContracts(contract)
                ib.reqMktData(contract, '', False, False)
                ib.sleep(2)
                ticker = ib.ticker(contract)
                ib.cancelMktData(contract)

                last = ticker.last if ticker.last == ticker.last else None
                close = ticker.close if ticker.close == ticker.close else None
                bid = ticker.bid if ticker.bid == ticker.bid else None
                ask = ticker.ask if ticker.ask == ticker.ask else None

                return {
                    'vix': last or close,
                    'bid': bid,
                    'ask': ask,
                }

            data = await service.execute(_fetch_vix, service.ib)

            return {
                "vix": data['vix'],
                "bid": data['bid'],
                "ask": data['ask'],
                "timestamp": datetime.now(pytz.UTC).isoformat(),
                "is_delayed": (config.MARKET_DATA_TYPE == 3 or config.MARKET_DATA_TYPE == 4)
            }

        except Exception as e:
            # VIX取得失敗時はモックデータを返す
            return {
                "vix": 18.5,
                "error": str(e),
                "timestamp": datetime.now(pytz.UTC).isoformat(),
                "is_fallback": True
            }
