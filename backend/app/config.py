import os
from dotenv import load_dotenv

# Load .env from the backend/ folder
_HERE = os.path.dirname(os.path.abspath(__file__))          # app/
_BACKEND = os.path.dirname(_HERE)                            # backend/
load_dotenv(os.path.join(_BACKEND, ".env"))
load_dotenv()  # fallback: cwd


class Settings:
    PROJECT_NAME: str = "Meeting AI Platform"

    # FAISS / Vector store
    EMBEDDING_DIM: int = 384          # all-MiniLM-L6-v2 output dim
    VECTOR_STORE_PATH: str = "vector_store/faiss.index"
    METADATA_PATH: str = "vector_store/metadata.pkl"

    # LLM (Groq)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = "llama3-8b-8192"

    # Kafka
    KAFKA_BOOTSTRAP: str = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")

    # Topics
    TOPIC_TRANSCRIPTS: str = "transcripts"
    TOPIC_RAW_AUDIO: str = "raw_audio"
    TOPIC_SUMMARIES: str = "summaries"
    TOPIC_ACTION_ITEMS: str = "action_items"
    TOPIC_ALERTS: str = "alerts"
    TOPIC_SPEAKER_EVENTS: str = "speaker_events"

    # SQLite DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meeting_platform.db")

    # Transcription (Groq Whisper)
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-large-v3")


settings = Settings()
