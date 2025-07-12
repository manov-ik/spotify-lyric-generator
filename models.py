from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Lyrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artistName: str
    songTitle: str
    spotifyTrackId: str
    spotifyUrl: str
    lyrics: str
    lyricGotFromUrl: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LyricsCreate(SQLModel):
    artistName: str
    songTitle: str
    spotifyTrackId: str
    spotifyUrl: str
    lyrics: str
    lyricGotFromUrl: str
