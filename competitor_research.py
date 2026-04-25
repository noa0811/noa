"""
競合アカウント調査データをGoogleスプレッドシートに書き込むスクリプト

使い方:
  1. credentials.json を同ディレクトリに配置する (OAuth2 クライアントシークレット)
  2. python competitor_research.py

初回実行時にブラウザが開くので Google アカウントにログインして権限を付与してください。
"""

import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json

# ──────────────────────────────────────────────
# 設定
# ──────────────────────────────────────────────
SPREADSHEET_ID = "1qXFft668hfrjNUwvLBuod-2FpkIC5INkHOrXhV0bZH8"
TARGET_GID = 1254143164
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# ──────────────────────────────────────────────
# 競合アカウントデータ
# 形式: [発見日, 評価, アカウント名, URL, FW, 開始日, リプ数, サブ/URL, LINE, note/無料, note/有料, note/アカウント, ペルソナ, コメント]
# 評価基準: A=リプ100〜, B=100前後, C=100以下
# ──────────────────────────────────────────────
TODAY = datetime.date.today().strftime("%Y/%m/%d")

ACCOUNTS = [
    # ── AIキャラ系 ──────────────────────────────────────────────────────
    [TODAY, "B", "みつい", "https://x.com/mrmitsuikun", "2000", "2023/01", "50〜80", "", "なし", "あり", "なし", "https://note.com/mrmitsui", "AI美女(架空モデル)", "AI美女×X運用の記録をnoteで公開。2000FW達成の実績あり。2025年基準外の可能性あり要確認"],
    [TODAY, "C", "九鬼若芽", "https://x.com/kukiwakame_ai", "不明", "2022/03", "〜50", "", "なし", "あり", "なし", "https://note.com/kukiwakame_ai", "AI美少女白書(イラスト系)", "AI美少女イラスト特化。開始2022年で条件外の可能性あり要確認"],
    [TODAY, "C", "怠目藍成(あいなる)", "https://x.com/darume_ainaru", "不明", "2025/01以降", "〜30", "", "要確認", "あり", "なし", "https://note.com/darume_ainaru", "AI美女研究・勉強中", "AI美女イラスト・X運用に関するnote多数。LINE有無は要確認"],
    [TODAY, "C", "てんねん", "https://x.com/munou_ac", "41000", "2024/頃", "〜100", "", "なし", "あり", "あり", "https://note.com/munou_ac", "AIイラストクリエイター", "AIイラスト1日12投稿。FW多すぎで条件外。参考競合として記録"],
    [TODAY, "C", "アミラナ", "https://x.com/amirana39", "不明", "2025/頃", "〜30", "", "要確認", "あり", "なし", "https://note.com/amirana39", "AIキャラ・日常系", "X AIコンパニオン機能紹介など。note有。詳細要確認"],
    # ── 以下は追加調査が必要なプレースホルダー (Grokで発掘後に記入) ─────────
    [TODAY, "要調査", "（未調査6）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", "Grokで「日常系女子 note LINE」検索で発掘"],
    [TODAY, "要調査", "（未調査7）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", "Grokで「AIキャラ 日常 note」検索で発掘"],
    [TODAY, "要調査", "（未調査8）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査9）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査10）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査11）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査12）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査13）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査14）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査15）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査16）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査17）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査18）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査19）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
    [TODAY, "要調査", "（未調査20）", "", "", "2025/", "", "", "要確認", "要確認", "要確認", "", "", ""],
]

HEADER = [
    "発見日", "評価", "アカウント名", "URL", "FW", "開始日",
    "リプ数", "サブ/URL", "LINE", "note/無料", "note/有料",
    "note/アカウント", "ペルソナ", "コメント"
]


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' が見つかりません。\n"
                    "Google Cloud Console でOAuth2クライアントIDを作成し、\n"
                    "JSONをダウンロードしてこのフォルダに配置してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def get_sheet_name_by_gid(service, spreadsheet_id: str, target_gid: int) -> str:
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta.get("sheets", []):
        props = sheet.get("properties", {})
        if props.get("sheetId") == target_gid:
            return props["title"]
    raise ValueError(f"GID {target_gid} に対応するシートが見つかりません")


def find_next_empty_row(service, spreadsheet_id: str, sheet_name: str) -> int:
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'!A:A"
    ).execute()
    values = result.get("values", [])
    return len(values) + 1


def write_to_sheet(service, spreadsheet_id: str, sheet_name: str,
                   start_row: int, rows: list) -> None:
    range_name = f"'{sheet_name}'!A{start_row}"
    body = {"values": rows}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"✅ {len(rows)} 行を '{sheet_name}'!A{start_row} から書き込みました")


def main():
    print("🔑 認証中...")
    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    print(f"📋 シート名を GID={TARGET_GID} から取得中...")
    sheet_name = get_sheet_name_by_gid(service, SPREADSHEET_ID, TARGET_GID)
    print(f"   → シート名: {sheet_name}")

    # 既存データの末尾を確認
    next_row = find_next_empty_row(service, SPREADSHEET_ID, sheet_name)
    print(f"   → 書き込み開始行: {next_row}")

    # ヘッダーが1行目にない場合のみヘッダーを書く
    if next_row == 1:
        rows_to_write = [HEADER] + ACCOUNTS
        start = 1
    else:
        rows_to_write = ACCOUNTS
        start = next_row

    write_to_sheet(service, SPREADSHEET_ID, sheet_name, start, rows_to_write)
    print(f"\n📊 完了！スプレッドシートを確認してください:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={TARGET_GID}")


if __name__ == "__main__":
    main()
