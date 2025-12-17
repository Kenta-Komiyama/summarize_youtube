# Steering LLM Behavior Without Fine-Tuning

- Channel: HuggingFace
- Published: 2025-12-17T16:00:32Z
- URL: https://www.youtube.com/watch?v=F2jd5WuT-zg

---

概要（3-5行）
- LLMの挙動を変える方法として、プロンプト設計やファインチューニングの第三の選択肢「activation steering（活性化の介入）」を解説。  
- 中間層の活性化ベクトルに「概念ベクトル」を加算して、推論時にモデルの性格や出力傾向を制御する手法を実演（LLaMA 3.1 8Bで「エッフェル塔」ペルソナ化）。  
- 手法の理論（線形表現・ベクトル加算・層の役割）、実装（Hugging Faceのforward hook＝coupler）、概念ベクトルの発見法、利点と限界を整理。

主要トピック（箇条書き）
- steering（活性化介入）の概念：推論時に内部表現を直接操作する手法  
- Transformer内部の「活性化ベクトル」と線形表現性（概念は方向で表現される）  
- 層ごとの役割：前層＝入力の反映、中間層＝抽象化／推論、後層＝出力化  
- 実装：HuggingFace Transformersでのforward hook（＝coupler）による加算  
- 概念ベクトルの探索方法：activation contrastive、sparse auto-encoder、Neuronpedia等のツール  
- 調整と安定化：スケーリング係数、温度やfrequency penaltyの調整  
- 長所・短所：低コストで強度調整可だが、新しい知識の付与には向かない

重要ポイント（番号付き、可能な範囲で概算タイムスタンプ）
1. (00:00–00:40) 背景 — プロンプトやファインチューニングに加え、推論時に内部活性化を操作する「第三の選択肢」がある。  
2. (00:40–02:00) 内部表現の構造 — 各層間の「隠れ状態ベクトル（活性化）」が高次元空間にあり、概念はそこにベクトルとして表現される（線形性）。  
3. (02:00–03:30) ベクトル演算の性質 — 概念は主に「方向」で決まり、ベクトルの大きさは表現の強さを調整するだけ。ベクトルの加算で複合概念や度合いを操作可能。  
4. (03:30–04:30) 層ごとの違い — 前方層は入力語の反映、中間層は抽象的概念の表現、後方層はトークン生成に近い表現。中間層を狙うのが効果的なことが多い。  
5. (04:30–06:00) 実装ポイント — 「coupler（forward hook）」を指定層に取り付け、活性化Xに正規化した概念ベクトルVを係数で乗じて加算するだけ。モデルの重みは変更しない（推論時のみ）。  
6. (06:00–07:00) デモ（LLaMA 3.1 8B） — 層15（全32層の中間）に「Eiffel Tower」ベクトルを加算。係数4で性向が変わり、係数8でモデルが「自分はエッフェル塔だ」と主張するほど強い影響を与えた（過度だと出力が破綻）。  
7. (07:00–08:30) 概念ベクトルの見つけ方：  
   - Activation contrastive：正例/負例の平均活性化差をとる（ラベルがある場合有効）。  
   - Sparse auto-encoder：中間活性化を疎な潜在で再構築すると各次元が解釈可能になる（非監督）。  
   - Neuronpediaなどの可視化リソースで既存の機能ベクトルを探す。  
8. (08:30–end) 利点と限界 — 利点：推論時のみで強度調整可能、軽量で共有しやすい。限界：概念が元々モデルに学習されている必要がある、新情報の学習にはならない、過度の加算で流暢さが失われる。

アクション項目 / 役立つTips
- 実装手順（簡潔）：
  1. Hugging Faceで対象モデルをロード。  
  2. 狙う層のforward hook（coupler）を登録。  
  3. 概念ベクトルVを用意（activation contrastiveや既存のencoder/Neuronpediaから）。Vを正規化し、スカラー係数αでスケール。  
  4. hook内で出力活性化Xにα·Vを加算して推論を行う。  
- 概念ベクトルの作り方：正/負例を用意して平均活性化の差分を取る（activation contrastive）が実用的で簡単。  
- 層選び：まずは中間層（モデルの総層数の前後50%付近）を試す。前方は単純な記述語に強く、後方は出力表現に直結するので破綻しやすい。  
- スケーリング：αは少しずつ増やす（小→大）。過大だと「デラウィング（発散）」するので検証用プロンプトで安定性チェックを必ず行う。  
- 安定化：温度（temperature）を下げる、frequency penaltyを使う、または複数プロンプトで評価して最適αを探索する。  
- ツール／参考：HuggingFace Hub（モデル・カスタムencoders）、Neuronpedia（機能探索）、著者のブログ（実装の詳細と追加テクニック）。  
- 注意点：この手法は既存の表現を強調するもので、新知識をモデルに「学習」させるわけではない。また、概念がモデルに存在しない場合は効果が小さい。

英語 TL;DR
TL;DR — You can steer LLM behavior at inference by adding normalized concept vectors to intermediate activations (via a forward hook). Find concept vectors via contrastive activations or sparse encoders, tune a scalar multiplier for strength, and prefer middle layers for abstract influence.
