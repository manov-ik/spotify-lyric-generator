from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text

class Lyrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    artistName: str = Field(index=True, max_length=100)
    songTitle: str = Field(index=True, max_length=100)
    spotifyTrackId: str = Field(index=True, unique=True, max_length=50)
    lyrics: str = Field(sa_column=Column(Text, nullable=False))
    lyricGotFromUrl: str = Field(max_length=255)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class LyricsCreate(SQLModel):
    artistName: str = Field(max_length=100)
    songTitle: str = Field(max_length=100)
    spotifyTrackId: str = Field(max_length=50)
    lyrics: str
    lyricGotFromUrl: str = Field(max_length=255)
