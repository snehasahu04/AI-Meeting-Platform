# Meeting AI Platform

Meeting AI Platform is a full-stack application for capturing, processing, and analyzing meeting conversations. It supports transcript/audio ingestion, live WebSocket transcription, meeting summaries, action item extraction, sentiment analysis, topic clustering, semantic search, RAG-based Q&A, and an AI meeting agent.

The project includes a FastAPI backend, React frontend, optional Streamlit dashboard, SQLite storage, FAISS vector search, Kafka event topics, and Groq-powered LLM/transcription workflows.

## Features

| Area | Capability |
| --- | --- |
| Meeting management | Create meetings, list meetings, view meeting details |
| Ingestion | Upload audio files or ingest raw transcript text |
| Live transcription | WebSocket endpoint for real-time transcript chunks |
| Summaries | Generate and cache AI meeting summaries |
| Action items | Extract task, owner, deadline, and status from transcripts |
| Sentiment | Analyze sentiment per transcript chunk and aggregate meeting sentiment |
| Topics | Cluster transcript chunks and return top topic terms |
| Analytics | Overview stats, engagement score, sentiment timeline, speaker placeholder |
| RAG | Semantic transcript search and question answering over ingested meetings |
| Agent workflow | Escalation checks, unresolved topics, missed action items, follow-up reminders |
| Frontend | React UI for meetings, ingestion, RAG chat, dashboard, and live transcript |
| Dashboard | Streamlit dashboard with charts and meeting analytics |

## Tech Stack

| Layer | Tools |
| --- | --- |
| Backend API | Python, FastAPI, Uvicorn |
| Frontend | React, React Router, Axios, Recharts, Lucide React |
| AI / LLM | Groq, Llama 3, Whisper |
| Embeddings | FastEmbed |
| Vector search | FAISS |
| Machine learning | scikit-learn, TextBlob |
| Messaging | Kafka |
| Database | SQLite |
| Dashboard | Streamlit, Plotly, Pandas |
| Testing | pytest, httpx |
| Containerization | Docker, Docker Compose |

## Project Structure

```text
meeting_AI_platform/
+-- backend/
|   +-- app/
|   |   +-- main.py                    # FastAPI app entry point
|   |   +-- config.py                  # Environment and app settings
|   |   +-- llm.py                     # Groq LLM helper
|   |   +-- agent/                     # AI meeting agent workflow
|   |   +-- api/routes/                # REST API route groups
|   |   +-- db/models.py               # SQLite database helpers
|   |   +-- kafka/                     # Kafka producer and consumer code
|   |   +-- ml/                        # Clustering, anomaly detection, TF-IDF
|   |   +-- rag/                       # Chunking, FAISS store, retrieval, generation
|   |   +-- services/                  # Transcription, embeddings, summaries, sentiment
|   |   +-- streaming/audio_stream.py  # WebSocket transcription flow
|   +-- dashboard/app.py               # Streamlit dashboard
|   +-- tests/                         # pytest test suite
|   +-- vector_store/scripts/          # FAISS index build script
|   +-- requirements.txt
|   +-- Dockerfile
+-- frontend/
|   +-- public/
|   +-- src/
|   |   +-- api.js                     # Frontend API client
|   |   +-- App.js                     # React routing/layout
|   |   +-- pages/                     # Dashboard, Meetings, Ingest, RAG, Live views
|   +-- package.json
+-- data/                              # Local transcript/audio data
+-- vector_store/                      # Local FAISS index and metadata
+-- docker-compose.yml
+-- README.md
```

## Prerequisites

Install these before running locally:

| Tool | Recommended version |
| --- | --- |
| Python | 3.11 or newer |
| Node.js | 18 or newer |
| Docker Desktop | Required for Kafka / full Docker setup |
| ffmpeg | Required for audio handling |

On Windows, install ffmpeg with:

```bash
winget install ffmpeg
```

## Environment Variables

Create a `.env` file in the project root or in `backend/`.

```env
GROQ_API_KEY=your_groq_api_key
KAFKA_BOOTSTRAP=localhost:9092
DATABASE_URL=sqlite:///./meeting_platform.db
WHISPER_MODEL=whisper-large-v3
```

Only `GROQ_API_KEY` is required for LLM and Whisper-powered features. Kafka defaults to `localhost:9092` and SQLite defaults to a local database file.

## Run Locally

### 1. Start Kafka

From the project root:

```bash
docker compose up kafka kafka-init -d
```

This starts Kafka in KRaft mode and creates the required topics.

### 2. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

If `pyaudio` fails on Windows, install the needed audio dependency separately for your system and then rerun the install.

### 3. Start the backend

From the project root:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

| Service | URL |
| --- | --- |
| API health check | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### 4. Start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:3000
```

### 5. Start the Streamlit dashboard

Optional:

```bash
cd backend
streamlit run dashboard/app.py
```

Dashboard URL:

```text
http://localhost:8501
```

## Run with Docker Compose

From the project root:

```bash
docker compose up --build
```

Services:

| Service | URL / Port |
| --- | --- |
| Backend | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| Streamlit dashboard | http://localhost:8501 |
| Kafka | localhost:9092 |

## API Reference

### Health

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | API health check |

### Meetings

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/meetings/create` | Create a new meeting |
| GET | `/meetings/` | List all meetings |
| GET | `/meetings/{meeting_id}` | Get meeting details |
| GET | `/meetings/{meeting_id}/summary` | Generate or fetch cached summary |
| GET | `/meetings/{meeting_id}/action-items` | Generate or fetch cached action items |
| GET | `/meetings/{meeting_id}/sentiment` | Analyze meeting sentiment |
| GET | `/meetings/{meeting_id}/topics` | Cluster transcript topics |
| POST | `/meetings/{meeting_id}/follow-up` | Generate follow-up email |

### Ingestion

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/ingest/text` | Ingest raw transcript text |
| POST | `/ingest/audio` | Upload audio, transcribe it, chunk it, and index it |

### RAG

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/rag/search` | Return similar transcript chunks |
| POST | `/rag/ask` | Ask a question over indexed meeting transcripts |

### Analytics

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/analytics/overview` | Total meetings, chunks, and vectors |
| GET | `/analytics/{meeting_id}/engagement` | Engagement score, sentiment, and anomalies |
| GET | `/analytics/{meeting_id}/timeline` | Sentiment timeline by transcript chunk |
| GET | `/analytics/{meeting_id}/speakers` | Speaker analytics placeholder |

### Agent

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/agent/{meeting_id}/run` | Run the meeting agent workflow |

### Streaming

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/stream/transcript/{meeting_id}` | Fetch stored live transcript chunks |
| WS | `/stream/transcript?meeting_id={id}&title={title}` | Send live audio frames for transcription |

## Example Requests

### Create a meeting

```bash
curl -X POST "http://localhost:8000/meetings/create" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Sprint Planning\"}"
```

### Ingest transcript text

```bash
curl -X POST "http://localhost:8000/ingest/text" \
  -H "Content-Type: application/json" \
  -d "{\"transcript\":\"Alice will prepare the deployment plan by Friday. Bob will review the API logs.\"}"
```

### Ask a RAG question

```bash
curl -X POST "http://localhost:8000/rag/ask" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"What action items were discussed?\",\"top_k\":5}"
```

### Get a meeting summary

```bash
curl "http://localhost:8000/meetings/{meeting_id}/summary"
```

### Run the meeting agent

```bash
curl -X POST "http://localhost:8000/agent/{meeting_id}/run"
```

## Kafka Topics

| Topic | Purpose |
| --- | --- |
| `transcripts` | Full meeting transcripts |
| `raw_audio` | Raw/live audio events |
| `summaries` | Generated meeting summaries |
| `action_items` | Extracted action items |
| `alerts` | Escalations and anomaly alerts |
| `speaker_events` | Speaker activity events |

## Database Tables

The backend creates these SQLite tables automatically at startup:

| Table | Purpose |
| --- | --- |
| `meetings` | Meeting metadata |
| `meeting_transcripts` | Transcript chunks |
| `meeting_summaries` | Cached summaries |
| `meeting_action_items` | Extracted action items |
| `meeting_speakers` | Speaker analytics placeholder |
| `meeting_embeddings` | Metadata for indexed chunks |

## Testing

Run backend tests from the project root:

```bash
pytest backend/tests -q
```

Or run a focused subset:

```bash
pytest backend/tests/test_api.py -q
pytest backend/tests/test_ml.py backend/tests/test_rag.py -q
```

Frontend tests can be run from the frontend folder:

```bash
cd frontend
npm test
```

## Common Troubleshooting

| Problem | Fix |
| --- | --- |
| `GROQ_API_KEY` errors | Add a valid key to `.env` or `backend/.env` |
| Kafka connection warnings | Start Kafka with `docker compose up kafka kafka-init -d` |
| Audio transcription fails | Confirm ffmpeg is installed and the audio file format is supported |
| `pyaudio` install fails | Install OS-level PortAudio/PyAudio support, then rerun pip install |
| Frontend cannot reach backend | Confirm backend is running on `http://localhost:8000` |
| Empty RAG answers | Ingest transcript/audio first so FAISS has indexed chunks |

## Suggested Documentation Additions

Use this README as the base project documentation. Helpful next sections to add later:

- Architecture diagram
- Sequence diagram for ingestion and RAG
- Screenshots of the React UI and Streamlit dashboard
- Deployment notes for production
- Environment-specific configuration guide
- API response examples for each endpoint
