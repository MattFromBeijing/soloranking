# Solo-leveling: AI Consulting Case Interview Platform

Solo-leveling is an AI-powered interviewer platform designed for consulting case interview practice. The platform provides real-time, interactive case interview sessions with an intelligent agent that guides candidates through multi-phase consulting interviews while providing contextual coaching and feedback.

## What is Solo-leveling?

Solo-leveling simulates realistic consulting case interviews by providing:
- **Real-time voice interaction** with an AI interviewer agent
- **Multi-phase interview flow** that mirrors actual consulting case structures
- **Intelligent context retrieval** using RAG (Retrieval-Augmented Generation) for case-specific coaching
- **Dynamic state transitions** based on user response evaluation
- **Document upload and processing** for custom case materials

The platform allows aspiring consultants to practice case interviews in a low-pressure environment while receiving intelligent feedback and guidance throughout the process.

## Technologies Used

### Backend (Python/Flask)
- **Flask** - Web framework for API endpoints and application logic
- **OpenAI Realtime API** - Powers the conversational AI agent with real-time voice capabilities
- **LiveKit** - Real-time communication infrastructure for voice/video sessions
- **FAISS (Facebook AI Similarity Search)** - Vector database for efficient similarity search
- **OpenAI Embeddings (text-embedding-3-small)** - Text vectorization for RAG pipeline
- **PyPDF2** - PDF document processing and text extraction

**Key Components:**
- `CaseAgent.py` - Core AI agent implementing functional tool calling and state management
- `RAGService.py` - RAG pipeline with 1000-character chunking, 20% overlap, and L2 normalization
- `ExtractorService.py` & `LLMExtractorService.py` - Document processing and content extraction
- API endpoints for case management, file uploads, and interview sessions

### Frontend (Next.js/React)
- **Next.js 15** - React framework with server-side rendering capabilities
- **React 19** - UI component library for interactive user interfaces
- **LiveKit React Components** - Pre-built components for real-time communication
- **TypeScript** - Type-safe development environment
- **Tailwind CSS** - Utility-first CSS framework for styling

**Key Components:**
- `InterviewRoom.tsx` - Real-time interview session interface
- `UploadForm.tsx` - Case document upload functionality
- API routes for backend integration

### RAG Pipeline Implementation
The platform implements a sophisticated RAG system featuring:
- **FAISS IndexFlatIP** for cosine similarity search
- **1000-character text chunking** with 20% overlap for optimal context preservation
- **L2 normalization** of embeddings for accurate similarity calculations
- **Vector store persistence** for efficient case data retrieval

### Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js Web   │◄──►│   Flask API      │◄──►│  OpenAI APIs    │
│   Application   │    │   (Python)       │    │  (Realtime/     │
│                 │    │                  │    │   Embeddings)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   FAISS Vector   │
                       │   Store          │
                       │   (Case Data)    │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   LiveKit        │
                       │   (Real-time     │
                       │    Communication)│
                       └──────────────────┘
```

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- OpenAI API key
- LiveKit server access

### Backend Setup
```bash
cd interview-agent
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
cd web-app
npm install
npm run dev
```

The application will be available at `http://localhost:3000` with the backend API running on `http://localhost:5000`.

## Project Structure

```
soloranking/
├── interview-agent/          # Python Flask backend
│   ├── agents/              # AI agent implementations
│   ├── api/                 # REST API endpoints
│   ├── models/              # Data models (Case, Phase)
│   ├── services/            # Core services (RAG, LLM, Extractor)
│   ├── vector_store/        # FAISS vector databases
│   └── requirements.txt     # Python dependencies
└── web-app/                 # Next.js frontend
    ├── src/app/             # Next.js app router
    │   ├── api/             # API route handlers
    │   └── components/      # React components
    └── package.json         # Node.js dependencies
```

## Current Development Directions

### Multi-Agent Architecture Migration
The platform is transitioning from a single-agent paradigm to a more sophisticated multi-agent workflow:

- 🔄 **Multi-Agent Decomposition** - Exploring OpenAI's agent builder framework to replace the monolithic agent with specialized sub-agents for different interview phases and improved context extraction

### Agent Robustness & Flow Control
Addressing critical reliability challenges in conversational state management:

- 🎯 **Flow Control & Evaluation** - Strengthening state transition mechanisms and implementing stricter guardrails to ensure consistent interview progression and accurate candidate assessment

These developments aim to create a more reliable, contextually-aware interview experience that maintains professional consulting interview standards while providing adaptive, personalized coaching.