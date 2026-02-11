# イベントループ統合ガイド

## 概要

このドキュメントでは、`ib_insync`ライブラリとFastAPIの非同期環境を統合する際に直面したイベントループの競合問題と、その解決方法を説明します。

## 問題の背景

### ib_insyncとFastAPIの競合

`ib_insync`は内部的に`asyncio`を使用してInteractive Brokers TWS APIと通信します。一方、FastAPIも`asyncio`ベースのWebフレームワークです。両者を同じイベントループで実行しようとすると、以下のエラーが発生します：

```python
RuntimeError: This event loop is already running
```

これは、`ib_insync`の同期メソッド（`ib.connect()`, `ib.sleep()`など）が内部で`loop.run_until_complete()`を呼び出すためです。しかし、FastAPIのイベントループは既に実行中のため、ネストされた`run_until_complete()`呼び出しが失敗します。

## 解決アプローチ

### 採用した解決策：専用スレッド + キューベース実行

**コンセプト**：
- ib_insyncを**専用スレッド**で実行
- イベントループを作成するが`run_forever()`は呼ばない
- タスクをキュー経由で送信し、結果を`Future`で受け取る
- `ib.sleep(0.01)`でib_insyncの内部イベントを処理

### 実装の詳細

#### 1. IBKRServiceクラス（`backend/services/ibkr_service.py`）

```python
import threading
import asyncio
import queue
from concurrent.futures import Future
from ib_insync import IB, util

# FastAPIとの互換性のためにasyncioをパッチ
util.patchAsyncio()

class IBKRService:
    def __init__(self):
        self.ib = IB()
        self._thread = None
        self._connected = False
        self._running = False
        self._task_queue: queue.Queue[Tuple[Callable, tuple, dict, Future]] = queue.Queue()

    def start(self, host: str, port: int, client_id: int):
        """専用スレッドを起動してIBKRに接続"""
        self._running = True
        connect_done = threading.Event()
        connect_error: list = []

        def _worker():
            # 重要：イベントループを作成するが、run_forever()は呼ばない
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # 同期的に接続（ib_insyncが内部でloopを使用）
                self.ib.connect(host, port, clientId=client_id)
                self._connected = True
            except Exception as e:
                connect_error.append(e)
            finally:
                connect_done.set()

            # メインループ：キューからタスクを取り出して実行
            while self._running:
                try:
                    func, args, kwargs, future = self._task_queue.get(timeout=0.1)
                    try:
                        result = func(*args, **kwargs)
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                except queue.Empty:
                    # 重要：ib.sleep()でib_insyncの内部イベントを処理
                    if self._connected:
                        self.ib.sleep(0.01)

        self._thread = threading.Thread(target=_worker, daemon=True, name="ibkr-worker")
        self._thread.start()
        connect_done.wait(timeout=30)

    async def execute(self, func: Callable, *args, **kwargs):
        """FastAPIから非同期的に呼び出すメソッド"""
        future = Future()
        self._task_queue.put((func, args, kwargs, future))

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, future.result, 30)
```

#### 2. 使用方法（`backend/routers/market.py`）

```python
from backend.services.ibkr_service import IBKRService
from ib_insync import Stock

service = IBKRService.get_instance()

# 一連の処理を1つの関数にまとめる
def _fetch_spy_price(ib):
    contract = Stock('SPY', 'SMART', 'USD')
    ib.qualifyContracts(contract)
    ib.reqMktData(contract, '', False, False)
    ib.sleep(2)  # データ到着を待つ
    ticker = ib.ticker(contract)
    ib.cancelMktData(contract)

    return {
        'last': ticker.last,
        'bid': ticker.bid,
        'ask': ticker.ask
    }

# 専用スレッドで実行
data = await service.execute(_fetch_spy_price, service.ib)
```

## なぜこの方法で解決するのか

### 1. イベントループの分離

- **FastAPIのループ**：メインスレッドで実行
- **ib_insyncのループ**：専用スレッドで実行
- 両者は完全に独立しているため、競合しない

### 2. イベントループを作成するが主導権は渡さない

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
# run_forever()は呼ばない！
```

ib_insyncのメソッドが内部で`run_until_complete()`を呼ぶと、作成済みのループを使用します。しかし、ループ自体を`run_forever()`で実行していないため、FastAPIとの競合は発生しません。

### 3. `ib.sleep(0.01)`の役割

```python
except queue.Empty:
    if self._connected:
        self.ib.sleep(0.01)
```

ib_insyncは内部で価格更新などのイベントを処理しています。`ib.sleep(0.01)`を定期的に呼ぶことで、これらのイベントが適切に処理されます。

### 4. キューベースのタスク管理

- FastAPI → タスクをキューに投入 → 専用スレッドで実行 → 結果を`Future`で受け取る
- スレッド間の通信は`queue.Queue`と`Future`で安全に行う

## 試行錯誤の記録

### 失敗したアプローチ

#### アプローチ1: 同じイベントループで実行
```python
# ❌ エラー: This event loop is already running
result = ib.connect(host, port, clientId=client_id)
```

#### アプローチ2: `run_coroutine_threadsafe()`を使用
```python
# ❌ エラー: イベントループのコンテキストが複雑化
future = asyncio.run_coroutine_threadsafe(ib.connectAsync(...), loop)
```

#### アプローチ3: ThreadPoolExecutorで実行
```python
# ❌ エラー: There is no current event loop in thread
await loop.run_in_executor(executor, ib.connect, host, port)
```

#### アプローチ4: `util.patchAsyncio()`のみ
```python
# ❌ 不十分：パッチだけではイベントループの競合は解決しない
util.patchAsyncio()
```

### 成功したアプローチの要点

1. ✅ **専用スレッドでイベントループを作成**
2. ✅ **`run_forever()`は呼ばず、ib_insyncに制御を任せる**
3. ✅ **`ib.sleep(0.01)`で内部イベントを処理**
4. ✅ **キュー + Futureでスレッド間通信**
5. ✅ **`util.patchAsyncio()`も併用**

## モードの切り替え

### モックモード（開発用）

```python
# config.py
USE_MOCK_DATA = True
```

モックモードでは、IBKRServiceは使用せず、MockIBKRConnectionを使用します。

### リアルモード（本番用）

```python
# config.py
USE_MOCK_DATA = False
```

リアルモードでは、IBKRServiceを使用してTWSに接続します。

**注意**：TWS Paper Accountでリアルデータを取得する場合、マーケットデータサブスクリプションが必要です：
- TWS → Account → Market Data Subscriptions
- "US Securities Snapshot and Futures Value Bundle" を有効化（無料）

## トラブルシューティング

### エラー: "There is no current event loop in thread"

**原因**：専用スレッドでイベントループが作成されていない

**解決策**：
```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
```

### エラー: "This event loop is already running"

**原因**：FastAPIのイベントループで`run_until_complete()`を呼んでいる

**解決策**：専用スレッドでib_insyncを実行する

### リクエストがタイムアウトする

**原因**：ワーカースレッドがキューを処理していない

**解決策**：`ib.sleep(0.01)`を追加してイベント処理を継続

### マーケットデータエラー（Error 10089）

**原因**：TWS Paper Accountでマーケットデータサブスクリプションが未設定

**解決策**：TWSでマーケットデータサブスクリプションを有効化

## まとめ

ib_insyncとFastAPIの統合は、イベントループの管理が鍵となります。専用スレッドでib_insyncを実行し、キューベースでタスクを管理することで、両者を安全に統合できます。

**重要なポイント**：
- イベントループを作成するが、`run_forever()`は呼ばない
- `ib.sleep(0.01)`で内部イベントを処理
- タスクを1つの関数にまとめて`execute()`に渡す
- `util.patchAsyncio()`も併用

この設計により、FastAPIの非同期処理とib_insyncの同期APIを共存させることができます。
