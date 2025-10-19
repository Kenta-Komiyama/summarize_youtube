# [Video Response] What Cloudflare's code mode misses about MCP and tool calling

- Channel: Yannic Kilcher
- Published: 2025-10-19T10:58:51Z
- URL: https://www.youtube.com/watch?v=0bpYCxv2qhw

---

概要（3-5行）
- Cloudflareが提唱する「code mode」（ツールをTypeScript APIとして表現し、LLMにそのAPI呼び出しコードを書かせ実行する方式）は、LLMの事前学習に大量の実世界コードがあるため有効である可能性が高い。  
- ただし著者は、複雑で非決定的な現実世界のツール連携では「事前にすべての呼び出しを組み立てる」やり方が失敗しやすいと警告する。  
- 中間出力を見て動的に判断する必要があるケースには、全てを一括実行するだけでは対応できないため、「投機的（speculative）実行＋後続検証」という折衷案を提案している。

主要トピック（箇条書き）
- code mode の概念：ツールをTypeScript APIに変換し、LLMにコードを書かせる
- なぜ有効か：LLMの事前学習にコードが大量に含まれる可能性
- 従来のツール呼び出し（tool calling）との違い（トークン浪費・反復処理）
- 非決定性（ツール出力が常に同じではない現実世界データ）の問題
- JSON modeや固定フォーマットの限界
- 提案：投機的（speculative）ツール呼び出し＋中間出力のLLMによる検証
- MCPの過大評価への注意（MCPは単なるAPI公開の標準）

重要ポイント（番号付き、場所目安）
1. （導入）code mode の主張：ツールをTypeScript APIとして提示し、LLMにコードを書かせればより多く・複雑なツールを扱えるというCloudflareの観察。  
2. （導入）根拠仮説：LLMは事前学習で大量の実世界TypeScriptコードを見ているため、APIコールを「コードで記述する」方が得意。対して従来のツール呼び出しは微調整（fine-tuning）例に依存し限定的。  
3. （中盤）Cloudflareの主張2：複数ツールを連結する際、各ツールの出力を毎回LLMに戻すのは無駄なので、あらかじめコードで連結して一度に実行した方が効率的、という点に同意はするが…  
4. （中盤）問題提起：現実世界ではツール出力が非決定的（位置がGPSだったり住所だったり、あるいはユーザーへの確認が必要だったり）で、次の手が出力に応じて変わるケースが多い。事前に固定したフローでは対処できない。  
5. （中盤）JSON mode等の厳格フォーマットも万能ではなく、出力に依存した分岐ロジックが必要になる場面がある。  
6. （中盤/実践）人間は中間出力を見て計画を修正する。LLM主体での「事前一括実行」は、計画通りに動くことを前提にしすぎている。  
7. （終盤）提案：投機的ツール呼び出し（複数のツール呼び出しを一括で実行して中間結果を全て記録）し、その中間出力ごとにLLMに「どこが怪しいか／計画を継続して良いか」を判断させる。これでcode modeの利点（少ない往復）と従来方式の利点（中間判断）を両取りできる可能性がある。  
8. （結論）MCP自体は魔法ではなく単なるAPI公開の標準。過度な期待は禁物。

アクション項目 / 役立つTips
- ツールをTypeScript APIでラップするのは有効：LLMが扱いやすくなるため導入を検討する価値あり。  
- ただし、複雑・非決定的ワークフローでは「中間出力のログ」を必ず保存し、LLMや別ロジックで後から検証できる仕組みを作る。  
- 投機的実行パターン：可能性の高い分岐を先回りして実行→中間出力をLLMに再評価させる。余分な呼び出しが増えるが、往復回数と手動介入を減らせる場合がある。  
- ツールは「常に同じ型の出力を返す」と仮定せず、エラー／確認要求／複数フォーマットを扱える設計にする（型柔軟性・バリデーション・フォールバック）。  
- 実装上の工夫：中間出力をシリアライズしてLLMに渡すテンプレートを用意、どの出力が“想定外”かを掴ませるためのプロンプト設計を行う。  
- MCPを導入する際は「標準化の利点（運用・互換性）」と「新しい能力が付与されるわけではない」点をチームに共有する。

英語 TL;DR (1-2 lines)
Cloudflare's "code mode" (wrap tools as TypeScript APIs and let LLMs write the calling code) leverages LLMs' code-heavy pretraining, but fails when tool outputs are non-deterministic. A practical compromise: speculative execution of multiple calls + feed intermediate results back to the LLM for validation.
