#!/usr/bin/env python3
"""
Manual WebSocket Broadcast Test
Connects to the backend WebSocket and manually triggers price updates
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def manual_broadcast_test():
    """Test by subscribing and then manually triggering API calls that should update prices"""

    print("=" * 60)
    print("Phase C Manual Broadcast Test")
    print("=" * 60)

    # Connect to WebSocket
    session = aiohttp.ClientSession()
    ws_url = "http://localhost:8000/ws"

    try:
        async with session.ws_connect(ws_url) as ws:
            print("✅ WebSocket connected\n")

            # Subscribe to SPY channel
            await ws.send_json({"action": "subscribe", "channel": "spy"})
            msg = await ws.receive_json()
            print(f"Subscription response: {msg}\n")

            # Subscribe to FX channel
            await ws.send_json({"action": "subscribe", "channel": "fx"})
            msg = await ws.receive_json()
            print(f"Subscription response: {msg}\n")

            print("Frontend should now be connected. Check the browser:")
            print("1. Open http://localhost:3000")
            print("2. Check browser DevTools console for WebSocket messages")
            print("3. Verify 'Live' indicator appears on SPY price card")
            print("4. Watch for price flash animations (green/red)")
            print("\nPress Ctrl+C to stop...\n")

            # Keep connection alive and listen for messages
            count = 0
            while True:
                try:
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
                    count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    if msg.get("type") == "spy_price":
                        price = msg.get("data", {}).get("last")
                        print(f"[{timestamp}] ({count}) SPY Price: ${price:.2f}")
                    elif msg.get("type") == "fx_rate":
                        rate = msg.get("data", {}).get("usd_jpy")
                        print(f"[{timestamp}] ({count}) FX Rate: ¥{rate:.2f}")
                    elif msg.get("type") == "pong":
                        print(f"[{timestamp}] Heartbeat: pong")

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await ws.send_json({"action": "ping"})

    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(manual_broadcast_test())
