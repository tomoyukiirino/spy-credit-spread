"""
モックデータ生成モジュール: テスト・開発用のダミーデータ
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
from tabulate import tabulate
import config
from logger import get_logger


class MockMarketDataManager:
    """
    モックマーケットデータマネージャー
    data.pyのMarketDataManagerと同じインターフェースでモックデータを提供
    """

    def __init__(self, ib=None):
        """
        Args:
            ib: 互換性のため受け取るが使用しない
        """
        self.logger = get_logger()
        self.logger.info('🎭 モックデータモードで動作中')

        # SPY現在価格（モック）
        self.spy_price = 583.50

    def get_spy_price(self) -> Optional[Dict[str, float]]:
        """
        SPYの現在価格を取得（モック）

        Returns:
            {'last': 最終価格, 'bid': Bid, 'ask': Ask, 'mid': 中間値}
        """
        spread = 0.05
        price_data = {
            'last': self.spy_price,
            'bid': self.spy_price - spread,
            'ask': self.spy_price + spread,
            'mid': self.spy_price
        }

        self.logger.info(f'SPY価格（モック）: Last=${price_data["last"]:.2f}, Bid=${price_data["bid"]:.2f}, Ask=${price_data["ask"]:.2f}')

        return price_data

    def get_option_chain_params(self) -> List[str]:
        """
        SPYのオプションチェーンパラメータ（満期日リスト）を取得（モック）

        Returns:
            満期日のリスト（YYYYMMDD形式の文字列）
        """
        today = datetime.now().date()
        expirations = []

        # 今後7日以内の満期日を生成（月・水・金を想定）
        for i in range(1, 10):
            future_date = today + timedelta(days=i)
            # 月曜(0)、水曜(2)、金曜(4)のみ
            if future_date.weekday() in [0, 2, 4]:
                exp_str = future_date.strftime('%Y%m%d')
                dte = (future_date - today).days
                if config.MIN_DTE <= dte <= config.MAX_DTE:
                    expirations.append(exp_str)

        self.logger.info(f'満期日候補（モック、DTE {config.MIN_DTE}-{config.MAX_DTE}日）: {len(expirations)}件')
        for exp in expirations:
            exp_date = datetime.strptime(exp, '%Y%m%d').date()
            dte = (exp_date - today).days
            self.logger.info(f'  {exp} ({exp_date.strftime("%Y-%m-%d")}) - DTE: {dte}日')

        return expirations

    def get_put_options_with_greeks(
        self,
        expiration: str,
        spy_price: float
    ) -> pd.DataFrame:
        """
        指定満期日のPutオプションとGreeksを取得（モック）

        Args:
            expiration: 満期日（YYYYMMDD形式）
            spy_price: SPYの現在価格

        Returns:
            オプション情報のDataFrame
        """
        # 行使価格の範囲を計算（SPY価格の-3%〜-15%）
        strike_min = spy_price * 0.85  # -15%
        strike_max = spy_price * 0.97  # -3%

        self.logger.info(f'行使価格範囲（モック）: ${strike_min:.2f} - ${strike_max:.2f}')

        # $5刻みでストライクのリストを生成
        strikes = []
        strike = int(strike_min / 5) * 5  # 5の倍数に切り下げ
        while strike <= strike_max:
            strikes.append(float(strike))
            strike += 5

        self.logger.info(f'チェック対象ストライク（モック）: {len(strikes)}件')

        # モックオプションデータを生成
        options_data = []
        for strike in strikes:
            # 距離に応じてデルタとIVを計算（リアルなシミュレーション）
            # Putオプション: ストライクがSPY価格より低いほどOTM、デルタは小さい
            distance_pct = (spy_price - strike) / spy_price

            # デルタ: OTMほど0に近づく、ATMに近いほど0.50に近づく
            # distance_pct: 0.03〜0.15 の範囲
            # デルタ: 0.05（OTM、-15%）〜 0.30（ATM寄り、-3%）
            delta = max(0.05, min(0.35, 0.50 - distance_pct * 3))

            # IV: ATMから離れるほど少し上がる（ボラティリティスマイル）
            iv_base = 18.0
            iv = iv_base + distance_pct * 50  # OTMほどIVが少し上がる

            # プレミアム: デルタが大きいほど高い（より価値がある）
            # Putオプションのプレミアムは、ITM度合いとIVで決まる
            intrinsic_value = max(0, strike - spy_price)  # 内在価値（ITMの場合のみ）
            time_value = delta * spy_price * 0.025  # 時間価値
            mid = intrinsic_value + time_value

            spread_pct = 0.10  # Bid/Askスプレッド10%
            spread_amount = mid * spread_pct
            bid = mid - spread_amount / 2
            ask = mid + spread_amount / 2

            options_data.append({
                'strike': strike,
                'delta': delta,
                'iv': iv,
                'bid': bid,
                'ask': ask,
                'mid': mid,
                'contract': None  # モックなのでNone
            })

        # DataFrameに変換してデルタでソート
        df = pd.DataFrame(options_data)
        df = df.sort_values('delta')

        self.logger.info(f'Putオプション取得完了（モック）: {len(df)}件')

        return df

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

    def get_options_by_dte_range(self, dte_min: int = None, dte_max: int = None) -> List[Dict]:
        """
        DTEレンジでオプションデータを取得（モック）

        Args:
            dte_min: 最小DTE
            dte_max: 最大DTE

        Returns:
            list: オプションデータのリスト
        """
        if dte_min is None:
            dte_min = config.MIN_DTE
        if dte_max is None:
            dte_max = config.MAX_DTE

        # 満期日を取得
        expirations = self.get_option_chain_params()
        spy_price = self.spy_price
        today = datetime.now().date()

        all_options = []

        for expiration in expirations:
            exp_date = datetime.strptime(expiration, '%Y%m%d').date()
            dte = (exp_date - today).days

            # DTEフィルタ
            if dte < dte_min or dte > dte_max:
                continue

            # オプションデータを取得
            options_df = self.get_put_options_with_greeks(expiration, spy_price)

            # DataFrameを辞書のリストに変換
            for _, row in options_df.iterrows():
                option_data = {
                    'strike': row['strike'],
                    'expiry': expiration,
                    'exp_date': exp_date.strftime('%Y-%m-%d'),
                    'dte': dte,
                    'bid': row['bid'],
                    'ask': row['ask'],
                    'mid': row['mid'],
                    'delta': row['delta'],
                    'gamma': None,  # モックでは未実装
                    'theta': None,  # モックでは未実装
                    'iv': row['iv'],
                    'volume': None,  # モックでは未実装
                    'open_interest': None  # モックでは未実装
                }
                all_options.append(option_data)

        self.logger.info(f'オプションデータ取得完了（モック）: {len(all_options)}件 (DTE {dte_min}-{dte_max})')

        return all_options

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

        self.logger.info(f'\n{title}（モック）')
        self.logger.info('\n' + tabulate(display_df, headers='keys', tablefmt='grid', showindex=False))

    def display_spread_info(self, spread: Dict):
        """
        スプレッド情報を表示

        Args:
            spread: スプレッド情報の辞書
        """
        self.logger.info('\n=== Bull Put Spread 候補（モック）===')
        self.logger.info(f'売りプット: ${spread["short_strike"]:.2f} (デルタ: {spread["short_delta"]:.3f}, IV: {spread["short_iv"]:.1f}%, プレミアム: ${spread["short_premium"]:.2f})')
        self.logger.info(f'買いプット: ${spread["long_strike"]:.2f} (デルタ: {spread["long_delta"]:.3f}, IV: {spread["long_iv"]:.1f}%, プレミアム: ${spread["long_premium"]:.2f})')
        self.logger.info(f'ネットプレミアム: ${spread["net_premium"]:.2f}')
        self.logger.info(f'最大利益: ${spread["max_profit"]:.2f}')
        self.logger.info(f'最大損失: ${spread["max_loss"]:.2f}')
        self.logger.info(f'リスク/リワード比: {spread["risk_reward_ratio"]:.2f}')


class MockIBKRConnection:
    """
    モックIBKR接続クラス
    connection.pyのIBKRConnectionと同じインターフェース
    """

    def __init__(self, use_paper: bool = True, max_retries: int = 3):
        self.logger = get_logger()
        self.use_paper = use_paper
        self.connected = True
        self.logger.info('🎭 モックIBKR接続モードで動作中')

    def __enter__(self):
        """コンテキストマネージャーのエントリー"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.disconnect()
        return False

    def connect(self):
        """接続（モック）"""
        account_type = 'ペーパー' if self.use_paper else 'リアル'
        self.logger.info(f'IBKR {account_type}口座への接続を開始...（モック）')
        self.logger.info('✓ 接続成功（モック）')
        self.logger.info('管理口座: [\'DUP843993\']（モック）')

    def disconnect(self):
        """切断（モック）"""
        self.logger.info('IBKR接続を切断中...（モック）')
        self.connected = False
        self.logger.info('✓ 切断完了（モック）')

    def get_account_summary(self) -> Dict[str, Dict[str, str]]:
        """口座サマリー情報を取得（モック）"""
        return {
            'NetLiquidation': {'value': '10000.00', 'currency': 'USD'},
            'TotalCashValue': {'value': '8500.00', 'currency': 'USD'},
            'BuyingPower': {'value': '25000.00', 'currency': 'USD'}
        }

    def print_account_info(self):
        """口座情報をコンソールに表示（モック）"""
        summary = self.get_account_summary()
        self.logger.info('=== 口座情報（モック）===')
        for tag, data in summary.items():
            self.logger.info(f'  {tag}: {data["value"]} {data["currency"]}')

    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self.connected

    def get_ib(self):
        """IBインスタンスを取得（モックではNone）"""
        return None


class MockFXRateManager:
    """
    モック為替レートマネージャー
    fx_rate.pyのFXRateManagerと同じインターフェース
    """

    def __init__(self, ib=None):
        self.logger = get_logger()
        self.logger.info('🎭 モック為替レートモードで動作中')

    def get_usd_jpy_rate(self) -> Optional[float]:
        """USD/JPY為替レートを取得（モック）"""
        rate = 149.50
        self.logger.info(f'✓ USD/JPYレート取得（モック）: {rate:.2f}')
        return rate

    def get_tts_rate(self, trade_date: Optional[str] = None) -> Optional[float]:
        """TTSレートを取得（モック）"""
        self.logger.info('TTSレートは手動で入力してください（モック）')
        return None

    def get_rates_for_trade(self):
        """取引記録用の為替レートを取得（モック）"""
        spot_rate = self.get_usd_jpy_rate()
        tts_rate = self.get_tts_rate()
        return spot_rate, tts_rate
