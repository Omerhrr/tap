# Tap & Split

A real-time collaborative bill-splitting application where users join a session via code/QR, scan receipts to auto-extract items, assign items to people via drag-and-drop, and settle payments instantly.

## Features

- **Real-time Collaboration**: WebSocket-based updates across all connected clients
- **Receipt Scanning**: OCR-powered receipt parsing using Tesseract
- **Drag & Drop Assignment**: Assign items to participants with intuitive UI
- **Smart Settlement**: Optimized transaction calculation to minimize payments
- **Cross-platform**: Works on mobile, desktop (Kivy/KivyMD)
- **Material Design**: Beautiful UI with KivyMD components

## Architecture

```
┌─────────────┐      WebSocket       ┌─────────────┐
│  Kivy App   │ ◄──────────────────► │  FastAPI    │
│  (Mobile/   │      HTTP/REST       │   Server    │
│   Desktop)  │ ◄──────────────────► │             │
└──────┬──────┘                      └──────┬──────┘
       │                                      │
       │         ┌─────────────┐              │
       └────────►│  Camera/    │              │
                 │  Gallery    │              │
                 └─────────────┘              │
                                              │
       ┌─────────────┐         │
       │   SQLite/   │◄────────┘
       │  PostgreSQL │
       │   (Async)   │
       └─────────────┘
              │
       ┌─────────────┐
       │  Tesseract  │
       │    OCR      │
       └─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Tesseract OCR (for receipt scanning)
- PostgreSQL (optional, for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Omerhrr/tap.git
   cd tap/tap_split
   ```

2. **Install Tesseract OCR**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # macOS
   brew install tesseract

   # Windows
   # Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Backend Setup**
   ```bash
   cd backend

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Run the server
   uvicorn app.main:app --reload --port 8000
   ```

4. **Frontend Setup (Kivy/KivyMD)** (in a new terminal)
   ```bash
   cd kivy_app

   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Run the app
   python main.py
   ```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Documentation

Once the backend is running, access the interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create a new session |
| GET | `/sessions/{code}` | Get session details |
| POST | `/sessions/{id}/join` | Join a session |
| POST | `/sessions/{id}/lock` | Lock session for settlement |
| POST | `/sessions/{id}/settle` | Mark session as settled |
| POST | `/sessions/{id}/items` | Add item to session |
| POST | `/items/{id}/assign` | Assign item to participant |
| POST | `/ocr` | Process receipt image |

### WebSocket

Connect to `ws://localhost:8000/ws/{session_id}` for real-time updates.

**Message Types:**
- `participant_joined` - New participant joined
- `item_added` - New item added
- `item_assigned` - Item assigned to participant
- `session_locked` - Session locked for settlement
- `session_settled` - Session marked as settled

## Project Structure

```
tap_split/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── crud.py              # Database operations
│   │   ├── deps.py              # Dependencies
│   │   ├── routers/
│   │   │   ├── sessions.py
│   │   │   ├── items.py
│   │   │   ├── assignments.py
│   │   │   └── ocr.py
│   │   ├── services/
│   │   │   ├── ocr_service.py
│   │   │   └── calculation.py
│   │   └── websocket.py
│   ├── requirements.txt
│   └── Dockerfile
├── kivy_app/
│   ├── main.py                  # Entry point
│   ├── state.py                 # State management
│   ├── api_client.py            # HTTP client
│   ├── screens/
│   │   ├── home_screen.py
│   │   └── session_screen.py
│   ├── components/
│   │   ├── dialogs.py
│   │   ├── item_card.py
│   │   └── participant_chip.py
│   └── requirements.txt
├── flet_app/                    # Legacy Flet frontend (deprecated)
├── docker-compose.yml
└── README.md
```

## Development

### Running Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
# Using Alembic (if configured)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite+aiosqlite:///./tap_split.db
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
CORS_ORIGINS=["*"]
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

## Currency

The app uses Nigerian Naira (₦) as the default currency.

## License

MIT License - see LICENSE file for details.
