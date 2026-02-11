"""
ポジションサービス: ポジション管理とP&L計算
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Dict, Optional


class PositionService:
    """ポジション管理サービス"""

    def __init__(self, position_manager):
        """
        初期化

        Args:
            position_manager: PositionManager インスタンス
        """
        self.position_manager = position_manager

    def get_all_positions(self) -> List[Dict]:
        """
        全ポジションを取得

        Returns:
            list: ポジションのリスト
        """
        return list(self.position_manager.positions.values())

    def get_open_positions(self) -> List[Dict]:
        """
        オープンポジションを取得

        Returns:
            list: オープンポジションのリスト
        """
        return self.position_manager.get_open_positions()

    def get_position_by_id(self, spread_id: str) -> Optional[Dict]:
        """
        IDでポジションを取得

        Args:
            spread_id: スプレッドID

        Returns:
            dict: ポジション情報
        """
        return self.position_manager.positions.get(spread_id)

    def get_position_summary(self) -> Dict:
        """
        ポジションサマリーを取得

        Returns:
            dict: サマリー情報
        """
        return self.position_manager.get_position_summary()

    def close_position(
        self,
        spread_id: str,
        exit_premium: float,
        fx_rate: Optional[float] = None
    ) -> bool:
        """
        ポジションをクローズ

        Args:
            spread_id: スプレッドID
            exit_premium: 決済プレミアム
            fx_rate: 為替レート

        Returns:
            bool: 成功ならTrue
        """
        try:
            self.position_manager.close_position(
                spread_id=spread_id,
                exit_premium=exit_premium,
                fx_rate_usd_jpy=fx_rate
            )
            return True
        except Exception as e:
            print(f"Error closing position: {e}")
            return False

    def calculate_unrealized_pnl(
        self,
        spread_id: str,
        current_premium: float
    ) -> Optional[float]:
        """
        未実現損益を計算

        Args:
            spread_id: スプレッドID
            current_premium: 現在のプレミアム

        Returns:
            float: 未実現損益（USD）
        """
        position = self.get_position_by_id(spread_id)
        if not position or position['status'] != 'open':
            return None

        entry_premium = position['entry_premium']
        quantity = position['quantity']

        # クレジットスプレッドなので、プレミアムが減少すれば利益
        unrealized_pnl = (entry_premium - current_premium) * 100 * quantity

        return unrealized_pnl
