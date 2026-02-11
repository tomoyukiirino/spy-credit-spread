"""
Claude チャットAPIルーター
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter()


class Message(BaseModel):
    """メッセージモデル"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """チャットリクエスト"""
    message: str
    conversation_history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_claude(request: ChatRequest):
    """
    Claude APIを使用してチャット

    Args:
        request: チャットリクエスト（メッセージと会話履歴）

    Returns:
        Claude からのレスポンス
    """
    try:
        # Anthropic API キーの確認
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            # API キーがない場合はモックレスポンス
            return ChatResponse(
                response=f"申し訳ございません。現在、Claude APIの設定が完了していません。\n\n"
                         f"あなたのメッセージ: 「{request.message}」\n\n"
                         f"💡 ヒント: ANTHROPIC_API_KEY環境変数を設定すると、実際のClaude APIに接続できます。"
            )

        # Anthropic SDK を使用
        try:
            from anthropic import Anthropic
        except ImportError:
            return ChatResponse(
                response="Anthropic SDKがインストールされていません。\n\n"
                         "`pip install anthropic` を実行してください。"
            )

        client = Anthropic(api_key=api_key)

        # 会話履歴を構築
        messages = []
        for msg in request.conversation_history:
            if msg.role in ['user', 'assistant']:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # 新しいメッセージを追加
        messages.append({
            "role": "user",
            "content": request.message
        })

        # システムプロンプト
        system_prompt = """あなたはSPYクレジットスプレッド取引の専門アドバイザーです。

以下のトピックについてユーザーをサポートしてください:
- SPY（S&P 500 ETF）のBull Put Credit Spread戦略
- オプション取引の基礎（デルタ、IV、DTE等のGreeks）
- リスク管理とポジションサイジング
- 税務申告（日本の雑所得）
- 為替レート（USD/JPY）の影響
- IBKR（Interactive Brokers）の使い方

回答は:
- 簡潔で分かりやすく
- 日本語で
- 必要に応じて具体例を示す
- リスクについても正直に説明する

ユーザーの現在の設定:
- 元金: $10,000 USD
- スプレッド幅: $5
- 目標デルタ: 0.20 (勝率約80%)
- リスク/トレード: 資金の8%
- DTE範囲: 1〜7日
"""

        # Claude API呼び出し
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",  # 最新のSonnet 4.5
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        # レスポンスを抽出
        assistant_message = response.content[0].text

        return ChatResponse(response=assistant_message)

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get response from Claude: {str(e)}"
        )
