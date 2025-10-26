import os
from openai import OpenAI

SYSTEM_PROMPT = """あなたは有能な要約アシスタントです。動画の文字起こしを読み、
読者が3分以内で要点を把握できるように、重複を除き、正確・簡潔に要約してください。
技術用語は噛み砕きつつ、ニュアンスは保ってください。"""

USER_TEMPLATE = """以下はYouTube動画のメタ情報と文字起こしです。{lang_label}中心でまとめ、最後に英語で短いTL;DRを1-2行追記してください。

# メタ情報
- タイトル: {title}
- チャンネル: {channel_title}
- 公開日: {published_at}
- URL: https://www.youtube.com/watch?v={video_id}

# 期待する出力（{lang_label}）
- 概要（3-5行）
- 主要トピック（箇条書き）
- 重要ポイント（番号付き、可能ならタイムスタンプを含めて）
- アクション項目 / 役立つTips
- 英語TL;DR（1-2行）

# 文字起こし
{transcript}
"""

def summarize(meta: dict, transcript_text: str, lang="ja") -> str:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    lang_label = "日本語" if lang.startswith("ja") else "English"
    prompt = USER_TEMPLATE.format(
        lang_label=lang_label,
        title=meta["title"],
        channel_title=meta["channel_title"],
        published_at=meta["published_at"],
        video_id=meta["video_id"],
        # transcript=transcript_text[:60000],26337646
        transcript=transcript_text[:10000000],
    )
    resp = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":prompt}],
    )
    return resp.choices[0].message.content.strip()
