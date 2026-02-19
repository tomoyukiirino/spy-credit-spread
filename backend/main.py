"""
FastAPI アプリケーション
SPY Bull Put Credit Spread ダッシュボードのバックエンドAPI
"""

import sys
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# .envファイルを読み込み
load_dotenv()

# 親ディレクトリをパスに追加（既存モジュールをインポートできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from logger import get_logger

# グローバル変数
app_state = {
    'ibkr_connection': None,
    'market_data_manager': None,
    'position_manager': None,
    'logger': None
}

# APScheduler インスタンス（グローバル）
scheduler = AsyncIOScheduler(timezone=pytz.timezone('US/Eastern'))


async def _broadcast_real_time_data(service):
    """
    リアルモード用: IBKRストリーミングデータをWebSocket経由でブロードキャスト（3秒ごと）
    """
    from ws.manager import manager

    while True:
        try:
            if manager.get_connection_count() > 0:
                spy_data = service.get_streaming_spy_price()
                if spy_data:
                    await manager.broadcast({
                        'type': 'spy_price',
                        'data': spy_data,
                        'timestamp': datetime.now(pytz.UTC).isoformat()
                    }, channel='spy')

                fx_data = service.get_streaming_fx_rate()
                if fx_data:
                    await manager.broadcast({
                        'type': 'fx_rate',
                        'data': fx_data,
                        'timestamp': datetime.now(pytz.UTC).isoformat()
                    }, channel='fx')

        except Exception as e:
            pass  # ブロードキャストエラーは無視して継続

        await asyncio.sleep(3)


def _setup_scheduler(service):
    """
    APScheduler を設定・起動する

    スケジュール:
    - 月曜 09:35 ET: 自動エントリー（Bull Put Spread 発注）
    """
    from backend.services.auto_trader import run_auto_entry, set_scheduler_active

    entry_hour, entry_minute = config.ENTRY_TIME.split(':')

    async def _scheduled_entry():
        _logger = get_logger()
        _logger.info(f'[スケジューラー] 自動エントリー起動 ({config.ENTRY_TIME} ET)')
        result = await run_auto_entry(service)
        if result.get('success'):
            _logger.info(f'[スケジューラー] エントリー完了: {result}')
        else:
            _logger.warning(f'[スケジューラー] エントリー見送り: {result.get("reason")}')

    scheduler.add_job(
        _scheduled_entry,
        CronTrigger(
            day_of_week='mon',
            hour=int(entry_hour),
            minute=int(entry_minute),
            timezone=pytz.timezone('US/Eastern')
        ),
        id='auto_entry',
        replace_existing=True
    )

    # ポジション監視: 平日マーケット時間中（9:30〜16:15 ET）に15分おき
    async def _scheduled_monitor():
        from backend.services.auto_trader import run_position_monitor
        _logger = get_logger()
        actions = await run_position_monitor(service)
        if actions:
            for a in actions:
                _logger.warning(f'[監視] 損切り実行: {a["spread_id"]} | {a["reason"]}')

    scheduler.add_job(
        _scheduled_monitor,
        CronTrigger(
            day_of_week='mon-fri',
            hour='9-16',
            minute='*/15',
            timezone=pytz.timezone('US/Eastern')
        ),
        id='position_monitor',
        replace_existing=True
    )

    scheduler.start()

    # 次回実行時刻を取得してステータスに反映
    job = scheduler.get_job('auto_entry')
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    set_scheduler_active(True, next_run)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    起動時にIBKR接続を確立、終了時に切断
    """
    logger = get_logger()
    app_state['logger'] = logger

    logger.info('=' * 60)
    logger.info('FastAPI Dashboard Starting...')
    logger.info(f'Mode: {"Mock" if config.USE_MOCK_DATA else "Real"}')
    logger.info('=' * 60)

    # 既存モジュールをインポート
    if config.USE_MOCK_DATA:
        from mock_data import MockIBKRConnection, MockMarketDataManager
        from position import PositionManager

        logger.info('🎭 モックモードで起動中...')

        # モック接続を確立
        conn = MockIBKRConnection(use_paper=config.USE_PAPER_ACCOUNT)
        conn.connect()

        app_state['ibkr_connection'] = conn
        app_state['market_data_manager'] = MockMarketDataManager(conn.get_ib())
        app_state['position_manager'] = PositionManager()

        logger.info('✓ モック接続確立')

    else:
        from backend.services.ibkr_service import IBKRService
        from position import PositionManager

        logger.info('📡 リアルモードで起動中...')

        # 新しいIBKRServiceを使用（専用スレッドでイベントループ競合を回避）
        service = IBKRService.get_instance()
        try:
            service.start(
                host=config.TWS_HOST,
                port=config.TWS_PORT,
                client_id=config.CLIENT_ID
            )
            logger.info('✓ IBKR接続確立（専用スレッド）')
        except Exception as e:
            logger.warning(f'⚠️ IBKR接続失敗（TWSが起動しているか確認してください）: {e}')
            logger.warning(f'   接続先: {config.TWS_HOST}:{config.TWS_PORT}')
            logger.warning('   サーバーは起動しますが、IBKRデータは利用できません')

        app_state['ibkr_service'] = service
        app_state['position_manager'] = PositionManager()

        # ストリーミングとWebSocketブロードキャストを開始
        if service.is_connected:
            try:
                await service.setup_streaming()
                asyncio.create_task(_broadcast_real_time_data(service))
                logger.info('✓ リアルタイムストリーミング開始')
            except Exception as e:
                logger.warning(f'⚠️ ストリーミング開始失敗: {e}')

        # 自動売買スケジューラーを起動（AUTO_EXECUTE=True かつ IBKR接続済みの場合）
        if config.AUTO_EXECUTE and service.is_connected:
            _setup_scheduler(service)
            logger.info(f'✓ 自動売買スケジューラー開始（月曜 {config.ENTRY_TIME} ET）')
        elif config.AUTO_EXECUTE and not service.is_connected:
            logger.warning('⚠️ AUTO_EXECUTE=True だが IBKR未接続のためスケジューラーを起動しません')

    logger.info('FastAPI Dashboard Ready')
    logger.info('=' * 60)

    yield  # アプリケーション実行

    # シャットダウン処理
    logger.info('FastAPI Dashboard Shutting down...')

    # スケジューラー停止
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info('✓ スケジューラー停止')

    if config.USE_MOCK_DATA:
        if app_state.get('ibkr_connection'):
            app_state['ibkr_connection'].disconnect()
    else:
        if app_state.get('ibkr_service'):
            app_state['ibkr_service'].stop()

    logger.info('✓ Shutdown complete')


# FastAPIアプリケーション初期化
app = FastAPI(
    title="SPY Credit Spread Dashboard API",
    description="Bull Put Credit Spread 自動取引システムのバックエンドAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定（開発環境：localhost全ポート許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ルーター登録
from routers import account, market, options, positions, fx, chat, strategy, trades
app.include_router(account.router, prefix="/api", tags=["Account"])
app.include_router(market.router, prefix="/api", tags=["Market"])
app.include_router(options.router, prefix="/api", tags=["Options"])
app.include_router(positions.router, prefix="/api", tags=["Positions"])
app.include_router(fx.router, prefix="/api", tags=["FX"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(strategy.router, prefix="/api", tags=["Strategy"])
app.include_router(trades.router, prefix="/api", tags=["Trades"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "SPY Credit Spread Dashboard API",
        "version": "1.0.0",
        "mode": "mock" if config.USE_MOCK_DATA else "real"
    }


@app.get("/api/health")
async def health_check():
    """
    ヘルスチェック
    """
    if config.USE_MOCK_DATA:
        conn = app_state.get('ibkr_connection')
        is_connected = conn.is_connected() if conn else False
    else:
        service = app_state.get('ibkr_service')
        is_connected = service.is_connected if service else False

    return {
        "status": "ok",
        "ibkr_connected": is_connected,
        "mode": "mock" if config.USE_MOCK_DATA else "real",
        "auto_execute": config.AUTO_EXECUTE,
        "scheduler_running": scheduler.running,
        "timestamp": datetime.now(pytz.UTC).isoformat()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント
    リアルタイム価格配信用
    """
    from ws.manager import manager
    import json

    await manager.connect(websocket)

    try:
        while True:
            # クライアントからのメッセージを受信
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get('action')
            channel = message.get('channel', 'all')

            if action == 'subscribe':
                await manager.subscribe(websocket, channel)
                await manager.send_personal_message({
                    "type": "subscribed",
                    "channel": channel
                }, websocket)

            elif action == 'unsubscribe':
                await manager.unsubscribe(websocket, channel)
                await manager.send_personal_message({
                    "type": "unsubscribed",
                    "channel": channel
                }, websocket)

            elif action == 'ping':
                await manager.send_personal_message({
                    "type": "pong"
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
