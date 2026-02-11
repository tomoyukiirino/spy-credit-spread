"""
戦略モジュール: Bull Put Spreadの選択ロジック
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import pandas as pd
import config
from logger import get_logger


class SpreadStrategy:
    """Bull Put Credit Spread戦略の実装"""

    def __init__(self, market_data_manager):
        """
        Args:
            market_data_manager: MarketDataManagerまたはMockMarketDataManager
        """
        self.market_data = market_data_manager
        self.logger = get_logger()

    def select_best_spread(
        self,
        spy_price: float,
        account_summary: Dict[str, Dict[str, str]]
    ) -> Optional[Dict]:
        """
        最適なBull Put Spreadを選択

        Args:
            spy_price: SPYの現在価格
            account_summary: 口座サマリー情報

        Returns:
            選択されたスプレッド情報、見つからない場合はNone
        """
        self.logger.info('=== スプレッド選択開始 ===')

        # 1. オプションチェーン取得
        expirations = self.market_data.get_option_chain_params()
        if not expirations:
            self.logger.error('満期日の取得に失敗')
            return None

        # 2. 各満期日のスプレッド候補を評価
        all_candidates = []
        for expiration in expirations:
            exp_date = datetime.strptime(expiration, '%Y%m%d').date()
            dte = (exp_date - datetime.now().date()).days

            self.logger.info(f'満期日 {exp_date} (DTE: {dte}日) を評価中...')

            # Putオプション取得
            options_df = self.market_data.get_put_options_with_greeks(
                expiration,
                spy_price
            )

            if options_df.empty:
                self.logger.warning(f'満期日 {exp_date} のオプションデータなし')
                continue

            # 目標デルタに最も近い売りプットを見つける
            short_put = self.market_data.find_target_delta_strike(options_df)
            if not short_put:
                self.logger.warning(f'満期日 {exp_date} で目標デルタのオプションなし')
                continue

            # スプレッドペアを見つける
            spread_info = self.market_data.find_spread_pair(short_put, options_df)
            if not spread_info:
                self.logger.warning(f'満期日 {exp_date} でスプレッドペアなし')
                continue

            # 追加情報を付与
            spread_info['expiration'] = expiration
            spread_info['exp_date'] = exp_date
            spread_info['dte'] = dte

            all_candidates.append(spread_info)

        if not all_candidates:
            self.logger.error('スプレッド候補が見つかりませんでした')
            return None

        # 3. 最適なスプレッドを選択（リスク/リワード比が良いもの）
        best_spread = self._select_best_from_candidates(
            all_candidates,
            account_summary
        )

        if best_spread:
            self.logger.info(f'✓ 最適スプレッド選択: {best_spread["exp_date"]} (DTE: {best_spread["dte"]}日)')
            self.logger.info(f'  売り: ${best_spread["short_strike"]:.2f} (Δ: {best_spread["short_delta"]:.3f})')
            self.logger.info(f'  買い: ${best_spread["long_strike"]:.2f}')
            self.logger.info(f'  最大利益: ${best_spread["max_profit"]:.2f}')
            self.logger.info(f'  最大損失: ${best_spread["max_loss"]:.2f}')
            self.logger.info(f'  R/R比: {best_spread["risk_reward_ratio"]:.2f}')

        return best_spread

    def _select_best_from_candidates(
        self,
        candidates: List[Dict],
        account_summary: Dict[str, Dict[str, str]]
    ) -> Optional[Dict]:
        """
        候補の中から最適なスプレッドを選択

        Args:
            candidates: スプレッド候補リスト
            account_summary: 口座サマリー

        Returns:
            最適なスプレッド
        """
        # 口座残高からリスク上限を計算
        net_liq = float(account_summary.get('NetLiquidation', {}).get('value', '0'))
        max_risk_per_trade = net_liq * config.RISK_PER_TRADE

        self.logger.info(f'口座残高: ${net_liq:.2f}')
        self.logger.info(f'1取引あたり最大リスク: ${max_risk_per_trade:.2f} ({config.RISK_PER_TRADE*100:.0f}%)')

        # リスク上限を超えるものを除外
        valid_candidates = [
            c for c in candidates
            if c['max_loss'] <= max_risk_per_trade
        ]

        if not valid_candidates:
            self.logger.warning('⚠ すべての候補がリスク上限を超えています')
            self.logger.warning('最もリスクの低い候補を選択します')
            # リスクが最も低いものを選択
            valid_candidates = sorted(candidates, key=lambda x: x['max_loss'])[:1]

        # 複数の基準でスコアリング
        for candidate in valid_candidates:
            score = self._calculate_spread_score(candidate)
            candidate['score'] = score

        # スコアが最も高いものを選択
        best = max(valid_candidates, key=lambda x: x['score'])

        self.logger.info(f'候補数: {len(candidates)} → フィルタ後: {len(valid_candidates)}')

        return best

    def _calculate_spread_score(self, spread: Dict) -> float:
        """
        スプレッドのスコアを計算（高いほど良い）

        評価基準:
        - デルタが目標に近いほど高スコア
        - プレミアムが高いほど高スコア
        - DTEが短すぎず長すぎないほど高スコア
        - リスク/リワード比が低いほど高スコア

        Args:
            spread: スプレッド情報

        Returns:
            スコア（0-100）
        """
        score = 0.0

        # 1. デルタスコア（40点満点）
        # TARGET_DELTAに近いほど高スコア
        delta_diff = abs(spread['short_delta'] - config.TARGET_DELTA)
        delta_score = max(0, 40 - delta_diff * 200)
        score += delta_score

        # 2. プレミアムスコア（30点満点）
        # ネットプレミアムが高いほど高スコア（$0.20 - $2.00の範囲を想定）
        premium = spread['net_premium']
        premium_score = min(30, premium / 2.0 * 30)
        score += premium_score

        # 3. DTEスコア（20点満点）
        # 2-5日が最適、それ以外は減点
        dte = spread['dte']
        if 2 <= dte <= 5:
            dte_score = 20
        elif dte == 1:
            dte_score = 15
        elif dte == 6:
            dte_score = 15
        elif dte == 7:
            dte_score = 10
        else:
            dte_score = 5
        score += dte_score

        # 4. リスク/リワード比スコア（10点満点）
        # 比率が低いほど高スコア（10以下が理想）
        rr_ratio = spread['risk_reward_ratio']
        if rr_ratio <= 10:
            rr_score = 10
        elif rr_ratio <= 15:
            rr_score = 7
        elif rr_ratio <= 20:
            rr_score = 4
        else:
            rr_score = 1
        score += rr_score

        self.logger.debug(
            f'スコア詳細: {spread["exp_date"]} - '
            f'Total: {score:.1f} '
            f'(Δ: {delta_score:.1f}, Prem: {premium_score:.1f}, '
            f'DTE: {dte_score:.1f}, R/R: {rr_score:.1f})'
        )

        return score

    def calculate_position_size(
        self,
        spread: Dict,
        account_summary: Dict[str, Dict[str, str]]
    ) -> int:
        """
        ポジションサイズ（契約数）を計算

        Args:
            spread: スプレッド情報
            account_summary: 口座サマリー

        Returns:
            契約数（1以上）
        """
        net_liq = float(account_summary.get('NetLiquidation', {}).get('value', '0'))
        max_risk_per_trade = net_liq * config.RISK_PER_TRADE

        # 1契約あたりの最大損失
        max_loss_per_contract = spread['max_loss']

        # 契約数を計算
        if max_loss_per_contract > 0:
            quantity = int(max_risk_per_trade / max_loss_per_contract)
        else:
            quantity = 1

        # 最低1契約
        quantity = max(1, quantity)

        self.logger.info(f'ポジションサイズ計算:')
        self.logger.info(f'  最大リスク: ${max_risk_per_trade:.2f}')
        self.logger.info(f'  1契約損失: ${max_loss_per_contract:.2f}')
        self.logger.info(f'  契約数: {quantity}')

        return quantity

    def validate_spread(self, spread: Dict) -> Tuple[bool, str]:
        """
        スプレッドが取引基準を満たしているか検証

        Args:
            spread: スプレッド情報

        Returns:
            (検証OK, エラーメッセージ)
        """
        # 1. デルタ範囲チェック
        if not (config.DELTA_RANGE[0] <= spread['short_delta'] <= config.DELTA_RANGE[1]):
            return False, f'デルタ {spread["short_delta"]:.3f} が範囲外 {config.DELTA_RANGE}'

        # 2. プレミアムチェック（最低$0.10）
        if spread['net_premium'] < 0.10:
            return False, f'ネットプレミアム ${spread["net_premium"]:.2f} が低すぎます'

        # 3. リスク/リワード比チェック（最大25倍まで）
        if spread['risk_reward_ratio'] > 25:
            return False, f'R/R比 {spread["risk_reward_ratio"]:.2f} が高すぎます'

        # 4. スプレッド幅チェック
        actual_width = spread['short_strike'] - spread['long_strike']
        if abs(actual_width - config.SPREAD_WIDTH) > 0.01:
            return False, f'スプレッド幅 ${actual_width:.2f} が設定値 ${config.SPREAD_WIDTH} と異なります'

        return True, 'OK'
