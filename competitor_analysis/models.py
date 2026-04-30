from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TweetStats:
    impressions: Optional[int] = None  # 自分のツイートのみ取得可能
    replies: int = 0
    reposts: int = 0
    likes: int = 0
    bookmarks: int = 0


@dataclass
class Tweet:
    tweet_id: str
    author_username: str
    created_at: datetime
    text: str
    stats: TweetStats
    url: str
    image_urls: list[str] = field(default_factory=list)

    @property
    def created_date(self) -> str:
        return self.created_at.strftime("%Y-%m-%d")

    @property
    def created_time(self) -> str:
        return self.created_at.strftime("%H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "投稿日": self.created_date,
            "投稿時間": self.created_time,
            "投稿内容": self.text,
            "インプレッション数": self.stats.impressions if self.stats.impressions is not None else "N/A",
            "リプ数": self.stats.replies,
            "リポスト数": self.stats.reposts,
            "いいね数": self.stats.likes,
            "ブックマーク数": self.stats.bookmarks,
            "URL": self.url,
            "画像URL": ", ".join(self.image_urls) if self.image_urls else "",
        }
