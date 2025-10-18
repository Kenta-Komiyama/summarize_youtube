# RAG vs Fine Tuning vs Prompt Engineering

- Channel: codebasics
- Published: 2025-10-17T13:30:07Z
- URL: https://www.youtube.com/watch?v=Q-_D_2NWECE

---

概要（3-5行）
- 動画は「Prompt Engineering」「RAG（Retrieval Augmented Generation）」「Fine-tuning」の違いを、銀行のチャットボット（遅延手数料の問い合わせ）という単純な例で解説。  
- Prompt engineeringは応答のトーン・フォーマットを整える手法、RAGは外部データベースから事実を引いて正確な回答を作る手法、Fine-tuningは過去の会話やポリシーでモデル自体を再学習して一貫性ある応答を出す手法だと整理される。  
- コスト・精度・適用場面のトレードオフ（RAGは安く正確な事実参照、Fine-tuneは高コストでブランド/ドメインに最適化）と、実運用では三者を組み合わせるのが最良、という結論。

主要トピック（箇条書き）
- 生のLLMの挙動（一般的・無個性な回答）
- Prompt engineering：スタイル/トーン/フォーマット制御
- RAG：外部データベースを参照して事実に基づく回答を生成
- Fine-tuning：過去チャット等でモデルを再学習してドメイン適応
- パラメータ効率的微調整（PEFT）：LoRA / QLoRA
- 比較（コスト、精度、用途）と実運用での組合せ

重要ポイント（番号付き、（推定）タイムスタンプ）
1. （推定 0:00）問題提起：生のLLMは一般的な応答（例：late fee "$30–$40"）しか返さず、ブランド礼節・個別情報は反映されない。  
2. （推定 0:30）Prompt engineeringの役割：質問の前に「MDFC銀行アシスタントとして丁寧に回答。わからなければ『わかりません』と答える」などの指示を入れると、トーンやフォーマットが改善される（ただし事実の正確性は変わらない）。  
3. （推定 1:40）RAGの説明：顧客アカウントや社内ドキュメントなどの外部データを検索して、“根拠のある”正確な回答（例：ゴールドカードは遅延手数料 $35）を生成できる。事実参照が必要な場面に有効。  
4. （推定 2:30）Fine-tuningの説明：過去の1万〜百万件のチャットやポリシーでモデルを再学習させ、ブランド固有の言い回しや推奨（例：自動引落しを提案する）を恒常的に出せるようにする。モデルの重みを更新するためコストが高い。  
5. （推定 3:10）PEFT（LoRA/QLoRA）：全てのパラメータを更新せずに追加パラメータだけ学習する手法。計算・費用を大幅に抑えられるため実務で多用される。  
6. （推定 3:40）トレードオフ整理：Prompt engineering＝スタイル制御、RAG＝外部知識で正確性、Fine-tuning＝ドメイン適応と一貫性。RAGは安価だがFine-tuneは精度と一貫性が高い。  
7. （推定 4:10）実運用の推奨：三者を組み合わせることで最良の結果を得る（例：Fine-tunedモデルにRAGを組み合わせ、さらにプロンプトでトーンを統制）。  
8. （推定 4:30）面接向けメモ：これらの用語の違いを理解しておくとAIエンジニアの面接で役立つ、という締め。

アクション項目 / 役立つTips
- まず要件を整理：必要なのは「正確な事実参照か」「ブランドトーンの徹底か」「どちらもか」かを決める。  
- 低コストで済ませたい→Prompt engineering + RAGを組み合わせて運用開始。  
- ブランド一貫性や大量過去会話の反映が必要→PEFT（LoRA/QLoRA）で段階的にFine-tuneを検討。  
- RAG設計の注意：データの索引化（embeddings）、信頼できるソース設計、応答にソース参照を付ける（根拠提示）を必ず行う。  
- Fine-tune運用の注意：データ品質（ノイズ除去）、プライバシー（個人情報はマスク）、コスト評価を事前に実施。  
- 評価指標：正確度（fact accuracy）、一貫性（style conformity）、コスト（推論＆学習）、応答速度を定量化して比較する。  
- フォールバック設計：モデルが「わかりません」と答えるか、人間対応にエスカレーションする仕組みを入れる。  
- まずはMVPで検証→成功指標で拡張（PEFT→必要ならフルファインチューニングへ）。

英語 TL;DR
TL;DR: Prompt engineering controls tone/format, RAG injects factual external data for accurate answers, and fine-tuning adapts the model to domain-specific style and behavior; combine them in production and use PEFT (LoRA/QLoRA) to reduce fine-tuning costs.
