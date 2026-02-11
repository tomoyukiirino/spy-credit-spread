# Phase C Browser Test Checklist

This checklist helps verify the WebSocket integration visually in the browser.

## Prerequisites

✅ Backend running: `http://localhost:8000`
✅ Frontend running: `http://localhost:3000`

---

## Test 1: WebSocket Connection

1. Open `http://localhost:3000` in your browser
2. Open DevTools (F12 or Cmd+Option+I on Mac)
3. Go to the **Console** tab
4. Look for WebSocket connection messages:

   **Expected Output:**
   ```
   [WebSocket] Connecting to ws://localhost:8000/ws
   [WebSocket] Connected successfully
   [WebSocket] Subscribing to channel: spy
   [WebSocket] Subscribing to channel: fx
   ```

   ✅ PASS if you see connection and subscription messages
   ❌ FAIL if you see connection errors

---

## Test 2: Network Tab Verification

1. In DevTools, go to the **Network** tab
2. Filter by "WS" (WebSocket)
3. Click on the `ws` connection
4. Go to the **Messages** tab

   **Expected:**
   - You should see subscription confirmation messages
   - You may see ping/pong messages (heartbeat)

   ✅ PASS if WebSocket connection is shown and messages are visible
   ❌ FAIL if no WebSocket connection appears

---

## Test 3: Live Indicator

1. Look at the **SPY Price Card** on the dashboard
2. Check the top-right corner of the card

   **Expected:**
   - Green "Live" text with a pulsing Wifi icon
   - The icon should pulse/animate

   ✅ PASS if "Live" indicator is visible and animated
   ⚠️  PARTIAL if indicator appears but doesn't pulse
   ❌ FAIL if no "Live" indicator

---

## Test 4: StatusBar Display

1. Look at the bottom of the page (StatusBar)
2. Check for SPY price and FX rate display

   **Expected:**
   - SPY price should be displayed (e.g., "$624.50")
   - Time should be displayed and updating every second

   ✅ PASS if both values are shown
   ❌ FAIL if values are missing or show "-"

---

## Test 5: Page Navigation

1. Click on "オプション取引" in the sidebar
2. Verify the options page loads
3. Check the StatusBar at the bottom

   **Expected:**
   - Options page loads successfully
   - StatusBar still shows SPY price and FX rate
   - No errors in console

   ✅ PASS if navigation works and StatusBar persists
   ❌ FAIL if errors occur or StatusBar disappears

---

## Test 6: Console Error Check

1. In DevTools Console, look for any errors (red text)
2. Common errors to ignore:
   - CORS warnings (if any)
   - HMR (Hot Module Reload) messages

   **Expected:**
   - No WebSocket connection errors
   - No React rendering errors
   - No 404 or 500 API errors

   ✅ PASS if no critical errors
   ⚠️  PARTIAL if minor warnings only
   ❌ FAIL if connection or rendering errors

---

## Test 7: Price Flash Animation (When Backend Broadcasts Enabled)

**Note**: This test requires background broadcast tasks to be running.

1. Watch the main SPY price number on the dashboard
2. Wait for price to change

   **Expected:**
   - When price increases: Brief green background flash (500ms)
   - When price decreases: Brief red background flash (500ms)
   - Flash should be smooth and not jarring

   ✅ PASS if animations trigger correctly
   ⏸️  SKIP if broadcast tasks not enabled
   ❌ FAIL if no animation or wrong colors

---

## Test 8: Fallback Behavior (Optional)

1. Stop the backend server (`Ctrl+C` in terminal)
2. Observe the frontend

   **Expected:**
   - "Live" indicator should disappear
   - After a few seconds, you might see connection retry messages
   - Page should still function with polling fallback
   - No crash or blank page

   ✅ PASS if graceful fallback
   ❌ FAIL if page crashes or becomes unusable

3. Restart the backend server
4. Refresh the page

   **Expected:**
   - "Live" indicator returns
   - WebSocket reconnects

   ✅ PASS if reconnection works

---

## Quick Visual Reference

### ✅ Healthy Dashboard
```
┌─────────────────────────────────────────┐
│ Header [IBKR: Connected] [Mode: Mock]  │
├─────┬───────────────────────────────────┤
│ 📊  │ Account Info    │ SPY Price      │
│ 🎯  │                 │ [$624.50] 🟢Live│
│ 📈  │                 │ Strategy        │
└─────┴───────────────────────────────────┘
│ 💹 SPY: $624.50 | 💴 USD/JPY: ¥152.34 │ 🕐 20:45:23
```

### Console Output (Healthy)
```javascript
[WebSocket] Connecting to ws://localhost:8000/ws
[WebSocket] Connected successfully
[WebSocket] Subscribing to channel: spy
[WebSocket] Subscribing to channel: fx
```

### Network Tab (Messages)
```
{"type":"subscribed","channel":"spy"}
{"type":"subscribed","channel":"fx"}
{"action":"ping"}
{"type":"pong"}
```

---

## Summary

After completing all tests, you should have:

- ✅ WebSocket connection established
- ✅ Live indicator showing
- ✅ SPY price displayed
- ✅ FX rate displayed (if available)
- ✅ Navigation working between pages
- ✅ No critical console errors
- ⏸️ Price flash animations (when broadcasts enabled)
- ✅ Graceful fallback behavior

---

## Troubleshooting

### "Live" indicator not showing
- Check DevTools Console for WebSocket errors
- Verify backend is running on port 8000
- Check Network tab for WebSocket connection

### Prices showing as "-"
- Initial data fetch may have failed
- Check Network tab for API call errors
- Verify backend APIs are responding (http://localhost:8000/api/health)

### WebSocket connection keeps failing
- Ensure backend is running
- Check firewall settings
- Try hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

### No price flash animations
- Normal if broadcast background tasks are not enabled
- Verify `broadcast_spy_price()` is running in backend
- Check if prices are actually changing

---

**Happy Testing!** 🧪✨
