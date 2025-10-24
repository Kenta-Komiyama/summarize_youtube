# What is Databricks?

- Channel: codebasics
- Published: 2025-10-24T13:31:57Z
- URL: https://www.youtube.com/watch?v=P5-A60xmAbw

---

概要
DatabricksはApache Sparkを基盤にしたクラウドのマネージドプラットフォームで、データ格納・処理・解析を大規模に行える。クラスタ管理やスケーリングなどのインフラ運用をDatabricks側が引き受けるため、ユーザはビジネスロジックに集中できる。学習用途は databricks.com、本番／企業用途ではAzureなどクラウド上のDatabricks利用が一般的。

主要トピック
- 自己ホスティング（自分でSparkをダウンロードして構築）とマネージドサービスの比較
- DatabricksのUI（ノートブック、SQLエディタ、コネクタ、データパイプライン、AI/ML機能）
- クラスタライフサイクル管理（プロビジョニング、スケーリング、ログ監視などをDatabricksが代行）
- オートスケール／サーバーレス的な利用（必要に応じたコンピュート割当て）
- Databricksの起源（Apache Sparkの創始者が設立、Berkeley由来）と普及理由
- マルチクラウド展開（databricks.comの他にAzure Databricks等で利用可能）
- Azure上での利点（ADLS・Power BIなどエコシステム統合、セキュリティ・サポート・ガバナンス）

重要ポイント（番号付き）
1. DatabricksはApache Sparkを“そのまま使う”のではなく、Sparkのクラスタ管理をマネージドで提供するプラットフォームである。  
   - インフラ（VMのプロビジョニング、スケーリング、ログ管理等）をユーザが直接運用する必要がない。
2. 自己ホスティングの負担は大きい（ノード管理、インストール、手動スケーリングなど）。Databricksはこれを「イベントプランナー」に例える形で代行する。  
3. UIと機能：ノートブック作成、SQLクエリエディタ、データエンジニアリング／ジョブ実行、各種コネクタ（SalesforceやSQL Server等）、AI/MLオプションを備える。  
4. オートスケール／消費ベース課金により、必要時にだけコンピュートを使う運用が可能（Lambda的な“サーバーレス”感）。  
5. DatabricksはSpark設立者ら（Berkeleyの研究者）が創業しており、その信頼性と普及理由に繋がっている。創業者の一部は高い評価を受けている。  
6. Databricksは直営のweb版で学習や実験がしやすいが、企業プロジェクトではAzure Databricks等を選ぶことが多い。  
7. Azureなどクラウド上でのDatabricks利用の利点：ストレージ（ADLS）、BI（Power BI）、イベントハブ、セキュリティ／コンプライアンス、サポートなどの深い統合。  
8. UIはdatabricks.comもAzure Databricksもほぼ同じで、違いは主に裏側のクラウド統合・企業機能。

（注）文字起こしにタイムスタンプが含まれていないため、個別発言の正確な時刻は付記できません。

アクション項目 / 役立つTips
- 学習・実験：まずは databricks.com の環境でノートブックやSQLエディタに触れてみる。  
- 本番導入：クラウドプロバイダ（例：Azure Databricks）上での利用を優先し、既存のクラウド資源（ADLS、Power BI等）との連携を設計する。  
- コスト管理：オートスケールやサーバーレス設定を活用して不要な常時稼働を避ける（使い終わったら自動停止設定なども検討）。  
- 運用フォーカス：インフラ運用を最小化して、データパイプライン設計やモデル開発に注力する。  
- セキュリティ／ガバナンス：企業導入時はクラウド版のセキュリティ機能やサポート体制を確認する。  
- コネクタ活用：既存データソース（Salesforce、SQL Serverなど）へはDatabricksのコネクタで直接接続してパイプラインを簡略化する。

英語 TL;DR
Databricks is a managed cloud platform built on Apache Spark that offloads cluster lifecycle and scaling so teams can focus on data engineering and analytics. Use databricks.com for learning; use cloud-specific Databricks (e.g., Azure Databricks) for enterprise integration, security, and support.
