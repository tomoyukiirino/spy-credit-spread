"""
為替レートサービス: USD/JPYレート取得
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, Optional
from datetime import datetime
import pytz


class FxService:
    """為替レート管理サービス"""

    def __init__(self, fx_rate_manager=None):
        """
        初期化

        Args:
            fx_rate_manager: FXRateManager または MockFXRateManager
        """
        self.fx_rate_manager = fx_rate_manager

    def get_current_rate(self) -> Dict:
        """
        現在のUSD/JPYレートを取得

        Returns:
            dict: {
                'usd_jpy': float,
                'source': str,
                'timestamp': str,
                'tts_rate': float | None
            }
        """
        if self.fx_rate_manager is None:
            # フォールバック: 固定レート
            return {
                'usd_jpy': 150.0,
                'source': 'fallback',
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'tts_rate': None
            }

        rate_data = self.fx_rate_manager.get_usd_jpy_rate()

        if rate_data:
            return {
                'usd_jpy': rate_data['usd_jpy'],
                'source': rate_data.get('source', 'unknown'),
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'tts_rate': rate_data.get('tts_rate')
            }

        # フォールバック
        return {
            'usd_jpy': 150.0,
            'source': 'fallback',
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'tts_rate': None
        }

    def set_manual_rate(self, usd_jpy: float, tts_rate: Optional[float] = None) -> Dict:
        """
        手動で為替レートを設定

        Args:
            usd_jpy: USD/JPYレート
            tts_rate: TTSレート（オプション）

        Returns:
            dict: 設定されたレート情報
        """
        # 将来実装: ログファイルに保存
        return {
            'usd_jpy': usd_jpy,
            'source': 'manual',
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'tts_rate': tts_rate
        }

    def calculate_tts_rate(self, spot_rate: float, margin: float = 1.0) -> float:
        """
        スポットレートからTTSレートを計算

        Args:
            spot_rate: スポットレート
            margin: マージン（円、デフォルト1円）

        Returns:
            float: TTSレート
        """
        return spot_rate + margin
