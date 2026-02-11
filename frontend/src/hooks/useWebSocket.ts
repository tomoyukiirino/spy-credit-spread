/**
 * useWebSocket カスタムフック
 * WebSocket接続とリアルタイムデータ更新を管理
 */

import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { getWebSocketClient, WebSocketMessage } from '@/lib/websocket';

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  autoConnect?: boolean;
}

export function useWebSocket(channels: string[] = [], options: UseWebSocketOptions = {}) {
  const { onMessage, autoConnect = true } = options;
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // channelsを安定した文字列に変換して無限ループを防ぐ
  const channelsKey = useMemo(() => channels.sort().join(','), [channels.join(',')]);
  const channelsRef = useRef<string[]>(channels);

  // channelsKeyが変わった時だけchannelsRefを更新
  useEffect(() => {
    channelsRef.current = channels;
  }, [channelsKey]);

  const connect = useCallback(async () => {
    try {
      const client = getWebSocketClient();

      if (!client.isConnected()) {
        await client.connect();
        setIsConnected(true);
        setError(null);

        // 接続確立後、少し待ってからチャンネルを購読
        setTimeout(() => {
          channelsRef.current.forEach((channel) => {
            client.subscribe(channel);
          });
        }, 100);
      }
    } catch (err) {
      // エラーメッセージがある場合のみログ出力
      if (err instanceof Error && err.message) {
        console.error('[useWebSocket] Connection failed:', err.message);
      }
      setError(err instanceof Error ? err : new Error('Connection failed'));
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    const client = getWebSocketClient();
    client.disconnect();
    setIsConnected(false);
  }, []);

  // 初回接続のみ（channelsKeyは含めない = 再接続しない）
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // クリーンアップ関数では切断しない
    // （シングルトンWebSocketは他のコンポーネントでも使用されている可能性があるため）
    return () => {
      // 何もしない - WebSocketは共有リソース
    };
  }, [autoConnect, connect, disconnect]);

  // channelsが変更されたら購読を更新（接続は維持）
  useEffect(() => {
    const client = getWebSocketClient();
    if (client.isConnected()) {
      channelsRef.current.forEach((channel) => {
        client.subscribe(channel);
      });
    }
  }, [channelsKey]);

  useEffect(() => {
    if (onMessage) {
      const client = getWebSocketClient();

      // すべてのメッセージタイプでコールバックを登録
      const messageTypes = ['spy_price', 'options_update', 'fx_rate', 'subscribed', 'unsubscribed', 'pong'];

      messageTypes.forEach((type) => {
        client.on(type, onMessage);
      });

      return () => {
        messageTypes.forEach((type) => {
          client.off(type, onMessage);
        });
      };
    }
  }, [onMessage]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
  };
}

/**
 * SPY価格のリアルタイム更新用フック
 */
export function useSpyPrice() {
  const [spyPrice, setSpyPrice] = useState<number | null>(null);
  const [priceChange, setPriceChange] = useState<'up' | 'down' | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'spy_price' && message.data) {
      const newPrice = message.data.last || message.data.mid;

      if (newPrice !== null && newPrice !== undefined) {
        setSpyPrice((prevPrice) => {
          if (prevPrice !== null) {
            setPriceChange(newPrice > prevPrice ? 'up' : newPrice < prevPrice ? 'down' : null);

            // 500msでフラッシュアニメーションをリセット
            setTimeout(() => setPriceChange(null), 500);
          }
          return newPrice;
        });
      }
    }
  }, []);

  const { isConnected } = useWebSocket(['spy'], { onMessage: handleMessage });

  return {
    spyPrice,
    priceChange,
    isConnected,
  };
}

/**
 * FX レート（USD/JPY）のリアルタイム更新用フック
 */
export function useFxRate() {
  const [fxRate, setFxRate] = useState<number | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'fx_rate' && message.data) {
      const rate = message.data.usd_jpy;
      if (rate) {
        setFxRate(rate);
      }
    }
  }, []);

  const { isConnected } = useWebSocket(['fx'], { onMessage: handleMessage });

  return {
    fxRate,
    isConnected,
  };
}
