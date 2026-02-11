"""
マーケットデータサービス: SPY価格とVIX取得
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Optional


class MarketService:
    """マーケットデータ管理サービス"""

    def __init__(self, market_data_manager):
        """
        初期化

        Args:
            market_data_manager: MarketDataManager または MockMarketDataManager
        """
        self.market_data_manager = market_data_manager

    def get_spy_price(self) -> Optional[Dict]:
        """
        SPY現在価格を取得

        Returns:
            dict: {'last': float, 'bid': float, 'ask': float, 'mid': float}
        """
        return self.market_data_manager.get_spy_price()

    def get_vix_level(self) -> Optional[float]:
        """
        VIX水準を取得（将来実装）

        Returns:
            float: VIX値
        """
        # 将来実装
        return None
