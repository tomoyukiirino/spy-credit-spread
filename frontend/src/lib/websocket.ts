/**
 * WebSocketクライアント
 * バックエンドとのリアルタイム通信を管理
 */

export type WebSocketMessage = {
  type: string;
  data: any;
  timestamp?: string;
};

export type WebSocketCallback = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private callbacks: Map<string, Set<WebSocketCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isIntentionallyClosed = false;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * WebSocket接続を開始
   */
  connect(): Promise<void> {
    // 既に接続中または接続済みの場合は何もしない
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        console.log('[WebSocket] Already connected');
        return Promise.resolve();
      }
      if (this.ws.readyState === WebSocket.CONNECTING) {
        console.log('[WebSocket] Connection already in progress');
        return Promise.resolve();
      }
    }

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isIntentionallyClosed = false;

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = () => {
          // エラーは無視（接続失敗時はoncloseで処理される）
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] Disconnected', event.code);

          // 接続確立前のクローズ（接続失敗）
          if (event.code !== 1000 && event.code !== 1005) {
            reject(new Error(`WebSocket closed with code ${event.code}`));
          }

          if (!this.isIntentionallyClosed) {
            this.attemptReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 再接続を試みる
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnect failed:', error);
      });
    }, delay);
  }

  /**
   * WebSocket接続を切断
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * チャンネルを購読
   */
  subscribe(channel: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        action: 'subscribe',
        channel: channel,
      };
      this.ws.send(JSON.stringify(message));
      console.log(`[WebSocket] Subscribed to channel: ${channel}`);
    }
  }

  /**
   * チャンネルの購読を解除
   */
  unsubscribe(channel: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        action: 'unsubscribe',
        channel: channel,
      };
      this.ws.send(JSON.stringify(message));
      console.log(`[WebSocket] Unsubscribed from channel: ${channel}`);
    }
  }

  /**
   * メッセージタイプに対するコールバックを登録
   */
  on(type: string, callback: WebSocketCallback): void {
    if (!this.callbacks.has(type)) {
      this.callbacks.set(type, new Set());
    }
    this.callbacks.get(type)!.add(callback);
  }

  /**
   * コールバックを解除
   */
  off(type: string, callback: WebSocketCallback): void {
    const callbacks = this.callbacks.get(type);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  /**
   * 受信したメッセージを処理
   */
  private handleMessage(message: WebSocketMessage): void {
    const callbacks = this.callbacks.get(message.type);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(message);
        } catch (error) {
          console.error(`[WebSocket] Callback error for type ${message.type}:`, error);
        }
      });
    }
  }

  /**
   * 接続状態を取得
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// シングルトンインスタンス（グローバルスコープで保持）
let wsClient: WebSocketClient | null = null;
let isCreating = false;

/**
 * WebSocketクライアントのシングルトンインスタンスを取得
 */
export function getWebSocketClient(): WebSocketClient {
  if (!wsClient && !isCreating) {
    isCreating = true;
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
    wsClient = new WebSocketClient(wsUrl);
    console.log('[WebSocket] Singleton instance created');
    isCreating = false;
  }
  return wsClient!;
}
