"""
マーケットデータ取得モジュール: SPY価格、オプションチェーン、Greeksを取得
"""

from ib_insync import IB, Stock, Option, Contract
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from tabulate import tabulate
import config
from logger import get_logger


class MarketDataManager:
    """マーケットデータとオプションチェーンを管理するクラス"""

    def __init__(self, ib: IB):
        """
        Args:
            ib: 接続済みのIBインスタンス
        """
        self.ib = ib
        self.logger = get_logger()

    def get_spy_price(self) -> Optional[Dict[str, float]]:
        """
        SPYの現在価格を取得

        Returns:
            {'last': 最終価格, 'bid': Bid, 'ask': Ask, 'mid': 中間値}
            取得できない場合はNone
        """
        try:
            # SPY株式コントラクトを作成
            spy = Stock(config.SYMBOL, config.EXCHANGE, config.CURRENCY)

            # コントラクトを検証
            qualified = self.ib.qualifyContracts(spy)
            if not qualified:
                self.logger.error('SPYコントラクトの検証に失敗')
                return None

            spy = qualified[0]

            # マーケットデータをリクエスト（スナップショット）
            ticker = self.ib.reqMktData(spy, '', False, False)

            # データが返ってくるまで待機
            self.ib.sleep(2)

            # 価格データを取得
            last = ticker.last if ticker.last and ticker.last > 0 else ticker.close
            bid = ticker.bid if ticker.bid and ticker.bid > 0 else last
            ask = ticker.ask if ticker.ask and ticker.ask > 0 else last
            mid = (bid + ask) / 2

            # マーケットデータのサブスクリプションを解除
            self.ib.cancelMktData(spy)

            price_data = {
                'last': last,
                'bid': bid,
                'ask': ask,
                'mid': mid
            }

            self.logger.info(f'SPY価格: Last=${last:.2f}, Bid=${bid:.2f}, Ask=${ask:.2f}')

            return price_data

        except Exception as e:
            self.logger.error(f'SPY価格の取得に失敗: {str(e)}')
            return None

    def get_option_chain_params(self) -> List[str]:
        """
        SPYのオプションチェーンパラメータ（満期日リスト）を取得

        Returns:
            満期日のリスト（YYYYMMDD形式の文字列）
        """
        try:
            # SPY株式コントラクトを作成
            spy = Stock(config.SYMBOL, config.EXCHANGE, config.CURRENCY)

            # オプションパラメータを取得
            chains = self.ib.reqSecDefOptParams(
                spy.symbol,
                '',
                spy.secType,
                spy.conId
            )

            if not chains:
                self.logger.error('オプションチェーンパラメータの取得に失敗')
                return []

            # SPY用のチェーンを取得（通常は最初の要素）
            chain = chains[0]
            expirations = sorted(chain.expirations)

            # DTE範囲でフィルタリング
            today = datetime.now().date()
            filtered_expirations = []

            for exp_str in expirations:
                exp_date = datetime.strptime(exp_str, '%Y%m%d').date()
                dte = (exp_date - today).days

                if config.MIN_DTE <= dte <= config.MAX_DTE:
                    filtered_expirations.append(exp_str)

            self.logger.info(f'満期日候補（DTE {config.MIN_DTE}-{config.MAX_DTE}日）: {len(filtered_expirations)}件')
            for exp in filtered_expirations:
                exp_date = datetime.strptime(exp, '%Y%m%d').date()
                dte = (exp_date - today).days
                self.logger.info(f'  {exp} ({exp_date.strftime("%Y-%m-%d")}) - DTE: {dte}日')

            return filtered_expirations

        except Exception as e:
            self.logger.error(f'オプションチェーンパラメータの取得に失敗: {str(e)}')
            return []

    def get_put_options_with_greeks(
        self,
        expiration: str,
        spy_price: float
    ) -> pd.DataFrame:
        """
        指定満期日のPutオプションとGreeksを取得

        Args:
            expiration: 満期日（YYYYMMDD形式）
            spy_price: SPYの現在価格

        Returns:
            オプション情報のDataFrame
        """
        try:
            # 行使価格の範囲を計算（SPY価格の-3%〜-15%）
            strike_min = spy_price * 0.85  # -15%
            strike_max = spy_price * 0.97  # -3%

            self.logger.info(f'行使価格範囲: ${strike_min:.2f} - ${strike_max:.2f}')

            # オプションコントラクトのリストを作成
            # ib_insyncでは、全ストライクを一度に取得するのではなく、
            # 範囲を指定して段階的に取得する必要がある

            # まず、$5刻みでストライクのリストを生成
            strikes = []
            strike = int(strike_min / 5) * 5  # 5の倍数に切り下げ
            while strike <= strike_max:
                strikes.append(float(strike))
                strike += 5

            self.logger.info(f'チェック対象ストライク: {len(strikes)}件')

            # オプションデータを格納するリスト
            options_data = []

            # ストライクごとにオプションを取得（制限回避のため少しずつ処理）
            for i, strike in enumerate(strikes):
                try:
                    # Putオプションコントラクトを作成
                    option = Option(
                        config.SYMBOL,
                        expiration,
                        strike,
                        'P',  # Put
                        config.EXCHANGE
                    )

                    # コントラクトを検証
                    qualified = self.ib.qualifyContracts(option)
                    if not qualified:
                        continue

                    option = qualified[0]

                    # マーケットデータとGreeksをリクエスト
                    ticker = self.ib.reqMktData(option, '', False, False)

                    # Greeksが返ってくるまで待機（少し長めに）
                    self.ib.sleep(1.5)

                    # データを取得
                    greeks = ticker.modelGreeks or ticker.lastGreeks
                    if greeks and greeks.delta is not None:
                        bid = ticker.bid if ticker.bid and ticker.bid > 0 else 0
                        ask = ticker.ask if ticker.ask and ticker.ask > 0 else 0
                        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0

                        options_data.append({
                            'strike': strike,
                            'delta': abs(greeks.delta),  # Putのデルタは負なので絶対値
                            'iv': greeks.impliedVol * 100 if greeks.impliedVol else 0,  # %表示
                            'bid': bid,
                            'ask': ask,
                            'mid': mid,
                            'contract': option
                        })

                    # マーケットデータのサブスクリプションを解除
                    self.ib.cancelMktData(option)

                    # 5件ごとに少し待機（レート制限対策）
                    if (i + 1) % 5 == 0:
                        self.ib.sleep(1)

                except Exception as e:
                    self.logger.debug(f'ストライク ${strike} の取得エラー: {str(e)}')
                    continue

            if not options_data:
                self.logger.warning('Putオプションデータを取得できませんでした')
                return pd.DataFrame()

            # DataFrameに変換してデルタでソート
            df = pd.DataFrame(options_data)
            df = df.sort_values('delta')

            self.logger.info(f'Putオプション取得完了: {len(df)}件')

            return df

        except Exception as e:
            self.logger.error(f'Putオプションの取得に失敗: {str(e)}')
            return pd.DataFrame()

    def find_target_delta_strike(self, options_df: pd.DataFrame) -> Optional[Dict]:
        """
        目標デルタに最も近い行使価格を見つける

        Args:
            options_df: オプションデータのDataFrame

        Returns:
            選択されたオプション情報の辞書
        """
        if options_df.empty:
            return None

        # 目標デルタ（0.20）に最も近いものを探す
        options_df['delta_diff'] = abs(options_df['delta'] - config.TARGET_DELTA)
        closest = options_df.loc[options_df['delta_diff'].idxmin()]

        # デルタ範囲チェック
        if not (config.DELTA_RANGE[0] <= closest['delta'] <= config.DELTA_RANGE[1]):
            self.logger.warning(
                f'選択されたデルタ {closest["delta"]:.3f} が '
                f'許容範囲 {config.DELTA_RANGE} 外です'
            )

        return {
            'strike': closest['strike'],
            'delta': closest['delta'],
            'iv': closest['iv'],
            'bid': closest['bid'],
            'ask': closest['ask'],
            'mid': closest['mid'],
            'contract': closest['contract']
        }

    def find_spread_pair(
        self,
        short_put: Dict,
        options_df: pd.DataFrame
    ) -> Optional[Dict]:
        """
        Bull Put Spreadのペア（買いプット）を見つける

        Args:
            short_put: 売りプットの情報
            options_df: オプションデータのDataFrame

        Returns:
            スプレッドペアの情報
        """
        # 買いプットの行使価格（売りプット - スプレッド幅）
        long_strike = short_put['strike'] - config.SPREAD_WIDTH

        # 該当する買いプットを探す
        long_put_row = options_df[options_df['strike'] == long_strike]

        if long_put_row.empty:
            self.logger.warning(f'買いプット（ストライク ${long_strike}）が見つかりません')
            return None

        long_put = long_put_row.iloc[0]

        # スプレッド情報を計算
        # Bull Put Spread: 売りプットのプレミアム - 買いプットのプレミアム
        net_premium = short_put['mid'] - long_put['mid']
        max_profit = net_premium * 100  # 1契約あたり（オプションは100株単位）
        max_loss = (config.SPREAD_WIDTH - net_premium) * 100
        risk_reward_ratio = max_loss / max_profit if max_profit > 0 else 0

        spread_info = {
            'short_strike': short_put['strike'],
            'short_delta': short_put['delta'],
            'short_iv': short_put['iv'],
            'short_premium': short_put['mid'],
            'long_strike': long_strike,
            'long_delta': long_put['delta'],
            'long_iv': long_put['iv'],
            'long_premium': long_put['mid'],
            'net_premium': net_premium,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'risk_reward_ratio': risk_reward_ratio
        }

        return spread_info

    def display_options_table(self, options_df: pd.DataFrame, title: str = 'オプション一覧'):
        """
        オプションデータをテーブル形式で表示

        Args:
            options_df: オプションデータのDataFrame
            title: テーブルのタイトル
        """
        if options_df.empty:
            self.logger.info(f'{title}: データなし')
            return

        # 表示用にデータを整形
        display_df = options_df[['strike', 'delta', 'iv', 'bid', 'ask', 'mid']].copy()
        display_df.columns = ['ストライク', 'デルタ', 'IV(%)', 'Bid', 'Ask', 'Mid']

        # フォーマット
        display_df['ストライク'] = display_df['ストライク'].apply(lambda x: f'${x:.2f}')
        display_df['デルタ'] = display_df['デルタ'].apply(lambda x: f'{x:.3f}')
        display_df['IV(%)'] = display_df['IV(%)'].apply(lambda x: f'{x:.1f}%')
        display_df['Bid'] = display_df['Bid'].apply(lambda x: f'${x:.2f}')
        display_df['Ask'] = display_df['Ask'].apply(lambda x: f'${x:.2f}')
        display_df['Mid'] = display_df['Mid'].apply(lambda x: f'${x:.2f}')

        self.logger.info(f'\n{title}')
        self.logger.info('\n' + tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))

    def display_spread_info(self, spread: Dict):
        """
        スプレッド情報を表示

        Args:
            spread: スプレッド情報の辞書
        """
        self.logger.info('\n=== Bull Put Spread 候補 ===')
        self.logger.info(f'売りプット: ${spread["short_strike"]:.2f} (デルタ: {spread["short_delta"]:.3f}, IV: {spread["short_iv"]:.1f}%, プレミアム: ${spread["short_premium"]:.2f})')
        self.logger.info(f'買いプット: ${spread["long_strike"]:.2f} (デルタ: {spread["long_delta"]:.3f}, IV: {spread["long_iv"]:.1f}%, プレミアム: ${spread["long_premium"]:.2f})')
        self.logger.info(f'ネットプレミアム: ${spread["net_premium"]:.2f}')
        self.logger.info(f'最大利益: ${spread["max_profit"]:.2f}')
        self.logger.info(f'最大損失: ${spread["max_loss"]:.2f}')
        self.logger.info(f'リスク/リワード比: {spread["risk_reward_ratio"]:.2f}')
