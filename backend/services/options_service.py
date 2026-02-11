"""
オプションサービス: オプションチェーン取得とスプレッド計算
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import config
from typing import List, Dict, Optional
from datetime import datetime


class OptionsService:
    """オプション関連サービス"""

    def __init__(self, market_data_manager):
        """
        初期化

        Args:
            market_data_manager: MarketDataManager または MockMarketDataManager
        """
        self.market_data_manager = market_data_manager

    def get_options_chain(
        self,
        symbol: str = 'SPY',
        dte_min: int = None,
        dte_max: int = None
    ) -> List[Dict]:
        """
        オプションチェーンを取得

        Args:
            symbol: シンボル（デフォルト: SPY）
            dte_min: 最小DTE
            dte_max: 最大DTE

        Returns:
            list: オプションデータのリスト
        """
        if dte_min is None:
            dte_min = config.MIN_DTE
        if dte_max is None:
            dte_max = config.MAX_DTE

        # オプションチェーンを取得（新しいメソッドを使用）
        options_data = self.market_data_manager.get_options_by_dte_range(
            dte_min=dte_min,
            dte_max=dte_max
        )

        return options_data

    def get_spread_candidates(self) -> List[Dict]:
        """
        スプレッド候補を取得

        Returns:
            list: スプレッド候補のリスト
        """
        # オプションデータを取得
        options_data = self.get_options_chain()

        if not options_data:
            return []

        # 満期日でグループ化
        options_by_expiry = {}
        for option in options_data:
            expiry = option['expiry']
            if expiry not in options_by_expiry:
                options_by_expiry[expiry] = []
            options_by_expiry[expiry].append(option)

        candidates = []

        # 各満期日でスプレッドを生成
        for expiry, options in options_by_expiry.items():
            # デルタでソート
            sorted_options = sorted(options, key=lambda x: x.get('delta', 0) or 0)

            # 目標デルタに近いオプションを探す
            for option in sorted_options:
                delta = option.get('delta', 0)
                if not delta or delta < config.DELTA_RANGE[0] or delta > config.DELTA_RANGE[1]:
                    continue

                # ロングストライク（売りストライク - スプレッド幅）を探す
                short_strike = option['strike']
                long_strike = short_strike - config.SPREAD_WIDTH

                # ロングプットを見つける
                long_option = next((o for o in options if o['strike'] == long_strike), None)
                if not long_option:
                    continue

                # スプレッド指標を計算
                spread_premium = option['mid'] - long_option['mid']
                max_profit = spread_premium * 100
                max_loss = (config.SPREAD_WIDTH - spread_premium) * 100
                risk_reward_ratio = abs(max_loss / max_profit) if max_profit > 0 else 999
                win_probability = 1 - abs(delta)

                # スコア計算
                delta_score = 40 if abs(delta - config.TARGET_DELTA) < 0.05 else 20
                premium_score = min(30, (spread_premium / 2.0) * 30)
                dte_score = 20 if 2 <= option['dte'] <= 5 else 10
                rr_score = 10 if risk_reward_ratio <= 4 else 5
                score = delta_score + premium_score + dte_score + rr_score

                candidates.append({
                    'short_strike': short_strike,
                    'long_strike': long_strike,
                    'expiry': expiry,
                    'exp_date': option['exp_date'],
                    'dte': option['dte'],
                    'short_delta': delta,
                    'short_iv': option.get('iv'),
                    'spread_premium_mid': spread_premium,
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'risk_reward_ratio': risk_reward_ratio,
                    'win_probability': win_probability,
                    'score': score
                })

        # スコアでソート
        candidates.sort(key=lambda x: x.get('score', 0), reverse=True)

        return candidates

    def calculate_spread_metrics(
        self,
        short_strike: float,
        long_strike: float,
        short_premium: float,
        long_premium: float
    ) -> Dict:
        """
        スプレッドの指標を計算

        Args:
            short_strike: ショートストライク
            long_strike: ロングストライク
            short_premium: ショートプレミアム
            long_premium: ロングプレミアム

        Returns:
            dict: 計算結果
        """
        spread_premium = short_premium - long_premium
        max_profit = spread_premium * 100  # 1契約あたり
        max_loss = (short_strike - long_strike - spread_premium) * 100

        risk_reward_ratio = abs(max_loss / max_profit) if max_profit > 0 else 999

        return {
            'spread_premium': spread_premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'risk_reward_ratio': risk_reward_ratio
        }
