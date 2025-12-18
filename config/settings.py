import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL")

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    DATABASE_NAME = os.getenv("DATABASE_NAME")

    # Data Path
    DATA_PATH = "D:/Data"

    # Batch Size
    BATCH_SIZE = 10  # Add this line if not present

    # App Settings
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", 8000))

settings = Settings()