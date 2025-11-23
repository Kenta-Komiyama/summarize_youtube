# Unreal Engine 5.7: Billions Of Triangles, In Real Time

- Channel: Two Minute Papers
- Published: 2025-11-23T16:06:34Z
- URL: https://www.youtube.com/watch?v=IyLQyob8W-w

---

概要（3-5行）
Unreal Engine 5.7の目玉は「Substrate」「Nanite Foliage」「Megalights」の3つで、いずれもリアルタイム表現を大幅に向上させる技術。Substrateは多層材料の光輸送シミュレーションを現場向けに実用化し、Nanite Foliageは無数の小要素をシームレスに描画、Megalightsは数百の光源によるソフトシャドウをリアルタイムで扱えるようにする。ほとんどの利用者に無償で提供される点も強調されている。

主要トピック（箇条書き）
- Substrate：多層材料の物理ベース光シミュレーション（生産レベル）
- Nanite Foliage：大量の植物・小オブジェクトを高効率で描画、目立たないLOD切替
- Megalights：多数光源のリアルタイム陰影（ソフトシャドウ、方向光、髪や粒子のシャドウ）
- MatterHumanアップデート：リアルな人物生成・表情キャプチャ（Live Link Face）やヘア/物理の改良
- Lambda GPUCloud / OpenGPTの紹介：巨大モデルを速く動かせるクラウドGPUの話題

重要ポイント（番号付き、可能ならタイムスタンプ）
1. 0:00–0:15 — リリース概要：UE5.7が正式公開、ほとんどの用途で無料。  
2. 0:15–0:50 — Substrateの核心：何百万もの光線での光輸送をシミュレートし、金属芯＋コーティングのような多層材の光の反射・透過（層間の再反射）をリアルタイムで表現。研究成果が実用化され、プロダクション対応になった点が重要。  
3. 0:50–1:30 — Nanite Foliageの役割：林や草など「無数の小オブジェクト」を効率的にレンダリングし、遠距離⇔近距離のLOD切替で起きる“ポップ”をほとんど見えないレベルで解消。計算負荷を大幅削減。  
4. 1:30–2:10 — Megalightsの特徴：数百の光源を扱い、それぞれがソフトシャドウを落とすなど高品質かつリアルタイムなライティングが可能。方向光・粒子・髪へのシャドウ対応、ノイズ低減とパフォーマンス改善。現時点では実験段階からベータへ移行（まだ最終版ではない）。  
5. 2:10–2:50 — MatterHumanとリアルタイム表情：Live Link Faceでカメラから顔の表情をリアルタイム転送、ヘアスタイルの生成・アニメーションやキャラクターの物理的相互作用が向上。  
6. 2:50–終わり — 補足：LambdaのクラウドGPUでOpenGPTの巨大モデルを高速実行できる実例紹介（低コストで高性能をレンタル可能）。

アクション項目 / 役立つTips
- Substrateを試す：物理ベースの多層マテリアルを作り、コーティングや層間反射の見え方を比較してみる（金属＋クリアコートなどがわかりやすい）。  
- Nanite Foliage導入：森林や草地のシーンでパフォーマンステスト。LODの切替が目立たないか、遠景→近景での表示品質を確認する。  
- Megalightsはベータ扱い：プロジェクトに導入する前に安定性とパフォーマンスを小規模で検証。レイトレーシング対応GPUが必要。  
- Live Link Face活用：実写からの顔キャプチャを即座に試せるので、キャラ表現の評価やプロトタイプ制作に便利。  
- クラウドGPUの活用：手元のマシンが非力ならlambda.ai等で短時間レンタルして試し、コスト対効果を確認する（OpenGPTなど大規模モデルの試用に有効）。

英語 TL;DR
Unreal Engine 5.7 brings production-ready Substrate (multi-layer light transport), seamless Nanite foliage LOD for massive detail, and Megalights for hundreds of realtime soft-shadowing lights — plus MatterHuman and Live Link Face for real-time characters. Free for most users.
