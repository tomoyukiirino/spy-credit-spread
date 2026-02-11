# SPY Credit Spread Dashboard - Frontend

Next.js + TypeScript + Tailwind CSS で構築されたダークモードダッシュボード

## セットアップ

### 1. 依存関係のインストール

```bash
npm install
```

### 2. 環境変数の設定

`.env.local` ファイルを編集:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. 開発サーバーの起動

```bash
npm run dev
```

ブラウザで http://localhost:3000 を開く

## バックエンドとの連携

フロントエンドを起動する前に、バックエンド（FastAPI）を起動する必要があります:

```bash
# backend/ ディレクトリで
cd ../backend
python main.py
```

バックエンドは http://localhost:8000 で起動します。

## 主な機能

### 実装済み
- ✅ ダークモードUI
- ✅ 口座情報表示
- ✅ SPY価格表示
- ✅ 戦略パラメータ表示
- ✅ リスク管理ダッシュボード
- ✅ リアルタイムデータ更新（30秒ごと）
- ✅ レスポンシブデザイン

### 今後の実装予定
- ⏳ ポジション一覧テーブル
- ⏳ スプレッド候補の表示と選択
- ⏳ 取引履歴ページ
- ⏳ 税務レポートページ
- ⏳ Claude API チャット機能
- ⏳ WebSocket リアルタイム更新
- ⏳ チャート表示（Recharts）

## ディレクトリ構造

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # ルートレイアウト
│   │   ├── page.tsx         # ダッシュボードページ
│   │   └── globals.css      # グローバルスタイル
│   ├── components/          # Reactコンポーネント
│   │   ├── layout/          # レイアウトコンポーネント
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── StatusBar.tsx
│   │   └── dashboard/       # ダッシュボードコンポーネント
│   │       ├── AccountCard.tsx
│   │       ├── SpyPriceCard.tsx
│   │       └── StrategyCard.tsx
│   ├── lib/                 # ユーティリティ
│   │   ├── api.ts          # FastAPI クライアント
│   │   └── formatters.ts   # フォーマット関数
│   └── types/              # TypeScript型定義
│       └── index.ts
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 技術スタック

- **Next.js 14** - React フレームワーク
- **TypeScript** - 型安全性
- **Tailwind CSS** - スタイリング
- **Lucide React** - アイコン
- **Recharts** - チャート（将来実装）
- **date-fns** - 日付処理

## 開発コマンド

```bash
# 開発サーバー起動
npm run dev

# プロダクションビルド
npm run build

# プロダクションサーバー起動
npm start

# Lint実行
npm run lint
```

## API エンドポイント

フロントエンドは以下のAPIエンドポイントを使用:

- `GET /api/health` - ヘルスチェック
- `GET /api/account` - 口座情報
- `GET /api/account/summary` - 詳細サマリー
- `GET /api/market/spy` - SPY価格
- `GET /api/market/vix` - VIX水準（未実装）

## トラブルシューティング

### バックエンドに接続できない

1. バックエンドが起動しているか確認
2. `.env.local` の `NEXT_PUBLIC_API_URL` が正しいか確認
3. CORS設定を確認（バックエンド側で localhost:3000 を許可）

### ビルドエラー

```bash
# node_modules を削除して再インストール
rm -rf node_modules package-lock.json
npm install
```
