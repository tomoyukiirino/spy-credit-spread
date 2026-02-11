'use client';

import { useState } from 'react';
import { LayoutDashboard, TrendingUp, FileText, DollarSign, Settings, Target, MessageCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow';

interface SidebarProps {
  currentPage?: string;
}

export default function Sidebar({ currentPage = 'dashboard' }: SidebarProps) {
  const router = useRouter();
  const [isChatOpen, setIsChatOpen] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'ダッシュボード', icon: LayoutDashboard, href: '/' },
    { id: 'options', label: 'オプション取引', icon: Target, href: '/options' },
    { id: 'positions', label: 'ポジション', icon: TrendingUp, href: '/positions' },
    { id: 'trades', label: '取引履歴', icon: FileText, href: '/trades' },
    { id: 'tax', label: '税務', icon: DollarSign, href: '/tax' },
    { id: 'settings', label: '設定', icon: Settings, href: '/settings' },
  ];

  return (
    <aside className="w-64 bg-dark-surface border-r border-dark-border flex flex-col">
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;

            return (
              <li key={item.id}>
                <button
                  onClick={() => router.push(item.href)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-accent-primary text-white'
                      : 'text-gray-400 hover:bg-dark-hover hover:text-white'
                  }`}
                >
                  <Icon size={20} />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-dark-border space-y-3">
        {/* Claude チャットボタン */}
        <button
          onClick={() => setIsChatOpen(true)}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors bg-accent-primary/10 text-accent-primary hover:bg-accent-primary hover:text-white"
        >
          <MessageCircle size={20} />
          <span className="text-sm font-medium">Claude に相談</span>
        </button>

        <div className="text-xs text-gray-500">
          <p>Version 1.0.0</p>
          <p className="mt-1">© 2026 SPY Dashboard</p>
        </div>
      </div>

      {/* チャットウィンドウ */}
      <ChatWindow
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onMinimize={() => setIsChatOpen(false)}
      />
    </aside>
  );
}
