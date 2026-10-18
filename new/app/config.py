INDEX_NAME = "sheetdata_index"

LLM_URL = "https://azureservice.aiml.test.navbackoffice.com/api/v1/chat/inhouse"

LOW_CONFIDENCE_THRESHOLD = 0.02
MAX_CONTEXT_DOCS = 20

# Elasticsearch Config
ES_HOST = "https://inslordevv62.navbackoffice.com:9200"
ES_USER = "elastic"
ES_PASS = "nav#123"
ES_CERT_PATH = r"C:\Users\HarshalS\Downloads\elasticsearch-9.4.1-windows-x86_64\elasticsearch-9.4.1\config\certs\http_ca.crt"

# Model Path
MODEL_PATH = "C:/models/all-MiniLM-L6-v2"

SYSTEM_PROMPT = (
    "Strictly use only indexed data for answer generation. "
    "Use context. Do not hallucinate."
)

# Chat Session Storage
CHAT_SESSION_INDEX = "chat_sessions"

CHAT_MESSAGE_INDEX = "chat_messages"

CHAT_MEMORY_INDEX = "chat_memory_chunks"

RECENT_MESSAGE_LIMIT = 10

MEMORY_TOP_K = 5

MEMORY_CHUNK_SIZE = 10


UPLOAD_ROOT = "data/uploads"

UPLOAD_ORIGINALS_DIR = "data/uploads/originals"

UPLOAD_PROCESSED_DIR = "data/uploads/processed"

MAX_FILE_SIZE_MB = 25

SUPPORTED_FILE_TYPES = [
    ".pdf",
    ".docx",
    ".txt",
    ".csv"
]

ATTACHMENT_CHUNK_SIZE = 500

ATTACHMENT_CHUNK_OVERLAP = 50

ATTACHMENT_TOP_K = 20