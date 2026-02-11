/**
 * PriceFlash コンポーネント
 * 価格変動時にフラッシュアニメーションを表示
 */

'use client';

import { ReactNode } from 'react';

interface PriceFlashProps {
  children: ReactNode;
  direction: 'up' | 'down' | null;
  className?: string;
}

export default function PriceFlash({ children, direction, className = '' }: PriceFlashProps) {
  const flashClass = direction === 'up' ? 'price-flash-up' :
                     direction === 'down' ? 'price-flash-down' :
                     '';

  return (
    <span className={`inline-block transition-all duration-500 ${flashClass} ${className}`}>
      {children}
    </span>
  );
}
