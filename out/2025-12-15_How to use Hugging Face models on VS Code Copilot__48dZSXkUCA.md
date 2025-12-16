# How to use Hugging Face models on VS Code Copilot

- Channel: HuggingFace
- Published: 2025-12-15T23:00:53Z
- URL: https://www.youtube.com/watch?v=_48dZSXkUCA

---

概要（3-5行）
- Hugging FaceのCelinaが、VS CodeのCopilot Chat内でHugging Faceのオープンウェイトモデルを使う方法をデモ。Hugging Face Inference Providers（複数のインフラ提供者でモデル推論を実行するサービス）と、Marketplaceの拡張「Hugging Face Provider for GitHub Copilot」を使う流れを解説。
- 拡張の導入は簡単で、APIトークンを登録してモデルを追加、プロバイダや「fastest／cheapest」で絞ってCopilot Chat内で直接利用できる。
- 実例としてGLMやDeepSeqを使い、ローカルエージェントで実装を生成・反復しながら実務に組み込む様子を見せ、コスト感（約$0.20〜$0.30）や無料クレジット、拡張がOSSである点も強調。

主要トピック（箇条書き）
- Hugging Face Inference Providersの概要（複数プロバイダ、オープンウェイトモデルへの単一API）
- VS Code向け拡張「Hugging Face Provider for GitHub Copilot」の紹介
- Bring Your Own Key（BYOK）機能によるモデル持ち込み
- インストール／設定手順（APIトークン、権限設定）
- モデル選択のフィルタ（プロバイダ指定、fastest／cheapestモード）
- 実演：GLMを使ったコード実装の自動生成と反復ワークフロー
- コスト感、無料クレジット、Proプラン
- 拡張はオープンソースで頻繁にアップデート可能／クラウド・ローカル双方のエージェントで利用可

重要ポイント（番号付き、可能ならタイムスタンプを含めて）
1. Inference Providersの意義（約0:30）  
   - 複数の商用推論プロバイダ（例：Cerebras、Fireworks等）でオープンモデルを動かせ、ベンダーに縛られず速度・コスト・可用性を選べる。Hugging Face側で余分なマークアップは加えない。  

2. 拡張の入手と基本操作（約2:00）  
   - Marketplaceで「Hugging Face Provider for GitHub Copilot」をインストール → Copilot Chatのモデルピッカー→ Manage models → Add models → Hugging Faceを選択。  

3. APIトークンと権限設定（約2:30）  
   - Hugging Faceのアクセストークン（API key）を入力し、「inference providers」権限を与える必要がある。  

4. モデル選択とフィルタ（約3:15）  
   - プロバイダで絞る、または「fastest（最高スループット）」／「cheapest（最安）」モードで自動的に最適プロバイダを選べる。  

5. 実演：Copilot内での実装生成（約4:00）  
   - GLMやDeepSeqを選び、GitHub IssueのURLやコンテキストを渡して実装を生成。ローカルエージェントでステップごとに確認・修正できるためワークフローがスムーズ。  

6. コストとクレジット（約6:00）  
   - 実演のセッションは約$0.20〜$0.30（安価寄り）。無料アカウントで試せるクレジットあり。Pro契約で追加クレジット。従量課金。  

7. 拡張の利点と互換性（約7:00）  
   - 拡張が独立しているため頻繁に機能追加・バグ修正が可能。OpenAI互換のAPI実装でVS Code Copilot Chatへの統合が容易。クラウドエージェントとローカルエージェントの両方で利用可能。  

アクション項目 / 役立つTips
- インストール／初期設定手順：
  1. VS Code Marketplaceで「Hugging Face Provider for GitHub Copilot」をインストール。  
  2. Hugging Faceアカウントからアクセストークンを取得し、「inference providers」権限を付与。  
  3. Copilot Chat > Model picker > Manage models > Add models > Hugging Face を選択してトークンを入力。  

- 効率化のコツ：
  - まず「cheapest」でコスト感を掴み、必要性能があるなら「fastest」に切り替える。  
  - プロバイダフィルタで特定プロバイダがサポートするモデルだけを表示可能。  
  - ローカルエージェントで小刻みにプロンプトを調整しつつ生成物をレビューしてから最終コミットする。  
  - 拡張はOSS：不具合や欲しい機能はリポジトリへIssueやPull Requestを出して貢献可能。  
  - コストを意識して長時間の自動実行や大量推論はプロバイダと料金を確認する。  

英語TL;DR
- Hugging Face’s VS Code extension lets you use open-weight models in Copilot Chat via Hugging Face Inference Providers; install the extension, add your HF API key (inference_providers permission), then pick models and choose fastest/cheapest providers.  
- Demo shows GLM/DeepSeq for code tasks, cheap per-session cost (~$0.20–$0.30), works with local/cloud agents, and the extension is open-source for quick updates.
