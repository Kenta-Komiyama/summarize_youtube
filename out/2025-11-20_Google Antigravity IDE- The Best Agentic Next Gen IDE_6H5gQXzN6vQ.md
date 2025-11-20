# Google Antigravity IDE- The Best Agentic Next Gen IDE

- Channel: Krish Naik
- Published: 2025-11-20T06:06:21Z
- URL: https://www.youtube.com/watch?v=6H5gQXzN6vQ

---

概要（3-5行）
- Googleが発表した次世代IDE「Google Anti-Gravity」をKrishが初見で試したレビュー。主に「エージェント駆動（agentic）開発」を前提にした機能紹介と、実際にFastAPIの簡単な電卓アプリをエージェントに作らせるデモを行っている。  
- 無料プランでGemini 3 Pro等のモデルが使える点を強調し、エージェント管理（並列タスク、バックグラウンド実行、計画→実行）やブラウザ連携のフロントエンドプレビューなどが主要機能。  
- UIはVS Codeライクだが違いもあり、まだ荒削りな部分や一部統合（例：MCP）は見当たらないという印象。

主要トピック（箇条書き）
- Anti-Gravityの位置付け：次世代AI IDE、CursorやVS Codeの競合  
- 主要ユースケース：Professional / Front-end / Full-stack（各々に合わせた機能）  
- 無料プランの内容：Gemini 3 Pro、Cloud SONET 4.5、GPT OSS 等を含む（個人向けゼロドル）  
- エージェントマネージャー：複数エージェントの起動・監視・バックグラウンド処理  
- ブラウザ・イン・ザ・ループ：コーディング中にUIの可視化・反映が可能  
- 実演：新規プロジェクト作成→FastAPIで電卓APIをエージェントに生成・実行  
- キーボードショートカットやCLI連携（AGY）などの開発体験

重要ポイント（番号付き、可能ならタイムスタンプを含めて）
1. (導入〜初見) Anti-Gravityは「エージェント中心のIDE」で、バックグラウンドエージェントがタスクを計画・実行し、コンテキスト切り替えを減らす設計。  
2. (ユースケース説明) Professional, Front-end, Full-stackの3大ユースケースに対応。フロントは「ブラウザ連携でUI確認」が可能、フルスタックは検証やユーザー向けアーティファクト作成を重視。  
3. (料金・モデル) 個人向けは無料で提供（動画内では「$0/月」）かつGemini 3 ProやCloud SONET 4.5、GPT OSSが使えると説明。無制限のタブ補完やコマンドリクエスト、寛容なレート制限が利点。  
4. (セットアップ) インストーラ（exe）から起動、Googleでサインイン。初回にテーマ、開発モード（agent-driven / agent-assisted など）、キーボードバインドを選択。CLIツール（AGY）も導入される。  
5. (UIと既存エディタ比較) 見た目はVS Codeに近いが情報量や使い勝手は異なる。Cursorのような右側のチャット/エージェントパネルを持つ点は類似。UIはまだ改善の余地あり。  
6. (エージェント機能) エージェントは「Planning（計画）」と「Execute（実行）」モードを持ち、深い調査や簡単なタスクの自動実行が可能。Ctrl+Eでエージェントマネージャーを開ける（動画内ショートカット）。  
7. (コーディング支援) ファイル内編集、推奨拡張のインストール（例：Python拡張）、実行ターミナルの統合、コミット機能などIDEとしての基本機能は備える。Ctrl+Iでインライン編集、Ctrl+L等が紹介された。  
8. (実演デモ) 新規フォルダ作成→venv初期化→依存（fastapi）追加→「電卓APIを作る」命令でエージェントが実装計画を立て、main.pyを編集し、実行まで数分で完了。  
9. (制約と注意点) MCP等既存のクラウド統合は見当たらず、UIの完成度はまだ。長年のVS Codeユーザーは違和感を覚える可能性あり。開発環境（Python、APIキーなど）の準備は必要。

アクション項目 / 役立つTips
- まずは無料アカウントで触ってみる：個人向けはゼロ円なので手を出しやすい。  
- サインイン後の初期設定で「agent-assisted」を選ぶと人間の判断を保ちながらAI支援を受けられる（初心者は安全）。  
- 必須準備：Python環境、必要ならOpenAI等のAPIキー（プロジェクト依存）、推奨Python拡張をインストールしておく。  
- ショートカットを覚える：Ctrl+E（エージェントマネージャー）、Ctrl+I（インライン編集）など、エージェント運用がスムーズになる。  
- CLIツール（AGY）が入るのでローカルから速くプロジェクトを開ける。  
- フロントエンド作業には「browser-in-the-loop」を活用して即時プレビューを確認する。  
- 小規模なタスクやプロトタイプ（RAGアプリやAPI）を試すには向いているが、既存のワークフローや特定のクラウド統合が必要なら検討が必要。  
- セキュリティ上の注意：自動でコードやバックグラウンドエージェントに機密情報を渡さないよう、allow-listやレビュー設定を確認する。

英語 TL;DR (1–2 lines)
Google Anti-Gravity is a free, agent-centric IDE from Google (uses Gemini 3 Pro) that speeds development with background agents, browser-in-the-loop previews, and built-in CLI — promising for rapid prototyping though the UI and some integrations still need polish.
