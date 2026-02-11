"""
簡易接続テスト: マーケットデータ取得の確認
"""

from ib_insync import *
import time

# 接続
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=2)

print("✓ 接続成功")
print(f"口座: {ib.managedAccounts()}")

# マーケットデータタイプを設定
# 1 = Live, 2 = Frozen, 3 = Delayed, 4 = Delayed-Frozen
print("\n遅延データモードに設定...")
ib.reqMarketDataType(3)  # Delayed

# SPY株式コントラクト
spy = Stock('SPY', 'SMART', 'USD')
print(f"\nSPYコントラクト作成: {spy}")

# コントラクトを検証
print("コントラクトを検証中...")
contracts = ib.qualifyContracts(spy)
if contracts:
    spy = contracts[0]
    print(f"✓ 検証成功: {spy}")
else:
    print("✗ コントラクト検証失敗")
    ib.disconnect()
    exit(1)

# マーケットデータをリクエスト（遅延データ）
print("\nマーケットデータをリクエスト中...")
ticker = ib.reqMktData(spy, '', False, False)

# データが返ってくるまで待機
print("データ受信を待機中...")
for i in range(10):
    ib.sleep(1)
    print(f"  {i+1}秒: Last={ticker.last}, Bid={ticker.bid}, Ask={ticker.ask}, Close={ticker.close}")

    # データが取得できたら表示
    if (ticker.last and ticker.last > 0) or (ticker.close and ticker.close > 0):
        print("\n✓ マーケットデータ取得成功!")
        print(f"  Last: ${ticker.last if ticker.last else 'N/A'}")
        print(f"  Close: ${ticker.close if ticker.close else 'N/A'}")
        print(f"  Bid: ${ticker.bid if ticker.bid else 'N/A'}")
        print(f"  Ask: ${ticker.ask if ticker.ask else 'N/A'}")
        break
else:
    print("\n⚠ マーケットデータを取得できませんでした")
    print("TWSの Market Data Subscriptions を確認してください")

# クリーンアップ
ib.cancelMktData(spy)
ib.disconnect()
print("\n切断完了")
