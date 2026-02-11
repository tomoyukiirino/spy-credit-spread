'use client';

import { X, Calendar, DollarSign, TrendingUp } from 'lucide-react';
import { formatUSD, formatDateTime } from '@/lib/formatters';
import type { TradeRecord } from '@/types';

interface TradeDetailProps {
  trade: TradeRecord | null;
  onClose: () => void;
}

export default function TradeDetail({ trade, onClose }: TradeDetailProps) {
  if (!trade) return null;

  const isCredit = trade.net_amount_usd > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-dark-card border border-dark-border rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex items-center justify-between p-6 border-b border-dark-border">
          <h3 className="text-xl font-semibold">取引詳細</h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
          >
            <X size={20} className="text-gray-400" />
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-6 space-y-6">
          {/* 基本情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <Calendar size={16} />
              基本情報
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-400">Trade ID</div>
                <div className="text-sm font-mono">{trade.trade_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">Spread ID</div>
                <div className="text-sm font-mono">{trade.spread_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">取引日時 (JST)</div>
                <div className="text-sm font-mono">{formatDateTime(trade.timestamp_jst)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">取引日時 (ET)</div>
                <div className="text-sm font-mono">{formatDateTime(trade.timestamp_et)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">税務年度日付</div>
                <div className="text-sm font-mono">{trade.trade_date_jst}</div>
              </div>
            </div>
          </div>

          {/* オプション情報 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <TrendingUp size={16} />
              オプション情報
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-400">アクション</div>
                <div className="text-lg">
                  {trade.action === 'SELL' ? (
                    <span className="badge bg-red-500/20 text-red-400">SELL</span>
                  ) : (
                    <span className="badge bg-green-500/20 text-green-400">BUY</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-400">レッグ</div>
                <div className="text-lg">
                  {trade.leg === 'short' ? (
                    <span className="badge bg-orange-500/20 text-orange-400">Short</span>
                  ) : (
                    <span className="badge bg-blue-500/20 text-blue-400">Long</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-400">銘柄</div>
                <div className="text-lg font-mono font-bold">{trade.symbol}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">オプション種別</div>
                <div className="text-lg font-mono">{trade.option_type}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">ストライク</div>
                <div className="text-2xl font-mono font-bold">${trade.strike}</div>
              </div>
              <div>
                <div className="text-sm text-gray-400">満期日</div>
                <div className="text-lg font-mono">{trade.expiry}</div>
              </div>
            </div>
          </div>

          {/* 金額情報（USD） */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
              <DollarSign size={16} />
              金額情報 (USD)
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                <span className="text-sm text-gray-400">数量</span>
                <span className="text-lg font-mono font-bold">{trade.quantity} 枚</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                <span className="text-sm text-gray-400">単価</span>
                <span className="text-lg font-mono font-bold">{formatUSD(trade.premium_per_contract)}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                <span className="text-sm text-gray-400">合計プレミアム</span>
                <span className="text-lg font-mono font-bold">{formatUSD(Math.abs(trade.total_premium_usd))}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                <span className="text-sm text-gray-400">手数料</span>
                <span className="text-lg font-mono font-bold text-accent-danger">
                  {formatUSD(trade.commission_usd)}
                </span>
              </div>
              <div className="flex items-center justify-between p-4 bg-accent-primary/10 border border-accent-primary/20 rounded-lg">
                <span className="text-sm font-semibold">純額 (Net Amount)</span>
                <span className={`text-2xl font-mono font-bold ${
                  isCredit ? 'text-accent-success' : 'text-accent-danger'
                }`}>
                  {formatUSD(trade.net_amount_usd)}
                </span>
              </div>
            </div>
          </div>

          {/* 為替・円換算情報 */}
          {trade.fx_rate_usd_jpy && (
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-3">為替・円換算</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                  <span className="text-sm text-gray-400">為替レート (実勢)</span>
                  <span className="text-lg font-mono">
                    1 USD = ¥{trade.fx_rate_usd_jpy.toFixed(2)}
                  </span>
                </div>
                {trade.fx_rate_tts && (
                  <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
                    <span className="text-sm text-gray-400">TTSレート (参考)</span>
                    <span className="text-lg font-mono">
                      1 USD = ¥{trade.fx_rate_tts.toFixed(2)}
                    </span>
                  </div>
                )}
                {trade.net_amount_jpy && (
                  <div className="flex items-center justify-between p-4 bg-accent-primary/10 border border-accent-primary/20 rounded-lg">
                    <span className="text-sm font-semibold">純額 (円換算)</span>
                    <span className={`text-2xl font-mono font-bold ${
                      trade.net_amount_jpy >= 0 ? 'text-accent-success' : 'text-accent-danger'
                    }`}>
                      ¥{trade.net_amount_jpy.toLocaleString('ja-JP')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ステータス・備考 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-3">ステータス・備考</h4>
            <div className="space-y-2">
              <div>
                <div className="text-sm text-gray-400">ポジションステータス</div>
                <div className="text-sm font-mono">{trade.position_status}</div>
              </div>
              {trade.notes && (
                <div>
                  <div className="text-sm text-gray-400">備考</div>
                  <div className="text-sm bg-dark-surface rounded p-3">{trade.notes}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* フッター */}
        <div className="p-6 border-t border-dark-border">
          <button
            onClick={onClose}
            className="w-full btn bg-dark-hover text-gray-300 hover:bg-dark-border"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
}
