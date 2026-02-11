"""
リスク管理・監視モジュール: ポートフォリオリスクの監視とアラート
"""

from typing import Dict, List, Optional
import config
from logger import get_logger


class RiskMonitor:
    """リスク管理クラス"""

    def __init__(self, position_manager):
        """
        Args:
            position_manager: PositionManagerインスタンス
        """
        self.position_manager = position_manager
        self.logger = get_logger()

    def check_portfolio_risk(
        self,
        account_summary: Dict[str, Dict[str, str]]
    ) -> Dict:
        """
        ポートフォリオ全体のリスクをチェック

        Args:
            account_summary: 口座サマリー

        Returns:
            リスク評価結果
        """
        net_liq = float(account_summary.get('NetLiquidation', {}).get('value', '0'))
        position_summary = self.position_manager.get_position_summary()

        total_risk = position_summary['total_open_risk']
        risk_percentage = (total_risk / net_liq * 100) if net_liq > 0 else 0

        # リスク上限（口座の30%まで）
        max_portfolio_risk = net_liq * 0.30

        risk_check = {
            'net_liquidation': net_liq,
            'total_open_risk': total_risk,
            'risk_percentage': risk_percentage,
            'max_portfolio_risk': max_portfolio_risk,
            'risk_ok': total_risk <= max_portfolio_risk,
            'available_risk': max_portfolio_risk - total_risk
        }

        # ログ出力
        self.logger.info('=== ポートフォリオリスクチェック ===')
        self.logger.info(f'口座残高: ${net_liq:,.2f}')
        self.logger.info(f'オープンポジション総リスク: ${total_risk:,.2f} ({risk_percentage:.1f}%)')
        self.logger.info(f'リスク上限: ${max_portfolio_risk:,.2f} (30%)')
        self.logger.info(f'利用可能リスク: ${risk_check["available_risk"]:,.2f}')

        if not risk_check['risk_ok']:
            self.logger.warning('⚠ ポートフォリオリスクが上限を超えています！')

        return risk_check

    def can_open_new_position(
        self,
        new_position_risk: float,
        account_summary: Dict[str, Dict[str, str]]
    ) -> bool:
        """
        新規ポジションを開くことができるかチェック

        Args:
            new_position_risk: 新規ポジションの最大リスク
            account_summary: 口座サマリー

        Returns:
            開けるかどうか
        """
        risk_check = self.check_portfolio_risk(account_summary)

        if new_position_risk > risk_check['available_risk']:
            self.logger.warning(
                f'⚠ 新規ポジションリスク ${new_position_risk:.2f} が '
                f'利用可能リスク ${risk_check["available_risk"]:.2f} を超えています'
            )
            return False

        self.logger.info(f'✓ 新規ポジション開設可能（リスク: ${new_position_risk:.2f}）')
        return True

    def check_position_alert(
        self,
        spread_id: str,
        current_loss: float,
        loss_threshold: float = 0.50
    ) -> bool:
        """
        個別ポジションのアラートチェック

        Args:
            spread_id: スプレッドID
            current_loss: 現在の損失額（USD）
            loss_threshold: 損失閾値（最大損失の割合、デフォルト50%）

        Returns:
            アラートが必要かどうか
        """
        position = self.position_manager.get_position(spread_id)
        if not position:
            return False

        max_loss = position['max_loss']
        loss_limit = max_loss * loss_threshold

        if current_loss >= loss_limit:
            self.logger.warning(
                f'⚠ アラート: {spread_id} の損失が閾値に到達'
            )
            self.logger.warning(
                f'  現在損失: ${current_loss:.2f} / 閾値: ${loss_limit:.2f} '
                f'({loss_threshold*100:.0f}%)'
            )
            return True

        return False

    def suggest_action(
        self,
        spread_id: str,
        current_premium: float,
        dte: int
    ) -> str:
        """
        ポジションに対する推奨アクションを提案

        Args:
            spread_id: スプレッドID
            current_premium: 現在のプレミアム
            dte: 満期までの日数

        Returns:
            推奨アクション（'hold', 'close', 'monitor'）
        """
        position = self.position_manager.get_position(spread_id)
        if not position or position['status'] != 'open':
            return 'none'

        entry_premium = position['entry_premium']
        unrealized_pnl = self.position_manager.calculate_unrealized_pnl(
            spread_id,
            current_premium
        )

        # ルール1: 利益が50%以上出ている → クローズ推奨
        if unrealized_pnl and unrealized_pnl >= position['max_profit'] * 0.50:
            self.logger.info(
                f'推奨: {spread_id} をクローズ（利益50%達成）'
            )
            return 'close'

        # ルール2: 損失が60%以上 → クローズ推奨（損切り）
        if unrealized_pnl and unrealized_pnl <= -position['max_loss'] * 0.60:
            self.logger.warning(
                f'推奨: {spread_id} をクローズ（損切り）'
            )
            return 'close'

        # ルール3: DTEが0日（満期当日） → ホールド（満期を待つ）
        if dte == 0:
            return 'hold'

        # ルール4: DTEが1日で利益が出ている → クローズ検討
        if dte == 1 and unrealized_pnl and unrealized_pnl > 0:
            self.logger.info(
                f'推奨: {spread_id} のクローズを検討（DTE 1日、利益確保）'
            )
            return 'close'

        # デフォルト: 監視継続
        return 'monitor'
