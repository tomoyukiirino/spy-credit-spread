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
        # リアルモード: IBKRからオプションデータを取得
        from backend.services.ibkr_service import IBKRService
        from ib_insync import Stock, Option
        from datetime import datetime
        import math

        service = app_state.get('ibkr_service')
        if not service or not service.is_connected:
            raise HTTPException(status_code=503, detail="IBKR not connected")

        try:
            def _fetch_spread_candidates(ib):
                # 1. SPY現在価格を取得
                spy_contract = Stock('SPY', 'SMART', 'USD')
                ib.qualifyContracts(spy_contract)
                ib.reqMktData(spy_contract, '', False, False)
                ib.sleep(2)
                spy_ticker = ib.ticker(spy_contract)
                ib.cancelMktData(spy_contract)

                spy_price = spy_ticker.last
                if not spy_price or math.isnan(spy_price):
                    spy_price = spy_ticker.close
                if not spy_price or math.isnan(spy_price):
                    bid = spy_ticker.bid if spy_ticker.bid and not math.isnan(spy_ticker.bid) else 0
                    ask = spy_ticker.ask if spy_ticker.ask and not math.isnan(spy_ticker.ask) else 0
                    spy_price = (bid + ask) / 2 if bid and ask else 580

                # 2. オプションチェーンのパラメータを取得
                chains = ib.reqSecDefOptParams('SPY', '', 'STK', spy_contract.conId)
                if not chains:
                    return []

                # 最も多くの期限を持つチェーンを選択（近期オプションを含む）
                # ※ SMARTチェーンは近期オプションを含まないため、最大チェーンを使用
                chain = max(chains, key=lambda c: len(c.expirations))

                # 3. DTE範囲でフィルタリング
                today = datetime.now().date()
                valid_expirations = []
                for exp_str in sorted(chain.expirations):
                    exp_date = datetime.strptime(exp_str, '%Y%m%d').date()
                    dte = (exp_date - today).days
                    if config.MIN_DTE <= dte <= config.MAX_DTE:
                        valid_expirations.append((exp_str, exp_date, dte))

                if not valid_expirations:
                    return []

                # 4. ATM近辺のストライクに絞る（SPY価格の85%〜100%）
                target_strikes_all = sorted([
                    s for s in chain.strikes
                    if spy_price * 0.85 <= s < spy_price
                ])
                target_strikes = target_strikes_all[-15:] if len(target_strikes_all) > 15 else target_strikes_all

                candidates = []

                # 5. 各期限についてオプションデータを取得（最大2期限）
                for exp_str, exp_date, dte in valid_expirations[:2]:
                    # tradingClass='SPY'を指定してAmbiguous contractエラーを回避
                    option_contracts = [
                        Option('SPY', exp_str, strike, 'P', 'SMART', tradingClass='SPY')
                        for strike in target_strikes
                    ]

                    # 契約を検証
                    try:
                        ib.qualifyContracts(*option_contracts)
                        option_contracts = [c for c in option_contracts if c.conId]
                    except Exception as qe:
                        import logging
                        logging.getLogger(__name__).warning(f'qualifyContracts failed for {exp_str}: {qe}')
                        continue

                    if not option_contracts:
                        continue

                    # マーケットデータをリクエスト（Greeksを含む）
                    tickers_map = {}
                    for opt in option_contracts:
                        t = ib.reqMktData(opt, '100,101,105,106', False, False)
                        tickers_map[opt.strike] = (opt, t)

                    ib.sleep(5)  # データ到着を待つ

                    for strike, (opt, ticker) in tickers_map.items():
                        ib.cancelMktData(opt)

                        if not ticker:
                            continue

                        # デルタを取得（modelGreeks > bidGreeks > lastGreeks の順）
                        greeks = ticker.modelGreeks or ticker.bidGreeks or ticker.lastGreeks
                        delta = None
                        iv = None
                        if greeks:
                            if greeks.delta is not None and not math.isnan(greeks.delta):
                                delta = greeks.delta
                            if greeks.impliedVol is not None and not math.isnan(greeks.impliedVol):
                                iv = greeks.impliedVol

                        abs_delta = abs(delta) if delta is not None else None

                        # bid/ask/mid
                        bid = ticker.bid if ticker.bid and not math.isnan(ticker.bid) and ticker.bid > 0 else None
                        ask = ticker.ask if ticker.ask and not math.isnan(ticker.ask) and ticker.ask > 0 else None
                        mid = (bid + ask) / 2 if bid and ask else None

                        long_strike = strike - config.SPREAD_WIDTH
                        max_profit = mid * 100 if mid else None
                        max_loss = (config.SPREAD_WIDTH - mid) * 100 if (mid and mid < config.SPREAD_WIDTH) else None
                        win_prob = (1 - abs_delta) if abs_delta is not None else None
                        score = (win_prob * max_profit / max_loss) if (win_prob and max_profit and max_loss and max_loss > 0) else 0

                        candidates.append({
                            'short_strike': strike,
                            'long_strike': long_strike,
                            'expiry': exp_str,
                            'exp_date': exp_date.strftime('%Y-%m-%d'),
                            'dte': dte,
                            'short_delta': abs_delta,
                            'short_iv': iv,
                            'spread_premium_mid': mid,
                            'max_profit': max_profit,
                            'max_loss': max_loss,
                            'risk_reward_ratio': max_loss / max_profit if (max_profit and max_loss) else None,
                            'win_probability': win_prob,
                            'score': score,
                        })

                candidates.sort(key=lambda x: x['score'], reverse=True)
                return candidates

            # タイムアウトを60秒に延長（複数期限のデータ取得に時間がかかるため）
            candidates = await service.execute_timeout(60, _fetch_spread_candidates, service.ib)

            return {
                "candidates_count": len(candidates),
                "candidates": candidates
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get spread candidates: {str(e)}")


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
