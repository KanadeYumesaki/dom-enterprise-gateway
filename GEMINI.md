# Project: DOM Enterprise Gateway (PoC / P0 Core Chat)

## 1. Project Overview

- プロジェクト名: **DOM Enterprise Gateway**
- 目的:
  - エンタープライズ向けの **ガバナンス付き LLM ゲートウェイ** を PoC として構築する。
  - マルチエージェント（Domain Orchestrator Meister / Helper / Research / Answer）と
    長期メモリ (Structured / Episodic) ＋ Ephemeral RAG (セッション限定ベクトル検索) を組み合わせ、
    - 人間に近い文脈保持
    - 説明責任（参照ソース・メモリ・ポリシーのトレース）
    を両立する。
- フェーズ:
  - 本 GKIRO プロジェクトは **P0 = PoC Core Chat** を対象とする。
  - P1 以降（本番）は仕様書側に (P1) として定義済みだが、本ワークフローでは実装対象外。

## 2. Tech Stack / Constraints

- Backend:
  - 言語: **Python 3.12**
  - フレームワーク: FastAPI
  - LLM / RAG: **LangChain v1** (Runnable / LCEL / RAG / Agent)
  - ORM / Migration: SQLAlchemy + Alembic
- Frontend:
  - Angular (LTS)
  - i18n: Angular i18n または ngx-translate
- Infra:
  - PostgreSQL 15+（pgvector 拡張 or 対応）
  - Redis（Ephemeral Session Store / ロック / キャッシュ）
  - Docker / docker-compose（PoC 環境を一発起動できること）
- LLM:
  - PoC では Gemini を Main / Helper の両方に利用する。
  - LlmClient 抽象により将来 GPT / Claude / DeepSeek 等へ差し替え可能とする。
- Auth:
  - OAuth2.0 + OIDC (Auth Code + PKCE 想定)
  - 環境変数 `INITIAL_ADMIN_EMAIL` による初期管理者ブートストラップ。

## 3. Local Spec / Knowledge Files

このプロジェクトでは、次のローカルファイルを「仕様の正」として扱うこと。

- `requirements_p0_core_chat.md`
  - 機能要件・非機能要件・テーブル定義・セキュリティ・運用要件。
  - P0 の PoC 範囲を明示し、(P1) 以降は将来拡張として記載。
- `help_content_outline.md`
  - ヘルプセンター / オンボーディング / UX 周りの構成と見出し。
- `DOM Enterprise Gateway.txt`
  - プロジェクト全体の引き継ぎメモ。
  - マルチエージェント構成、DOM / Meister の役割、LangChain v1 前提などの設計思想。

> Kiro コマンド（/kiro:steering, /kiro:spec-*）を実行する際は、  
> 必要に応じて `@requirements_p0_core_chat.md` / `@help_content_outline.md` / `@"DOM Enterprise Gateway.txt"` を読み込むこと。

## 4. Coding & Design Guidelines (プロジェクト固有)

- 言語:
  - **内部思考は英語で行ってよいが、生成する Markdown / コードコメント / 要件・設計ドキュメントは日本語で書く**。
- 例外処理:
  - `except Exception: pass` のような例外握りつぶしは禁止。
  - ネットワーク / LLM / DB / ファイルI/O / 認証エラーなど、想定される例外はカテゴリごとにハンドリングし、
    適切なログ・ユーザー向けメッセージ・HTTP ステータスを返す。
- コメント規約:
  - すべてのクラス / メソッド / 関数に対して docstring を付与し、
    - 引数
    - 戻り値
    - どんな目的の機能か
    を **初学者にも分かる具体的な日本語** で記載する。
- データベース:
  - Alembic でマイグレーション管理。DB 作り直し前提の破壊的変更は禁止。
  - 将来の拡張に備え、カラム削除や名前変更は「追加 → 移行 → 後日削除」で段階的に行う。
- Docker:
  - `docker-compose up` で Backend / Frontend / DB / Redis 一式が起動する構成を目指す。
  - 本番想定のイメージ設計も意識しつつ、PoC では開発しやすさを優先。

---

# AI-DLC and Spec-Driven Development

Kiro-style Spec Driven Development implementation on AI-DLC (AI Development Life Cycle)

## Project Context

### Paths
- Steering: `.kiro/steering/`
- Specs: `.kiro/specs/`

### Steering vs Specification

**Steering** (`.kiro/steering/`) - Guide AI with project-wide rules and context  
**Specs** (`.kiro/specs/`) - Formalize development process for individual features

### Active Specifications
- Check `.kiro/specs/` for active specifications
- Use `/kiro:spec-status [feature-name]` to check progress

## Development Guidelines
- Think in English, generate responses in Japanese.  
  All Markdown content written to project files (e.g., requirements.md, design.md, tasks.md, research.md, validation reports)
  MUST be written in Japanese (this spec's target language).

## Minimal Workflow
- Phase 0 (optional): `/kiro:steering`, `/kiro:steering-custom`
- Phase 1 (Specification):
  - `/kiro:spec-init "description"`
  - `/kiro:spec-requirements {feature}`
  - `/kiro:validate-gap {feature}` (optional: for existing codebase)
  - `/kiro:spec-design {feature} [-y]`
  - `/kiro:validate-design {feature}` (optional: design review)
  - `/kiro:spec-tasks {feature} [-y]`
- Phase 2 (Implementation): `/kiro:spec-impl {feature} [tasks]`
  - `/kiro:validate-impl {feature}` (optional: after implementation)
- Progress check: `/kiro:spec-status {feature}` (use anytime)

## Development Rules
- 3-phase approval workflow: Requirements → Design → Tasks → Implementation
- Human review required each phase; use `-y` only for intentional fast-track
- Keep steering current and verify alignment with `/kiro:spec-status`
- Follow the user's instructions precisely, and within that scope act autonomously:
  gather the necessary context and complete the requested work end-to-end in this run,
  asking questions only when essential information is missing or the instructions are critically ambiguous.

## Steering Configuration
- Load entire `.kiro/steering/` as project memory.
- Default files: `product.md`, `tech.md`, `structure.md`.
- Custom files are supported (managed via `/kiro:steering-custom`).
