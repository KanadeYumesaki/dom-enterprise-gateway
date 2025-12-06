# DOM Enterprise Gateway フロントエンド概要 (自動生成テンプレート)

- 生成日時: 2025-12-06
- 生成モデル: GPT-5 (Codex, Antigravity 拡張)

## このプロジェクトでできること
- 社内向けチャット / RAG / ナレッジ閲覧を Angular 20 + SSR + Zoneless で提供します。
- `/chat`, `/knowledge`, `/settings`, `/help` などの画面があります。

## 使い方 (WSL2 Ubuntu の例)
```bash
cd ~/work/dom-enterprise-gateway/frontend
npm install
npm start
```

## 安全に使うための注意
- 秘密情報は `.env` やクラウドのシークレット管理に入れ、コードへハードコードしないでください。
- ブラウザで開く前に Backend (`/api/*`) が起動していることを確認してください。
