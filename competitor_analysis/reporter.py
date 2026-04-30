import csv
import json
import os
from datetime import datetime

from tabulate import tabulate

from .models import Tweet


class Reporter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def print_table(self, tweets: list[Tweet], username: str) -> None:
        if not tweets:
            print(f"\n@{username} の投稿が見つかりませんでした。")
            return

        print(f"\n{'='*80}")
        print(f"  @{username} の競合分析レポート  ({len(tweets)} 件)")
        print(f"{'='*80}\n")

        rows = []
        for t in tweets:
            imp = str(t.stats.impressions) if t.stats.impressions is not None else "N/A"
            text_preview = t.text[:40] + "..." if len(t.text) > 40 else t.text
            rows.append([
                t.created_date,
                t.created_time,
                text_preview,
                imp,
                t.stats.replies,
                t.stats.reposts,
                t.stats.likes,
                t.stats.bookmarks,
                "あり" if t.image_urls else "なし",
            ])

        headers = ["投稿日", "時間", "内容（抜粋）", "IMP", "リプ", "リポスト", "いいね", "BM", "画像"]
        print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))

        print("\n--- 詳細 ---")
        for i, t in enumerate(tweets, 1):
            print(f"\n[{i}] {t.created_date} {t.created_time}")
            print(f"    URL: {t.url}")
            print(f"    内容: {t.text}")
            if t.image_urls:
                for j, img in enumerate(t.image_urls, 1):
                    print(f"    画像{j}: {img}")

    def save_csv(self, tweets: list[Tweet], username: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.output_dir, f"{username}_{ts}.csv")
        if not tweets:
            return path
        rows = [t.to_dict() for t in tweets]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nCSV保存: {path}")
        return path

    def save_json(self, tweets: list[Tweet], username: str) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.output_dir, f"{username}_{ts}.json")
        data = {
            "username": username,
            "fetched_at": datetime.now().isoformat(),
            "count": len(tweets),
            "tweets": [t.to_dict() for t in tweets],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON保存: {path}")
        return path
