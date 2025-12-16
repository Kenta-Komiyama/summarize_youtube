# Claude Code can generate AI images for your apps/websites with 🤗 Hugging Face

- Channel: HuggingFace
- Published: 2025-12-16T14:05:02Z
- URL: https://www.youtube.com/watch?v=tuWoCXjUSs8

---

概要（3-5行）
- 動画は、Hugging Faceの「Space」をMCPツールとして登録し、Cloud Code（タイトルではClaude Code）を使ってウェブサイト向けのAI生成画像をオンザフライで作る手順を実演しています。  
- 操作は「Space名をコピー → Hugging FaceアカウントのSettings → MCPに貼付 → MCPサーバーのCLIコマンドを実行 → Cloud Codeに画像生成を指示」の流れです。  
- 最後に、生成されたAI画像を使ってランディングページが自動生成されるところまで示しています。

主要トピック（箇条書き）
- Hugging Face SpaceをMCPツールとして登録する方法
- アカウント設定内の「MCP」セクションの使い方
- MCPサーバーのインストール（ターミナルでのCLI実行）
- Cloud Code（/Claude Code）で画像生成を指示し、サイト用画像を得る流れ
- 実際にAI生成された画像でランディングページを作るデモ

重要ポイント（番号付き）
1. スペース名をコピー：使いたいHugging Face Space（デモ用のツール）の名前をまずコピーする。  
2. アカウント設定でMCPに貼付：Hugging FaceのSettings → 下部の「MCP」欄に先ほどのスペース名を貼り付けると、そのSpaceがMCPツールとして登録される。  
3. MCPサーバーのインストール（CLI実行）：動画では画面上のコマンドをコピーして端末に貼り、実行することでMCPサーバーがセットアップされる。  
4. Cloud Codeで生成を指示：MCPサーバーが整ったらCloud Code上で「ランディングページ用の画像を生成して」といった命令を出すと、AI生成画像が返ってくる。  
5. 出力の利用：生成された画像をそのままランディングページに組み込んでデモを完成させる（動画はこれを実演）。  

アクション項目 / 役立つTips
- 事前準備：Hugging Faceアカウントにログインし、利用するSpaceへのアクセス権（公開/非公開設定）を確認する。  
- 正確にコピー＆貼付：Space名を誤ると連携できないので、コピペミスに注意。  
- CLI実行時は環境確認：ターミナルでのインストールには適切な権限と依存ツール（Pythonやnpm等）が必要な場合があるため、エラーメッセージを確認する。  
- プロンプト調整：生成画像の見た目は指示文（プロンプト）で大きく変わる。用途に合わせて具体的に書く。  
- コストと利用規約：API利用や生成画像の商用利用については課金やライセンス条件を事前に確認する。  
- テスト→本番：まず小さなリクエストで動作確認し、レイテンシやレート制限を把握してから本番組み込みを行う。

英語 TL;DR
Register a Hugging Face Space as an MCP tool, run the provided CLI to install the MCP server, then use Cloud Code to request AI-generated images and embed them into your landing page.
