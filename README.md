# Synapse RAG Chat & Document Ingestion System

> **Full-stack Hybrid RAG (Retrieval-Augmented Generation) Platform** combining semantic vector search and BM25/keyword search over Elasticsearch with local sentence transformers, contextual memory chunking, dynamic multi-format document ingestion, and a React + Vite conversational interface.

---

## 🤖 Context for AI Models (LLM / Agent Quick Index)

> **Directive for AI Agents:** Do **NOT** scan or reread all repository files repeatedly. Use this targeted index to determine exactly which file to inspect or edit based on the task type.

### File Responsibility & Routing Map

| Domain / Task | Target File | Key Functions / Responsibilities |
| :--- | :--- | :--- |
| **Server & Routing Entry** | [`app/main.py`](file:///c:/Users/BIT/Desktop/new/app/main.py) | FastAPI app initialization, CORS middleware, router registrations (`/chat`, `/attachments`), health check (`GET /`). |
| **System Configurations** | [`app/config.py`](file:///c:/Users/BIT/Desktop/new/app/config.py) | Global constants: Elasticsearch hosts, cert paths, indices (`sheetdata_index`, `chat_sessions`, `chat_messages`, `chat_memory_chunks`), model paths, thresholds, upload paths, chunk size limits. |
| **Query Orchestration & RAG** | [`app/routes/chat.py`](file:///c:/Users/BIT/Desktop/new/app/routes/chat.py) | `POST /chat` handler: records user queries, context query rewrite, triggers vector/keyword search, applies RRF fusion, extracts citations, fetches recent & long-term memory, constructs LLM prompt, calls LLM, triggers periodic memory chunk creation. |
| **Document Upload & Lifecycle** | [`app/routes/attachments.py`](file:///c:/Users/BIT/Desktop/new/app/routes/attachments.py) | `POST /attachments/upload`, `DELETE /attachments/{attachment_id}`, `GET /attachments/{attachment_id}` endpoints. Manages temporary file saving and error responses. |
| **Attachment Ingestion Logic** | [`app/services/attachment_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/attachment_service.py) | Ingestion pipeline orchestration: `ingest_attachment()`, chunk indexing `index_attachment_chunks()`, chunk deletion `delete_attachment()`, retrieval `get_attachment_chunks()`, metadata lookup `get_attachment_metadata()`. |
| **Document Extraction & Chunks**| [`app/services/document_parser_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/document_parser_service.py) | Extractors: `parse_pdf()` (`pdfplumber`), `parse_docx()` (`python-docx`), `parse_txt()`, `parse_csv()` (`pandas`). Overlapping sliding-window chunker: `chunk_text()`. |
| **Elasticsearch Operations** | [`app/services/elasticsearch_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/elasticsearch_service.py) | Elasticsearch client instance `es`. Semantic kNN search `semantic_search()`, keyword match search `keyword_search()`, session & chat history storage/queries, memory chunk persistence and kNN memory retrieval. |
| **Vector Embeddings** | [`app/services/embedding_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/embedding_service.py) | Local model loader (`SentenceTransformer(MODEL_PATH)`), single text `get_embedding()`, batch `get_embeddings()`. |
| **Ranking & Fusion** | [`app/services/fusion_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/fusion_service.py) | Reciprocal Rank Fusion (`rrf_fusion(vector_hits, keyword_hits, k=60)`), prompt context formatter `build_memory_context()`. |
| **LLM Gateway** | [`app/services/llm_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/llm_service.py) | Azure/In-house LLM API caller `call_llm()`, header handling (`X-API-KEY`), timeout and error parsing. |
| **Conversation Memory** | [`app/services/memory_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/memory_service.py) | Long-term memory chunk generator `create_memory_chunk()` and memory semantic retriever `get_relevant_memories()`. |
| **Chat History Storage** | [`app/services/chat_history_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/chat_history_service.py) | Message persistence wrapper: `store_user_message()`, `store_assistant_message()`, `fetch_recent_chat()`, `get_message_count()`. |
| **Query Rewriting & Entity** | [`app/utils/query_utils.py`](file:///c:/Users/BIT/Desktop/new/app/utils/query_utils.py) | Co-reference resolution: `extract_entity()` and `rewrite_query_with_context()`. Replaces pronouns (`it`, `they`, `this`) with prior entities. |
| **File I/O & Hashes** | [`app/utils/file_utils.py`](file:///c:/Users/BIT/Desktop/new/app/utils/file_utils.py) | Path and directory preparation, `sanitize_filename()`, `calculate_file_hash()` (SHA-256), `save_uploaded_file()`, `delete_file()`. |
| **Logging Utility** | [`app/logger.py`](file:///c:/Users/BIT/Desktop/new/app/logger.py) | Centralized logging configuration (`logs/app.log` and console stream). |
| **Data Contracts (Pydantic)** | [`app/models/request_models.py`](file:///c:/Users/BIT/Desktop/new/app/models/request_models.py), [`app/models/attachment_models.py`](file:///c:/Users/BIT/Desktop/new/app/models/attachment_models.py) | Request/Response schemas: `ChatRequest`, `CreateSessionRequest`, `AttachmentMetadata`, `AttachmentChunk`, `AttachmentUploadResponse`, `AttachmentDeleteResponse`. |
| **Frontend UI Core** | [`frontend/my-ui/src/App.jsx`](file:///c:/Users/BIT/Desktop/new/frontend/my-ui/src/App.jsx) | React single-page chat application: state for multi-session management, localStorage caching, file attachment uploading/validation, animated response typing, Markdown + Syntax highlighting rendering. |
| **Frontend Styles** | [`frontend/my-ui/src/App.css`](file:///c:/Users/BIT/Desktop/new/frontend/my-ui/src/App.css), [`frontend/my-ui/src/index.css`](file:///c:/Users/BIT/Desktop/new/frontend/my-ui/src/index.css) | Custom styles, sidebar styling, chat bubble themes, code block containers, animations. |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Frontend)"]
        UI["React 18 + Vite (my-ui)\nLocalStorage Multi-Session"]
    end

    subgraph API ["FastAPI Application (app/main.py)"]
        CR["Chat Router\n/chat"]
        AR["Attachment Router\n/attachments/*"]
    end

    subgraph Pipeline ["RAG Ingestion & Query Pipeline"]
        QR["Query Rewriter & Entity Extraction\n(app/utils/query_utils.py)"]
        Parser["Document Parser & Chunker\nPDF / DOCX / TXT / CSV\n(app/services/document_parser_service.py)"]
        Embedder["SentenceTransformer\n(app/services/embedding_service.py)"]
        RRF["Reciprocal Rank Fusion (RRF)\n(app/services/fusion_service.py)"]
        MemService["Memory & History Manager\n(app/services/memory_service.py)"]
    end

    subgraph Storage ["Elasticsearch Data Store"]
        ES_Docs[("Knowledge & Attachment Index\n(sheetdata_index)")]
        ES_Hist[("Message Log\n(chat_messages)")]
        ES_Sess[("Sessions\n(chat_sessions)")]
        ES_Mem[("Memory Chunks\n(chat_memory_chunks)")]
    end

    subgraph External ["LLM Service"]
        LLM["In-house / Azure LLM Endpoint\n(app/services/llm_service.py)"]
    end

    UI -->|Sends Query & Session ID| CR
    UI -->|Uploads Document File| AR

    AR --> Parser
    Parser -->|Raw Chunks| Embedder
    Embedder -->|Vectors + Text Chunks| ES_Docs

    CR -->|Resolves Pronouns| QR
    QR -->|Cleaned Query| Embedder
    Embedder -->|Query Vector| ES_Docs
    QR -->|Keyword Term| ES_Docs

    ES_Docs -->|Vector Hits + Keyword Hits| RRF
    RRF -->|Top Ranked Documents| CR

    CR -->|Fetches History| ES_Hist
    CR -->|Queries Contextual Chunks| ES_Mem
    MemService -->|Builds Composite Context| CR

    CR -->|Payload: System + Memory + Context + History| LLM
    LLM -->|Answer| CR
    CR -->|Persists Response| ES_Hist
    CR -->|Stores Periodic Chunk (every 10 msgs)| ES_Mem
    CR -->|JSON Reply + Citations| UI
```

---

## 🔄 Detailed Workflows

### 1. Document Upload & Ingestion Workflow
1. **User Upload**: User selects a file via frontend UI or sends `multipart/form-data` to `POST /attachments/upload`.
2. **Validation**: The file extension must be one of `.pdf`, `.docx`, `.txt`, `.csv` and within the 25 MB limit.
3. **Storage & Hash**: File is copied into `data/uploads/originals/{attachment_id}.ext`, and an SHA-256 hash is computed.
4. **Parsing**:
   - `.pdf`: Extracted using `pdfplumber`.
   - `.docx`: Extracted using `docx.Document`.
   - `.txt`: UTF-8 parsed with error handling.
   - `.csv`: Formatted into a table representation via `pandas`.
5. **Chunking**: `chunk_text()` splits text into sliding windows of 500 words with 50-word overlaps.
6. **Vectorization**: `SentenceTransformer` converts all chunks into dense embeddings in batch.
7. **Indexing**: Chunks are saved into Elasticsearch index `sheetdata_index` tagged with `attachment_id`, `session_id`, `filename`, `chunk_number`, and `embedding`.

### 2. Conversational Query & Hybrid Retrieval Workflow
1. **Incoming Request**: Receives user query, current session ID, and any active `attachment_ids`.
2. **Query Normalization & Coreference Resolution**:
   - `rewrite_query_with_context` inspects conversation turns.
   - If user asks *"Tell me more about it"*, it extracts the entity mentioned in earlier turns and replaces pronouns.
3. **Hybrid Search Execution**:
   - **Semantic Search**: `knn` query with `query_vector` and candidate pool (`num_candidates: 100`). If `attachment_ids` are passed, an Elasticsearch terms filter scopes search to those files.
   - **Keyword Search**: If query contains named entities, a fuzzy/multi-term match search is fired against the `combined` text field.
4. **Reciprocal Rank Fusion (RRF)**:
   - Combines vector search hits and keyword search hits using $Score = \sum \frac{1}{60 + rank + 1}$.
   - Discards searches below `LOW_CONFIDENCE_THRESHOLD` (0.02).
5. **Context Assembly**:
   - Selects top 20 documents (`MAX_CONTEXT_DOCS`).
   - Gathers document citations (`source_file`, `category`, `version`, `created_by`, `created_date`).
   - Retrieves recent chat messages (last 10).
   - Queries `chat_memory_chunks` using vector similarity for relevant long-term memories.
6. **LLM Invocation**:
   - Forms system prompt with combined Session Memory + Retrieved Knowledge Base Context.
   - Calls the LLM HTTP endpoint with JSON payload.
7. **Memory Evolution**:
   - Appends user and assistant messages to `chat_messages`.
   - Every 10 messages (`MEMORY_CHUNK_SIZE`), creates an embedded memory summary chunk stored in `chat_memory_chunks`.

---

## 📂 Project Directory Structure

```text
.
├── app/                                # Backend Application (FastAPI)
│   ├── main.py                         # App bootstrap, CORS, router inclusions
│   ├── config.py                       # Application configurations & indices
│   ├── logger.py                       # Rotating file & stdout logger setup
│   ├── models/
│   │   ├── attachment_models.py        # Pydantic models for attachments
│   │   └── request_models.py           # Pydantic models for chat requests
│   ├── routes/
│   │   ├── attachments.py              # Upload, delete, view attachment endpoints
│   │   └── chat.py                     # Main RAG chat endpoint & pipeline
│   ├── services/
│   │   ├── attachment_service.py       # Ingestion orchestration & ES attachment ops
│   │   ├── chat_history_service.py     # Message logging & retrieval
│   │   ├── document_parser_service.py  # PDF, Word, CSV, TXT parser & chunker
│   │   ├── elasticsearch_service.py    # Elasticsearch connection & queries
│   │   ├── embedding_service.py        # Sentence transformer model loader
│   │   ├── fusion_service.py           # RRF rank fusion & context builders
│   │   ├── llm_service.py              # External LLM API invocation
│   │   ├── memory_service.py           # Chat chunk memory embeddings & search
│   │   └── search_service.py           # Hybrid vector & keyword search coordinator
│   └── utils/
│       ├── file_utils.py               # File storage, hashing, and sanitization
│       └── query_utils.py              # Entity extraction & query coreference rewriter
│
├── frontend/                           # Frontend Web Application
│   └── my-ui/                          # Vite + React App
│       ├── src/
│       │   ├── App.jsx                 # Main conversational UI component
│       │   ├── App.css                 # Component & layout styles
│       │   ├── index.css               # Base CSS design tokens
│       │   └── main.jsx                # React root mount
│       ├── index.html                  # HTML template
│       ├── package.json                # Frontend dependencies (React, Axios, Markdown)
│       └── vite.config.js              # Vite configuration
│
├── package.json                        # Root helper package descriptors
└── README.md                           # Project documentation & AI context guide
```

---

## ⚙️ Configuration & Environment Variables

All primary backend settings reside in [`app/config.py`](file:///c:/Users/BIT/Desktop/new/app/config.py):

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `INDEX_NAME` | `sheetdata_index` | Primary index for document chunks & knowledge base. |
| `LLM_URL` | `https://azureservice.../chat/inhouse` | Target LLM endpoint. |
| `ES_HOST` | `https://inslordevv62.navbackoffice.com:9200` | Elasticsearch host cluster. |
| `ES_USER` / `ES_PASS` | `elastic` / `nav#123` | Elasticsearch authentication credentials. |
| `ES_CERT_PATH` | *Path to http_ca.crt* | SSL CA certificate for Elasticsearch. |
| `MODEL_PATH` | `C:/models/all-MiniLM-L6-v2` | Local HuggingFace sentence transformer path. |
| `LOW_CONFIDENCE_THRESHOLD` | `0.02` | Minimum RRF score cutoff to trigger LLM. |
| `MAX_CONTEXT_DOCS` | `20` | Max context chunks sent into the prompt. |
| `RECENT_MESSAGE_LIMIT` | `10` | Max recent history turns injected into prompt. |
| `MEMORY_CHUNK_SIZE` | `10` | Frequency of messages before triggering memory chunking. |
| `UPLOAD_ROOT` | `data/uploads` | Local upload directory base path. |
| `MAX_FILE_SIZE_MB` | `25` | Maximum upload size per file. |
| `ATTACHMENT_CHUNK_SIZE` | `500` | Word count per parsed document chunk. |
| `ATTACHMENT_CHUNK_OVERLAP` | `50` | Word overlap between adjacent chunks. |

---

## 🚀 Setup & Execution Guide

### 1. Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+ & npm
- **Elasticsearch**: 8.x+ / 9.x+ instance accessible with SSL & vector search enabled.
- **Embedding Model**: `all-MiniLM-L6-v2` downloaded locally (or adjust `MODEL_PATH` in `app/config.py`).

### 2. Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn elasticsearch sentence-transformers pdfplumber python-docx pandas requests pydantic
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Verify backend health:
   ```bash
   curl http://127.0.0.1:8000/
   # Returns: {"status": "healthy", "service": "synapse-api"}
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend/my-ui
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
4. Open your browser at `http://localhost:5173` to interact with the interface.

---

## 📡 API Reference

### `POST /chat`
Submits a conversation turn, executes hybrid search, builds context, and queries the LLM.

**Request Body:**
```json
{
  "session_id": "session_1729253400_abc123",
  "messages": [
    { "role": "user", "content": "What are the latest compliance guidelines?" }
  ],
  "top_k": 20,
  "attachment_ids": ["f89d3421-4f11-4389-a212-094191d4e743"]
}
```

**Response Body:**
```json
{
  "reply": "According to the compliance document...",
  "sources": [
    {
      "source_file": "guidelines_v2.pdf",
      "category": "Compliance",
      "version": "2.1",
      "created_by": "Auditor",
      "created_date": "2026-01-15"
    }
  ],
  "llm_called": true,
  "hits_used": 14,
  "max_score": 0.0321,
  "attachments_used": 1
}
```

---

### `POST /attachments/upload`
Uploads, parses, chunks, embeds, and indexes an attachment.

- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `session_id`: (string) ID of current chat session.
  - `file`: (binary) Uploaded file (`.pdf`, `.docx`, `.txt`, `.csv`).

**Response Body:**
```json
{
  "success": true,
  "attachment": {
    "attachment_id": "d0597ba1-8c4d-45df-bbbf-568eaec81781",
    "filename": "quarterly_report.pdf",
    "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "stored_filename": "d0597ba1-8c4d-45df-bbbf-568eaec81781.pdf",
    "chunk_count": 18,
    "status": "indexed"
  }
}
```

---

### `DELETE /attachments/{attachment_id}`
Deletes all Elasticsearch chunks associated with the specified attachment ID.

**Response Body:**
```json
{
  "success": true,
  "attachment_id": "d0597ba1-8c4d-45df-bbbf-568eaec81781",
  "message": "Attachment deleted successfully."
}
```

---

### `GET /attachments/{attachment_id}`
Returns metadata for the indexed attachment.

---

## 💡 Troubleshooting & Notes for AI Agents

- **Elasticsearch Certificate**: If SSL verification errors occur, ensure `ES_CERT_PATH` in [`app/config.py`](file:///c:/Users/BIT/Desktop/new/app/config.py) points to an accessible certificate or configure SSL verification parameters in [`app/services/elasticsearch_service.py`](file:///c:/Users/BIT/Desktop/new/app/services/elasticsearch_service.py).
- **Local Embedding Model Path**: `SentenceTransformer` loads from `MODEL_PATH`. If running in a new environment without `C:/models/all-MiniLM-L6-v2`, update this to the HuggingFace identifier `"sentence-transformers/all-MiniLM-L6-v2"`.
- **Upload Storage**: Files are saved to `data/uploads/originals`. Ensure the process has write permissions for `data/uploads`.
