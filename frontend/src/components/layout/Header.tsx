'use client';

import { Activity, Settings } from 'lucide-react';

interface HeaderProps {
  ibkrConnected: boolean;
  mode: 'mock' | 'real';
}

export default function Header({ ibkrConnected, mode }: HeaderProps) {
  return (
    <header className="h-16 bg-dark-surface border-b border-dark-border flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-white">SPY Credit Spread Dashboard</h1>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${ibkrConnected ? 'bg-accent-success' : 'bg-accent-danger'}`} />
          <span className="text-sm text-gray-400">
            {ibkrConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className={`badge ${mode === 'mock' ? 'badge-warning' : 'badge-success'}`}>
          {mode.toUpperCase()}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 hover:bg-dark-hover rounded-lg transition-colors">
          <Activity size={20} className="text-gray-400" />
        </button>
        <button className="p-2 hover:bg-dark-hover rounded-lg transition-colors">
          <Settings size={20} className="text-gray-400" />
        </button>
      </div>
    </header>
  );
}
