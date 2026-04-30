import os
from datetime import datetime, timezone
from typing import Optional

import tweepy

from .models import Tweet, TweetStats


class XFetcher:
    def __init__(self):
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN が設定されていません。.env ファイルを確認してください。")

        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            wait_on_rate_limit=True,
        )

        # OAuth 2.0 ユーザー認証が使えるか（インプレッション取得用）
        self._has_user_auth = all([
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        ])

    def get_user_id(self, username: str) -> str:
        response = self.client.get_user(username=username)
        if not response.data:
            raise ValueError(f"ユーザー '{username}' が見つかりません。")
        return str(response.data.id)

    def fetch_tweets(
        self,
        username: str,
        max_results: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        exclude_replies: bool = False,
        exclude_retweets: bool = True,
    ) -> list[Tweet]:
        user_id = self.get_user_id(username)

        tweet_fields = ["created_at", "public_metrics", "attachments", "text"]
        media_fields = ["url", "preview_image_url", "type"]
        expansions = ["attachments.media_keys", "author_id"]

        # 自分のアカウントにはnon_public_metricsも取得試行
        if self._has_user_auth:
            tweet_fields.append("non_public_metrics")

        exclude_list = []
        if exclude_replies:
            exclude_list.append("replies")
        if exclude_retweets:
            exclude_list.append("retweets")

        kwargs = dict(
            id=user_id,
            max_results=min(max_results, 100),
            tweet_fields=tweet_fields,
            media_fields=media_fields,
            expansions=expansions,
        )
        if exclude_list:
            kwargs["exclude"] = exclude_list
        if start_time:
            kwargs["start_time"] = start_time
        if end_time:
            kwargs["end_time"] = end_time

        response = self.client.get_users_tweets(**kwargs)

        if not response.data:
            return []

        # メディア情報をマップ化
        media_map: dict[str, list[str]] = {}
        if response.includes and "media" in response.includes:
            for media in response.includes["media"]:
                url = getattr(media, "url", None) or getattr(media, "preview_image_url", None)
                if url:
                    media_map[media.media_key] = url

        tweets = []
        for raw in response.data:
            pm = raw.public_metrics or {}
            npm = getattr(raw, "non_public_metrics", None) or {}

            stats = TweetStats(
                impressions=npm.get("impression_count"),
                replies=pm.get("reply_count", 0),
                reposts=pm.get("retweet_count", 0),
                likes=pm.get("like_count", 0),
                bookmarks=pm.get("bookmark_count", 0),
            )

            # 画像URL収集
            image_urls = []
            attachments = getattr(raw, "attachments", None)
            if attachments and hasattr(attachments, "media_keys"):
                for key in attachments.media_keys:
                    if key in media_map:
                        image_urls.append(media_map[key])

            created_at = raw.created_at
            if created_at and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            tweet = Tweet(
                tweet_id=str(raw.id),
                author_username=username,
                created_at=created_at,
                text=raw.text,
                stats=stats,
                url=f"https://x.com/{username}/status/{raw.id}",
                image_urls=image_urls,
            )
            tweets.append(tweet)

        return tweets
