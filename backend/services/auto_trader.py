"""
自動売買サービス: スケジュールに基づいてBull Put Spreadを自動執行

フロー:
1. VIX取得 → デルタ調整
2. SPY価格取得
3. オプションチェーン取得 → スプレッド候補選択
4. ポジションサイズ計算
5. Bull Put Spread 発注
"""

import logging
import math
from datetime import datetime
from typing import Optional
import pytz

import config

logger = logging.getLogger(__name__)

# グローバル状態（スケジューラー・UIから参照）
_state = {
    'is_active': False,      # スケジューラー有効かどうか
    'is_running': False,     # 現在実行中かどうか
    'last_run_time': None,   # 最終実行時刻（ISO文字列）
    'last_run_result': None, # 最終実行結果
    'last_error': None,      # 最終エラーメッセージ
    'next_run_time': None,   # 次回実行予定時刻（ISO文字列）
}


def get_auto_trader_status() -> dict:
    """自動売買の現在の状態を取得"""
    return dict(_state)


def set_scheduler_active(active: bool, next_run: Optional[str] = None):
    """スケジューラーの有効/無効と次回実行時刻をセット"""
    _state['is_active'] = active
    if next_run:
        _state['next_run_time'] = next_run


def _execute_entry_sync(ib) -> dict:
    """
    IBKR worker thread内で実行される自動発注コア処理

    Args:
        ib: IB instance (IBKRService のワーカースレッドから渡される)

    Returns:
        実行結果の辞書
    """
    from ib_insync import Stock, Option, Index, LimitOrder
    from backend.services.strategy_service import get_adjusted_delta

    result = {
        'success': False,
        'reason': None,
        'spread': None,
        'quantity': 0,
        'order_status': None,
        'vix': None,
        'adjusted_delta': None,
        'timestamp': datetime.now(pytz.UTC).isoformat(),
    }

    # 1. 口座情報取得
    account_values = ib.accountValues()
    net_liq = None
    for v in account_values:
        if v.tag == 'NetLiquidation' and v.currency == 'USD':
            net_liq = float(v.value)
            break

    if not net_liq or net_liq <= 0:
        result['reason'] = '口座情報（NetLiquidation）取得失敗'
        return result

    logger.info(f'NetLiquidation: ${net_liq:,.0f}')

    # 2. VIX取得（失敗時はデフォルト値 18.5 を使用）
    vix = 18.5
    try:
        vix_contract = Index('VIX', 'CBOE')
        ib.qualifyContracts(vix_contract)
        ib.reqMktData(vix_contract, '', False, False)
        ib.sleep(2)
        vix_ticker = ib.ticker(vix_contract)
        ib.cancelMktData(vix_contract)

        v_last = vix_ticker.last if vix_ticker.last and not math.isnan(vix_ticker.last) else None
        v_close = vix_ticker.close if vix_ticker.close and not math.isnan(vix_ticker.close) else None
        if v_last:
            vix = v_last
        elif v_close:
            vix = v_close
    except Exception as e:
        logger.warning(f'VIX取得失敗（デフォルト {vix} を使用）: {e}')

    result['vix'] = vix
    logger.info(f'VIX: {vix:.1f}')

    # 3. VIX連動デルタ調整
    adjusted_delta, position_size_factor = get_adjusted_delta(vix)
    if adjusted_delta is None:
        result['reason'] = f'VIX高すぎ（{vix:.1f} >= 35）、エントリー見送り'
        return result

    result['adjusted_delta'] = adjusted_delta
    logger.info(f'Target delta: {adjusted_delta:.2f}, size factor: {position_size_factor:.1f}')

    # 4. SPY価格取得
    spy_contract = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(spy_contract)
    ib.reqMktData(spy_contract, '', False, False)
    ib.sleep(2)
    spy_ticker = ib.ticker(spy_contract)
    ib.cancelMktData(spy_contract)

    spy_price = spy_ticker.last
    if not spy_price or math.isnan(spy_price):
        bid = spy_ticker.bid if spy_ticker.bid and not math.isnan(spy_ticker.bid) else None
        ask = spy_ticker.ask if spy_ticker.ask and not math.isnan(spy_ticker.ask) else None
        spy_price = (bid + ask) / 2 if bid and ask else None

    if not spy_price:
        result['reason'] = 'SPY価格取得失敗'
        return result

    logger.info(f'SPY price: ${spy_price:.2f}')

    # 5. オプションチェーン取得（最も満期が多いチェーンを選択）
    chains = ib.reqSecDefOptParams('SPY', '', 'STK', spy_contract.conId)
    if not chains:
        result['reason'] = 'オプションチェーン取得失敗'
        return result

    # SMART チェーンは近期オプションを含まないため、最大チェーンを使用
    chain = max(chains, key=lambda c: len(c.expirations))

    today = datetime.now().date()
    valid_expirations = []
    for exp_str in sorted(chain.expirations):
        exp_date = datetime.strptime(exp_str, '%Y%m%d').date()
        dte = (exp_date - today).days
        if config.MIN_DTE <= dte <= config.MAX_DTE:
            valid_expirations.append((exp_str, exp_date, dte))

    if not valid_expirations:
        result['reason'] = f'DTE {config.MIN_DTE}-{config.MAX_DTE}の満期なし'
        return result

    logger.info(f'Valid expirations: {[(e[0], e[2]) for e in valid_expirations]}')

    # 6. ATM近辺のストライクに絞る（SPY価格の85%〜100%）
    target_strikes_all = sorted([
        s for s in chain.strikes
        if spy_price * 0.85 <= s < spy_price
    ])
    target_strikes = target_strikes_all[-15:] if len(target_strikes_all) > 15 else target_strikes_all

    if not target_strikes:
        result['reason'] = '対象ストライクなし'
        return result

    candidates = []

    # 7. 各満期のオプションデータ取得（最大2満期）
    for exp_str, exp_date, dte in valid_expirations[:2]:
        option_contracts = [
            Option('SPY', exp_str, strike, 'P', 'SMART', tradingClass='SPY')
            for strike in target_strikes
        ]

        try:
            ib.qualifyContracts(*option_contracts)
            option_contracts = [c for c in option_contracts if c.conId]
        except Exception as qe:
            logger.warning(f'qualifyContracts失敗 {exp_str}: {qe}')
            continue

        if not option_contracts:
            continue

        tickers_map = {}
        for opt in option_contracts:
            t = ib.reqMktData(opt, '100,101,105,106', False, False)
            tickers_map[opt.strike] = (opt, t)

        ib.sleep(5)  # データ到着を待つ

        for strike, (opt, ticker) in tickers_map.items():
            ib.cancelMktData(opt)
            if not ticker:
                continue

            greeks = ticker.modelGreeks or ticker.bidGreeks or ticker.lastGreeks
            delta = None
            iv = None
            if greeks:
                if greeks.delta is not None and not math.isnan(greeks.delta):
                    delta = greeks.delta
                if greeks.impliedVol is not None and not math.isnan(greeks.impliedVol):
                    iv = greeks.impliedVol

            abs_delta = abs(delta) if delta is not None else None

            bid = ticker.bid if ticker.bid and not math.isnan(ticker.bid) and ticker.bid > 0 else None
            ask = ticker.ask if ticker.ask and not math.isnan(ticker.ask) and ticker.ask > 0 else None
            mid = (bid + ask) / 2 if bid and ask else None

            # deltaとmidが揃っていないスプレッドは除外
            if not mid or not abs_delta:
                continue

            long_strike = strike - config.SPREAD_WIDTH
            max_profit = mid * 100
            max_loss = (config.SPREAD_WIDTH - mid) * 100 if mid < config.SPREAD_WIDTH else None

            if not max_loss or max_loss <= 0:
                continue

            # 目標デルタへの近さでスコアリング（0.1以内ならフルスコア）
            delta_diff = abs(abs_delta - adjusted_delta)
            delta_score = max(0.0, 1.0 - delta_diff / 0.1)

            candidates.append({
                'short_strike': strike,
                'long_strike': long_strike,
                'expiry': exp_str,
                'exp_date': exp_date.strftime('%Y-%m-%d'),
                'dte': dte,
                'short_delta': abs_delta,
                'short_iv': iv,
                'net_premium': mid,
                'max_profit': max_profit,
                'max_loss': max_loss,
                'delta_score': delta_score,
                'risk_reward_ratio': max_loss / max_profit if max_profit > 0 else None,
            })

    if not candidates:
        result['reason'] = 'スプレッド候補なし（delta/midデータ不足）'
        return result

    # 8. 最適スプレッド選択（目標デルタに最も近いもの）
    candidates.sort(key=lambda x: x['delta_score'], reverse=True)
    best = candidates[0]

    logger.info(
        f'Best spread: {best["short_strike"]}/{best["long_strike"]} '
        f'DTE={best["dte"]} delta={best["short_delta"]:.3f} mid=${best["net_premium"]:.2f}'
    )

    # 9. ポジションサイズ計算
    max_risk = net_liq * config.RISK_PER_TRADE * position_size_factor
    quantity = max(1, int(max_risk / best['max_loss']))

    logger.info(f'Position size: {quantity} contracts, total max risk: ${best["max_loss"] * quantity:,.0f}')

    # 10. Bull Put Spread 発注
    short_put = Option('SPY', best['expiry'], best['short_strike'], 'P', 'SMART', tradingClass='SPY')
    long_put = Option('SPY', best['expiry'], best['long_strike'], 'P', 'SMART', tradingClass='SPY')

    try:
        ib.qualifyContracts(short_put, long_put)
    except Exception as e:
        result['reason'] = f'発注コントラクト検証失敗: {e}'
        return result

    # 指値: midpointから LIMIT_PRICE_OFFSET 有利に
    net_premium = best['net_premium']
    limit_price = round(net_premium - config.LIMIT_PRICE_OFFSET, 2)

    # SELL put: 高めの指値で入りやすく
    short_order = LimitOrder('SELL', quantity, round(limit_price + 0.05, 2), transmit=False)
    # BUY put: 低めの指値で入りやすく（両注文を同時送信）
    long_order = LimitOrder('BUY', quantity, round(limit_price - 0.05, 2), transmit=True)

    short_trade = ib.placeOrder(short_put, short_order)
    long_trade = ib.placeOrder(long_put, long_order)
    ib.sleep(5)

    short_status = short_trade.orderStatus.status if short_trade else 'Unknown'
    long_status = long_trade.orderStatus.status if long_trade else 'Unknown'

    order_ok = short_status in ('Submitted', 'Filled', 'PreSubmitted') and \
               long_status in ('Submitted', 'Filled', 'PreSubmitted')

    result.update({
        'success': order_ok,
        'spread': best,
        'quantity': quantity,
        'order_status': f'Short: {short_status}, Long: {long_status}',
        'reason': None if order_ok else f'注文ステータス異常: {short_status}/{long_status}',
    })

    return result


async def run_auto_entry(service) -> dict:
    """
    自動エントリーを実行（FastAPI/スケジューラーから呼び出し）

    Args:
        service: IBKRService instance

    Returns:
        実行結果の辞書
    """
    if _state['is_running']:
        logger.warning('自動エントリー: 既に実行中のためスキップ')
        return {'success': False, 'reason': '既に実行中'}

    if not service or not service.is_connected:
        logger.error('自動エントリー: IBKR未接続')
        return {'success': False, 'reason': 'IBKR未接続'}

    _state['is_running'] = True
    _state['last_run_time'] = datetime.now(pytz.UTC).isoformat()

    try:
        logger.info('=' * 50)
        logger.info('自動エントリー開始')
        logger.info('=' * 50)

        # タイムアウト 120秒（オプションデータ取得に時間がかかるため）
        result = await service.execute_timeout(120, _execute_entry_sync, service.ib)

        _state['last_run_result'] = result
        _state['last_error'] = None if result.get('success') else result.get('reason')

        if result.get('success'):
            spread = result['spread']
            logger.info(
                f'自動エントリー完了: {spread["short_strike"]}/{spread["long_strike"]} '
                f'x{result["quantity"]}枚 | ステータス: {result["order_status"]}'
            )
        else:
            logger.warning(f'自動エントリー見送り: {result.get("reason")}')

        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f'自動エントリーエラー: {error_msg}')
        _state['last_error'] = error_msg
        _state['last_run_result'] = {'success': False, 'reason': error_msg}
        return {'success': False, 'reason': error_msg}

    finally:
        _state['is_running'] = False


def _monitor_positions_sync(ib) -> list:
    """
    IBKR worker thread内で実行されるポジション監視・損切りコア処理

    損切り条件:
    1. 現在のネットプレミアム >= エントリープレミアム × STOP_LOSS_MULTIPLIER（デフォルト2倍）
    2. SPY価格 < ショートストライク × 0.98（ストライクの2%下）

    Args:
        ib: IB instance

    Returns:
        実行したアクションのリスト
    """
    from ib_insync import Stock, Option, MarketOrder
    from position import PositionManager

    actions = []
    pm = PositionManager()
    open_positions = pm.get_open_positions()

    if not open_positions:
        logger.info('ポジション監視: オープンポジションなし')
        return actions

    logger.info(f'ポジション監視: {len(open_positions)}件チェック')

    # SPY価格を一度だけ取得
    spy = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(spy)
    ib.reqMktData(spy, '', False, False)
    ib.sleep(2)
    spy_ticker = ib.ticker(spy)
    ib.cancelMktData(spy)

    spy_price = spy_ticker.last
    if not spy_price or math.isnan(spy_price):
        mid = (spy_ticker.bid + spy_ticker.ask) / 2 if (spy_ticker.bid and spy_ticker.ask) else None
        spy_price = mid

    if not spy_price:
        logger.warning('ポジション監視: SPY価格取得失敗、スキップ')
        return actions

    logger.info(f'ポジション監視: SPY ${spy_price:.2f}')

    for spread_id, position in open_positions.items():
        try:
            short_strike = float(position['short_strike'])
            long_strike = float(position['long_strike'])
            quantity = int(position['quantity'])
            entry_premium = float(position['entry_premium'])
            # expiration フィールドは YYYYMMDD 形式（position.py の add_position 参照）
            expiration = position.get('expiration', position.get('expiry', ''))
            expiration = expiration.replace('-', '')  # YYYY-MM-DD → YYYYMMDD

            stop_loss_threshold = entry_premium * config.STOP_LOSS_MULTIPLIER

            # 現在のオプション価格を取得（ショート + ロング）
            short_put = Option('SPY', expiration, short_strike, 'P', 'SMART', tradingClass='SPY')
            long_put = Option('SPY', expiration, long_strike, 'P', 'SMART', tradingClass='SPY')

            try:
                ib.qualifyContracts(short_put, long_put)
            except Exception as qe:
                logger.warning(f'{spread_id}: contract検証失敗 ({qe}), スキップ')
                continue

            short_ticker = ib.reqMktData(short_put, '', False, False)
            long_ticker = ib.reqMktData(long_put, '', False, False)
            ib.sleep(3)
            ib.cancelMktData(short_put)
            ib.cancelMktData(long_put)

            def _mid(t):
                bid = t.bid if t.bid and not math.isnan(t.bid) and t.bid > 0 else None
                ask = t.ask if t.ask and not math.isnan(t.ask) and t.ask > 0 else None
                last = t.last if t.last and not math.isnan(t.last) and t.last > 0 else None
                if bid and ask:
                    return (bid + ask) / 2
                return last

            short_mid = _mid(short_ticker)
            long_mid = _mid(long_ticker)

            # 現在のネットプレミアム（Buy-to-close コスト）
            if short_mid and long_mid:
                current_net_premium = short_mid - long_mid
            elif short_mid:
                current_net_premium = short_mid
            else:
                logger.warning(f'{spread_id}: オプション価格取得失敗、損切りチェックスキップ')
                continue

            # 損切り判定
            should_close = False
            reason = None

            if current_net_premium >= stop_loss_threshold:
                should_close = True
                reason = (
                    f'プレミアム{config.STOP_LOSS_MULTIPLIER}倍到達 '
                    f'(entry: ${entry_premium:.2f} → current: ${current_net_premium:.2f})'
                )

            elif spy_price < short_strike * 0.98:
                should_close = True
                reason = (
                    f'SPY価格がショートストライク98%を下回った '
                    f'(SPY: ${spy_price:.2f} < ${short_strike * 0.98:.2f})'
                )

            if not should_close:
                logger.info(
                    f'{spread_id}: 正常 | '
                    f'premium ${current_net_premium:.2f} (threshold ${stop_loss_threshold:.2f}) | '
                    f'SPY ${spy_price:.2f} vs strike ${short_strike:.2f}'
                )
                continue

            # 損切り実行: 成行で即時クローズ
            logger.warning(f'🚨 損切り発動: {spread_id} | 理由: {reason}')

            # ショートプット: Buy-to-close（成行）
            close_short = MarketOrder('BUY', quantity, transmit=False)
            # ロングプット: Sell-to-close（成行、同時送信）
            close_long = MarketOrder('SELL', quantity, transmit=True)

            trade_short = ib.placeOrder(short_put, close_short)
            trade_long = ib.placeOrder(long_put, close_long)
            ib.sleep(5)

            short_close_status = trade_short.orderStatus.status if trade_short else 'Unknown'
            long_close_status = trade_long.orderStatus.status if trade_long else 'Unknown'

            close_ok = short_close_status in ('Submitted', 'Filled', 'PreSubmitted') and \
                       long_close_status in ('Submitted', 'Filled', 'PreSubmitted')

            actions.append({
                'spread_id': spread_id,
                'action': 'STOP_LOSS',
                'reason': reason,
                'current_net_premium': current_net_premium,
                'entry_premium': entry_premium,
                'spy_price': spy_price,
                'close_order_ok': close_ok,
                'order_status': f'Short: {short_close_status}, Long: {long_close_status}',
            })

            if close_ok:
                # PositionManager にクローズを記録
                try:
                    pm.close_position(spread_id, exit_premium=current_net_premium, fx_rate=None)
                except Exception as pe:
                    logger.warning(f'{spread_id}: position close記録失敗: {pe}')
                logger.warning(f'✓ {spread_id}: 損切りクローズ完了')
            else:
                logger.error(f'✗ {spread_id}: 損切り注文ステータス異常 {short_close_status}/{long_close_status}')

        except Exception as e:
            logger.error(f'{spread_id}: 監視中エラー: {e}')

    return actions


async def run_position_monitor(service) -> list:
    """
    ポジション監視を実行（スケジューラーから15分おきに呼び出し）

    Args:
        service: IBKRService instance

    Returns:
        実行したアクションのリスト
    """
    if not service or not service.is_connected:
        return []

    if _state['is_running']:
        logger.info('ポジション監視: エントリー実行中のためスキップ')
        return []

    try:
        actions = await service.execute_timeout(60, _monitor_positions_sync, service.ib)
        if actions:
            logger.warning(f'ポジション監視: {len(actions)}件の損切りを実行')
        return actions
    except Exception as e:
        logger.error(f'ポジション監視エラー: {e}')
        return []
