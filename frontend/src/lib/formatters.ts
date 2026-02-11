/**
 * フォーマット関数
 */

/**
 * USD通貨フォーマット
 */
export function formatUSD(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * JPY通貨フォーマット
 */
export function formatJPY(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * 数値フォーマット（カンマ区切り）
 */
export function formatNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * パーセントフォーマット
 */
export function formatPercent(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined) return '-';
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * デルタフォーマット
 */
export function formatDelta(delta: number | null | undefined): string {
  if (delta === null || delta === undefined) return '-';
  return delta.toFixed(3);
}

/**
 * IVフォーマット
 */
export function formatIV(iv: number | null | undefined): string {
  if (iv === null || iv === undefined) return '-';
  return `${(iv * 100).toFixed(1)}%`;
}

/**
 * 日時フォーマット（ローカル時刻）
 */
export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

/**
 * 日付フォーマット
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

/**
 * 相対時間フォーマット（例: "2 hours ago"）
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return `${diffSecs}秒前`;
  if (diffMins < 60) return `${diffMins}分前`;
  if (diffHours < 24) return `${diffHours}時間前`;
  if (diffDays < 7) return `${diffDays}日前`;
  return formatDate(dateString);
}

/**
 * 有効期限フォーマット（YYYYMMDD → YYYY-MM-DD）
 */
export function formatExpiry(expiry: string): string {
  if (!expiry || expiry.length !== 8) return expiry;
  return `${expiry.slice(0, 4)}-${expiry.slice(4, 6)}-${expiry.slice(6, 8)}`;
}

/**
 * ストライクプライスフォーマット
 */
export function formatStrike(strike: number): string {
  return `$${strike.toFixed(2)}`;
}

/**
 * P&Lカラー取得
 */
export function getPnlColor(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'text-muted';
  if (value > 0) return 'text-success';
  if (value < 0) return 'text-danger';
  return 'text-muted';
}

/**
 * ポジションステータス表示名
 */
export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    open: 'オープン',
    closed: 'クローズ',
    expired: '満期',
  };
  return labels[status] || status;
}

/**
 * ステータスバッジクラス
 */
export function getStatusBadgeClass(status: string): string {
  const classes: Record<string, string> = {
    open: 'badge-success',
    closed: 'badge-warning',
    expired: 'badge-danger',
  };
  return `badge ${classes[status] || ''}`;
}
