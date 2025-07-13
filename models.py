from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text

class Lyrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    artist_name: str = Field(index=True, max_length=100)
    song_title: str = Field(index=True, max_length=100)
    spotify_track_id: str = Field(index=True, unique=True, max_length=50)
    lyrics: str = Field(sa_column=Column(Text, nullable=False))
    lyric_got_from_url: str = Field(max_length=255)

    created_at: datetime = Field(default_factory=datetime.utcnow)

class LyricsCreate(SQLModel):
    artist_name: str = Field(max_length=100)
    song_title: str = Field(max_length=100)
    spotify_track_id: str = Field(max_length=50)
    lyrics: str
    lyric_got_from_url: str = Field(max_length=255)
