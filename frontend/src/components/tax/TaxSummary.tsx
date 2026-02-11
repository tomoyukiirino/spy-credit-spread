'use client';

import { FileText, Download, TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { formatUSD, formatPercent } from '@/lib/formatters';
import type { TaxSummary as TaxSummaryType } from '@/types';

interface TaxSummaryProps {
  data: TaxSummaryType | null;
  loading?: boolean;
  onExportCsv?: () => void;
}

export default function TaxSummary({ data, loading, onExportCsv }: TaxSummaryProps) {
  if (loading) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          税務サマリー
        </h2>
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          税務サマリー
        </h2>
        <div className="text-gray-500">データがありません</div>
      </div>
    );
  }

  const isProfit = (data.net_profit_usd ?? 0) >= 0;
  const needsFilng = (data.net_profit_jpy ?? 0) >= 200000; // 20万円以上で申告義務

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <FileText size={20} className="text-accent-primary" />
          税務サマリー {data.year}年
        </h2>
        {onExportCsv && (
          <button
            onClick={onExportCsv}
            className="btn btn-primary flex items-center gap-2 text-xs"
          >
            <Download size={14} />
            税務申告用CSV
          </button>
        )}
      </div>

      {/* 申告義務アラート */}
      {needsFilng && (
        <div className="mb-4 p-4 bg-accent-warning/10 border border-accent-warning/20 rounded-lg">
          <div className="flex items-center gap-2 text-accent-warning font-semibold mb-1">
            ⚠️ 確定申告が必要です
          </div>
          <div className="text-sm text-gray-300">
            年間利益が20万円を超えています。雑所得として確定申告が必要です。
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* 取引統計 */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-3">取引統計</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-dark-surface rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">総取引数</div>
              <div className="text-2xl font-mono font-bold">{data.total_trades}</div>
            </div>
            <div className="bg-dark-surface rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">勝ちトレード</div>
              <div className="text-2xl font-mono font-bold text-accent-success">{data.win_count}</div>
            </div>
            <div className="bg-dark-surface rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">負けトレード</div>
              <div className="text-2xl font-mono font-bold text-accent-danger">{data.loss_count}</div>
            </div>
            <div className="bg-dark-surface rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">勝率</div>
              <div className="text-2xl font-mono font-bold">{formatPercent(data.win_rate, 1)}</div>
            </div>
          </div>
        </div>

        {/* 損益サマリー（USD） */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <DollarSign size={16} />
            損益サマリー（USD）
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
              <span className="text-sm text-gray-400">受取プレミアム合計</span>
              <span className="text-lg font-mono font-bold text-accent-success">
                {formatUSD(data.total_premium_received_usd)}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
              <span className="text-sm text-gray-400">支払プレミアム合計</span>
              <span className="text-lg font-mono font-bold text-accent-danger">
                {formatUSD(data.total_premium_paid_usd)}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-dark-surface rounded-lg">
              <span className="text-sm text-gray-400">手数料合計</span>
              <span className="text-lg font-mono font-bold text-accent-danger">
                {formatUSD(data.total_commission_usd)}
              </span>
            </div>
            <div className={`flex items-center justify-between p-4 rounded-lg border-2 ${
              isProfit
                ? 'bg-accent-success/10 border-accent-success/30'
                : 'bg-accent-danger/10 border-accent-danger/30'
            }`}>
              <span className="text-sm font-semibold flex items-center gap-2">
                {isProfit ? (
                  <TrendingUp size={16} className="text-accent-success" />
                ) : (
                  <TrendingDown size={16} className="text-accent-danger" />
                )}
                純損益（USD）
              </span>
              <span className={`text-2xl font-mono font-bold ${
                isProfit ? 'text-accent-success' : 'text-accent-danger'
              }`}>
                {formatUSD(data.net_profit_usd)}
              </span>
            </div>
          </div>
        </div>

        {/* 損益サマリー（JPY） */}
        <div>
          <h3 className="text-sm font-semibold text-gray-400 mb-3">損益サマリー（JPY）</h3>
          <div className={`flex items-center justify-between p-4 rounded-lg border-2 ${
            isProfit
              ? 'bg-accent-success/10 border-accent-success/30'
              : 'bg-accent-danger/10 border-accent-danger/30'
          }`}>
            <div>
              <div className="text-sm font-semibold flex items-center gap-2 mb-1">
                {isProfit ? (
                  <TrendingUp size={16} className="text-accent-success" />
                ) : (
                  <TrendingDown size={16} className="text-accent-danger" />
                )}
                純損益（円換算）
              </div>
              <div className="text-xs text-gray-400">
                確定申告用（雑所得）
              </div>
            </div>
            <span className={`text-3xl font-mono font-bold ${
              isProfit ? 'text-accent-success' : 'text-accent-danger'
            }`}>
              ¥{(data.net_profit_jpy ?? 0).toLocaleString('ja-JP')}
            </span>
          </div>
        </div>

        {/* 税務情報 */}
        <div className="pt-4 border-t border-dark-border">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">税務情報</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">税務年度</span>
              <span className="font-mono font-bold">{data.year}年</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">申告区分</span>
              <span className="font-mono">雑所得（総合課税）</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">申告義務</span>
              <span className={`font-semibold ${needsFilng ? 'text-accent-warning' : 'text-accent-success'}`}>
                {needsFilng ? '有り（20万円超）' : '無し（20万円以下）'}
              </span>
            </div>
          </div>
        </div>

        {/* 注記 */}
        <div className="pt-4 border-t border-dark-border">
          <div className="text-xs text-gray-400 space-y-2">
            <p className="font-semibold text-gray-300">📌 確定申告について</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>雑所得として年間20万円超の利益で申告義務が発生</li>
              <li>為替レートは取引時点の実勢レートまたはTTSレートを使用可能</li>
              <li>手数料は経費として計上可能</li>
              <li>損失の繰越控除は不可（雑所得のため）</li>
              <li>確定申告期限: 翌年2月16日〜3月15日</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
