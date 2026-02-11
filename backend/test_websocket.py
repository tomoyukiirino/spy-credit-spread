"""
WebSocket接続テスト
"""

import asyncio
import websockets
import json


async def test_websocket():
    """WebSocket接続をテスト"""
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected")

            # チャンネルを購読
            subscribe_msg = {
                "action": "subscribe",
                "channel": "spy"
            }
            await websocket.send(json.dumps(subscribe_msg))
            print(f"→ Sent: {subscribe_msg}")

            # レスポンスを受信
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"← Received: {data}")

            # Pingテスト
            ping_msg = {"action": "ping"}
            await websocket.send(json.dumps(ping_msg))
            print(f"→ Sent: {ping_msg}")

            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"← Received: {data}")

            print("✓ WebSocket test passed")

    except asyncio.TimeoutError:
        print("✗ WebSocket timeout")
        return False
    except Exception as e:
        print(f"✗ WebSocket error: {e}")
        return False

    return True


if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
