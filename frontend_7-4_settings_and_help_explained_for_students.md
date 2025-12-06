# Task 7.4: Settings & Help UI と Onboarding の使い方（やさしい解説）

## 何ができるようになった？
- `/settings` 画面で **テーマ（ライト/ダーク）・言語（日本語/英語）・文字サイズ（小/中/大）** を自分好みに変えられます。  
  ついでに「オンボーディングを見た / スキップした」フラグもここで確認できます。
- `/help` 画面で **ヘルプ記事の一覧と本文** を左右に分けて閲覧できます。URL の `?section=...` で最初に開く記事を指定することもできます。
- OnboardingService が初回ログイン時に軽い案内ダイアログを出します。閉じると、Backend の `/api/user/settings` に「見た/スキップ」状態が保存されます。

## 画面の動き
### Settings 画面
1. 開くとサーバーから現在の設定を読み込み、フォームに反映します。
2. 値を変えて「保存する」を押すと、**変更された項目だけ** を送信して保存します。
3. 保存後は全画面共通の UI 状態(StateService)にも即反映されます。

### Help 画面
1. 開くと `/api/help/content` からヘルプ記事をまとめて取得します。
2. 左のリストでタイトルを選ぶと、右側に本文が表示されます。  
   ※ いまはプレーンテキスト表示。Markdown 対応は P1 TODO。
3. URL に `?section=記事ID` を付けると、その記事が最初に選ばれます。

### Onboarding の流れ
1. MainLayout が起動時にユーザー設定を取得します。
2. `hasSeenOnboarding` と `onboardingSkipped` が両方 false の場合だけダイアログを表示します。
3. 「始める」→ `hasSeenOnboarding=true` を保存 / 「あとで」→ `onboardingSkipped=true` を保存。

## 便利なコマンド例（WSL Ubuntu 側で実行）
```bash
# WSL Ubuntu 側
cd ~/work/dom-enterprise-gateway/frontend
npm install
npm start
```
ブラウザで `http://localhost:4200/settings` や `/help` を開いて動きを確認できます。

## 使う API
- ユーザー設定: `GET /api/user/settings`, `POST /api/user/settings`
- ヘルプ記事: `GET /api/help/content`

### ちょっとした注意
- 認証が切れていると 401 が返り、ログイン画面へ誘導されます。
- ネットワークエラーや 5xx のときはエラーバナー/スナックバーが出ます。再読み込みしてみてください。
