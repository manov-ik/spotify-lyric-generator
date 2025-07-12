from generate_lyrics import engine
from sqlmodel import SQLModel

def init_db():
    SQLModel.metadata.create_all(engine)

init_db()
