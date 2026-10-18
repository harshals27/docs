from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router
from app.routes.attachments import router as attachment_router


app = FastAPI(
    title="Synapse API",
    version="1.0.0",
    description="RAG Chat API with attachment ingestion support"
)

# Chat routes
app.include_router(router)

# Attachment routes
app.include_router(attachment_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "synapse-api"
    }