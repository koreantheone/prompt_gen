# Keyword RAG Service

## Prerequisites
- Node.js 18+
- Python 3.10+
- OpenAI API Key
- DataforSEO API Credentials

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/` with:
```
OPENAI_API_KEY=your_key
DATAFORSEO_API_LOGIN=your_login
DATAFORSEO_API_PASSWORD=your_password
```

Run the server:
```bash
uvicorn main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)
