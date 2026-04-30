#!/usr/bin/env python3
"""
X（Twitter）競合分析ツール

使い方:
    python -m competitor_analysis.main --username <ユーザー名> [options]

例:
    python -m competitor_analysis.main --username elonmusk --max 20
    python -m competitor_analysis.main --username openai --max 10 --no-retweets
"""

import argparse
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from .fetcher import XFetcher
from .reporter import Reporter


def parse_args():
    parser = argparse.ArgumentParser(
        description="X（Twitter）競合アカウントの投稿を分析します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--username", "-u",
        required=True,
        help="分析対象のXユーザー名（@なし）。複数指定可（カンマ区切り）",
    )
    parser.add_argument(
        "--max", "-n",
        type=int,
        default=10,
        dest="max_results",
        help="取得する最大投稿数（デフォルト: 10, 最大: 100）",
    )
    parser.add_argument(
        "--no-retweets",
        action="store_true",
        help="リツイートを除外する",
    )
    parser.add_argument(
        "--no-replies",
        action="store_true",
        help="リプライを除外する",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ディレクトリ（デフォルト: output）",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "both", "none"],
        default="both",
        help="出力形式（デフォルト: both）",
    )
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()

    try:
        fetcher = XFetcher()
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    reporter = Reporter(output_dir=args.output_dir)
    usernames = [u.strip().lstrip("@") for u in args.username.split(",")]

    for username in usernames:
        print(f"\n@{username} の投稿を取得中...")
        try:
            tweets = fetcher.fetch_tweets(
                username=username,
                max_results=args.max_results,
                exclude_replies=args.no_replies,
                exclude_retweets=args.no_retweets,
            )
        except ValueError as e:
            print(f"エラー: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"取得エラー (@{username}): {e}", file=sys.stderr)
            continue

        reporter.print_table(tweets, username)

        if args.format in ("csv", "both"):
            reporter.save_csv(tweets, username)
        if args.format in ("json", "both"):
            reporter.save_json(tweets, username)

    print("\n完了。")


if __name__ == "__main__":
    main()
