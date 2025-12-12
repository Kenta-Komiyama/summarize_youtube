# How to use Hugging Face 🤗 models on VS Code

- Channel: HuggingFace
- Published: 2025-12-12T10:57:39Z
- URL: https://www.youtube.com/watch?v=qgcn4jlGcko

---

概要（3–5行）
VS Code上でHugging Faceモデルを直接使う方法を実演した短いチュートリアルです。手順は、VS CodeのHugging Face拡張を入れ、Copilotの「Manage Models」からHugging Faceを追加してAPIトークンを貼るだけ。トークン作成とモデル選択（プロバイダーの速度・料金差にも注意）の流れを実演し、実際にコード生成も試しています。

主要トピック（箇条書き）
- VS CodeのExtensionsで「Hugging Face」拡張をインストールする方法
- Copilotチャット → Model Selection → Manage Models でモデルを追加する手順
- Hugging FaceのAccess Token（APIキー）作成と必要な権限設定
- モデル選択とプロバイダー（速度/価格）の違い
- モデルのプレビューとエディタでの利用例（ランディングページ生成）

重要ポイント（番号付き、推定タイムスタンプ付き）
1. (0:00–0:15) VS CodeのExtensionsで「Hugging Face」拡張を検索してインストールする。ロゴで確認。  
2. (0:15–0:30) Copilotのチャット画面で「Model Selection」→「Manage Models」を開く。  
3. (0:30–0:50) 「Add Models」からHugging Faceを選び、APIキーを入力する必要がある。  
4. (0:50–1:10) Hugging Faceサイトでプロフィール→Access Tokens→Create New Token。権限は「Make Calls to Inference Providers」を付与する。名前を付けてトークンを生成、コピーする。  
5. (1:10–1:25) トークンを貼り付けるとVS Code内にHugging Faceのモデル一覧が表示される。  
6. (1:25–1:40) モデルはプロバイダー別に「fastest」「cheapest」等があり、これは呼び出し先プロバイダーの違い（速度・料金）を示す。用途に応じて選択する。  
7. (1:40–1:55) モデルを選んでプレビュー（目のアイコン）→Copilotのモデル一覧に追加すると実際にコード生成などが可能になる。動画ではQuent 3 Coderを使ってランディングページを自動生成している。

アクション項目 / 役立つTips
- まずVS Code拡張から「Hugging Face」をインストールする。  
- Hugging FaceのAccess Tokenはプロフィール→Access Tokensで作成。必須権限は「Make Calls to Inference Providers」。  
- APIキーは取り扱い注意：リポジトリにコミットしない、環境変数やシークレットストアで管理、定期的にローテーションする。  
- プロバイダー選びはコストとレイテンシのトレードオフ（cheapest＝安いプロバイダー、fastest＝速いプロバイダー）。用途に応じて選ぶ。  
- 使う前にモデルのModel Card（性能・用途・制限）を確認する。特にコード生成用途は専用のコーダーモデルを選ぶと良い。  
- 拡張やVS Codeを最新に保つことで互換性問題を避ける。  
- 初回は小さいリクエストで出力品質とコストを確認してから本格運用する。

英語 TL;DR
Install the Hugging Face VS Code extension, create an Access Token with "Make Calls to Inference Providers", add Hugging Face under Copilot → Manage Models, pick a model/provider, and start using it in-editor.
