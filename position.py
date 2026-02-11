"""
ポジション管理モジュール: スプレッドポジションの追跡と管理
"""

from typing import Dict, List, Optional
from datetime import datetime
import pytz
import json
import os
import config
from logger import get_logger


class PositionManager:
    """ポジション管理クラス"""

    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self.positions_file = 'logs/positions.json'
        self.positions = self._load_positions()

    def _load_positions(self) -> Dict:
        """
        保存されたポジションを読み込む

        Returns:
            ポジション辞書 {spread_id: position_data}
        """
        if os.path.exists(self.positions_file):
            try:
                with open(self.positions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f'ポジション読み込みエラー: {str(e)}')
                return {}
        return {}

    def _save_positions(self):
        """ポジションをファイルに保存"""
        try:
            os.makedirs(os.path.dirname(self.positions_file), exist_ok=True)
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(self.positions, f, indent=2, ensure_ascii=False, default=str)
            self.logger.debug(f'ポジションを保存: {len(self.positions)}件')
        except Exception as e:
            self.logger.error(f'ポジション保存エラー: {str(e)}')

    def add_position(
        self,
        spread_id: str,
        spread: Dict,
        quantity: int,
        entry_premium: float,
        fx_rate: Optional[float] = None
    ):
        """
        新しいポジションを追加

        Args:
            spread_id: スプレッドID
            spread: スプレッド情報
            quantity: 契約数
            entry_premium: エントリー時のネットプレミアム
            fx_rate: USD/JPYレート
        """
        timestamp_utc = datetime.now(pytz.UTC)
        timestamp_et = timestamp_utc.astimezone(pytz.timezone('US/Eastern'))
        timestamp_jst = timestamp_utc.astimezone(pytz.timezone('Asia/Tokyo'))

        position = {
            'spread_id': spread_id,
            'symbol': config.SYMBOL,
            'short_strike': spread['short_strike'],
            'long_strike': spread['long_strike'],
            'expiration': spread['expiration'],
            'exp_date': str(spread['exp_date']),
            'dte_at_entry': spread['dte'],
            'quantity': quantity,
            'entry_premium': entry_premium,
            'max_profit': spread['max_profit'] * quantity,
            'max_loss': spread['max_loss'] * quantity,
            'opened_at_utc': timestamp_utc.isoformat(),
            'opened_at_et': timestamp_et.isoformat(),
            'opened_at_jst': timestamp_jst.isoformat(),
            'status': 'open',
            'fx_rate_usd_jpy': fx_rate,
            'closed_at': None,
            'exit_premium': None,
            'realized_pnl_usd': None,
            'realized_pnl_jpy': None
        }

        self.positions[spread_id] = position
        self._save_positions()

        self.logger.info(f'✓ ポジション追加: {spread_id}')
        self.logger.info(f'  {quantity}x ${spread["short_strike"]}/{spread["long_strike"]} Put Spread')

    def get_open_positions(self) -> List[Dict]:
        """
        オープンポジションのリストを取得

        Returns:
            オープンポジションのリスト
        """
        return [
            pos for pos in self.positions.values()
            if pos['status'] == 'open'
        ]

    def get_position(self, spread_id: str) -> Optional[Dict]:
        """
        特定のポジションを取得

        Args:
            spread_id: スプレッドID

        Returns:
            ポジション情報、存在しない場合はNone
        """
        return self.positions.get(spread_id)

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
            exit_premium: エグジット時のネットプレミアム
            fx_rate: USD/JPYレート

        Returns:
            成功フラグ
        """
        if spread_id not in self.positions:
            self.logger.error(f'ポジションが見つかりません: {spread_id}')
            return False

        position = self.positions[spread_id]

        if position['status'] != 'open':
            self.logger.warning(f'ポジションはすでにクローズ済み: {spread_id}')
            return False

        timestamp_utc = datetime.now(pytz.UTC)

        # 実現損益を計算
        # Bull Put Spread: エントリー時にクレジット受取、エグジット時にデビット支払い
        # 利益 = エントリープレミアム - エグジットプレミアム
        entry_total = position['entry_premium'] * position['quantity'] * 100  # USD
        exit_total = exit_premium * position['quantity'] * 100  # USD
        realized_pnl_usd = entry_total - exit_total

        # 円建て損益
        realized_pnl_jpy = None
        if fx_rate:
            realized_pnl_jpy = realized_pnl_usd * fx_rate

        # ポジション情報を更新
        position['closed_at'] = timestamp_utc.isoformat()
        position['exit_premium'] = exit_premium
        position['realized_pnl_usd'] = realized_pnl_usd
        position['realized_pnl_jpy'] = realized_pnl_jpy
        position['status'] = 'closed'

        self._save_positions()

        self.logger.info(f'✓ ポジションクローズ: {spread_id}')
        self.logger.info(f'  実現損益: ${realized_pnl_usd:.2f} USD')
        if realized_pnl_jpy:
            self.logger.info(f'  実現損益: ¥{realized_pnl_jpy:,.0f} JPY')

        return True

    def mark_expired(self, spread_id: str) -> bool:
        """
        ポジションを期限切れとしてマーク

        Args:
            spread_id: スプレッドID

        Returns:
            成功フラグ
        """
        if spread_id not in self.positions:
            self.logger.error(f'ポジションが見つかりません: {spread_id}')
            return False

        position = self.positions[spread_id]

        if position['status'] != 'open':
            return False

        # 期限切れ時は最大利益を得る（OTMで満期）
        position['status'] = 'expired'
        position['closed_at'] = datetime.now(pytz.UTC).isoformat()
        position['exit_premium'] = 0  # 満期時はプレミアム0
        position['realized_pnl_usd'] = position['max_profit']

        self._save_positions()

        self.logger.info(f'✓ ポジション満期: {spread_id}')
        self.logger.info(f'  最大利益達成: ${position["max_profit"]:.2f}')

        return True

    def calculate_unrealized_pnl(
        self,
        spread_id: str,
        current_premium: float
    ) -> Optional[float]:
        """
        未実現損益を計算

        Args:
            spread_id: スプレッドID
            current_premium: 現在のネットプレミアム

        Returns:
            未実現損益（USD）
        """
        position = self.get_position(spread_id)
        if not position or position['status'] != 'open':
            return None

        # 未実現損益 = (エントリープレミアム - 現在プレミアム) × 契約数 × 100
        unrealized_pnl = (position['entry_premium'] - current_premium) * position['quantity'] * 100

        return unrealized_pnl

    def get_position_summary(self) -> Dict:
        """
        ポジションサマリーを取得

        Returns:
            サマリー情報
        """
        open_positions = self.get_open_positions()
        closed_positions = [p for p in self.positions.values() if p['status'] in ['closed', 'expired']]

        total_open_risk = sum(p['max_loss'] for p in open_positions)
        total_open_potential_profit = sum(p['max_profit'] for p in open_positions)

        total_realized_pnl = sum(
            p.get('realized_pnl_usd', 0) for p in closed_positions
            if p.get('realized_pnl_usd') is not None
        )

        return {
            'total_positions': len(self.positions),
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'total_open_risk': total_open_risk,
            'total_open_potential_profit': total_open_potential_profit,
            'total_realized_pnl_usd': total_realized_pnl
        }

    def print_summary(self):
        """ポジションサマリーを表示"""
        summary = self.get_position_summary()

        self.logger.info('=== ポジションサマリー ===')
        self.logger.info(f'全ポジション数: {summary["total_positions"]}')
        self.logger.info(f'オープン: {summary["open_positions"]}')
        self.logger.info(f'クローズ済み: {summary["closed_positions"]}')
        self.logger.info(f'オープンポジション最大リスク: ${summary["total_open_risk"]:.2f}')
        self.logger.info(f'オープンポジション潜在利益: ${summary["total_open_potential_profit"]:.2f}')
        self.logger.info(f'累積実現損益: ${summary["total_realized_pnl_usd"]:.2f}')
