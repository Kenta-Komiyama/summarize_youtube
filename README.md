# YouTube Summarizer (GitHub Actions)

## 概要
- 対象チャンネルの新着動画を検出
- 字幕を **yt-dlp** で取得（429対策/Androidクライアント偽装/任意cookie/任意proxy）
- 字幕が無い場合は **OpenAI Whisper** で文字起こし（任意）
- 本文を **gpt-5-mini** で要約 → `out/*.md` に保存
- `state.json` に処理済み videoId を記録して重複を防止

## セットアップ
1. このリポジトリを作成し、ここにあるファイルをすべて追加
2. リポジトリの **Settings → Secrets → Actions** で以下を設定
   - `OPENAI_API_KEY`（必須）
   - `YOUTUBE_API_KEY`（必須）
   - `COOKIES_TXT`（任意）ログインブラウザから `cookies.txt` をエクスポートし、中身を貼る
   - `HTTP_PROXY`（任意）`http://user:pass@host:port` など
3. `config.yaml` の `channels` を編集
4. Actions タブから **Run workflow**（手動）またはスケジュールで自動実行

## コスト目安（Whisper）
- 約 **$0.006/分**（例: 20分×2本 = $0.24）

## よくある質問
- **429/IpBlocked**: クラウドIPの制限。yt-dlpで回避、cookie/proxy、処理本数や間隔を調整。
- **字幕が無い**: Whisperを使うか `strict_captions_only: true` でスキップ。
- **コミットしない運用**: `EndBug/add-and-commit` ステップを外し、artifactsに保存する等へ変更可。
