# Friday - RAG Pipeline

A RAG (Retrieval-Augmented Generation) pipeline built with FastAPI and Convex.

## Prerequisites

- Python 3.12+
- Node.js and npm (for Convex)
- [uv](https://github.com/astral-sh/uv) package manager

## Environment Setup

1. Clone the repository:

```bash
git clone git@github.com:Anas-github-acc/texo-rag.git # ssh
git clone https://github.com/Anas-github-acc/texo-rag.git # http
cd texo-rag
```

2. Create a `.env.local` file in the root directory:

```bash
cp .env.template .env.local
```

3. Fill in your environment variables in `.env.local`:

```env
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_API_URL=your_qdrant_url
GEMINI_API_KEY=your_gemini_api_key
CONVEX_DEPLOYMENT=your_convex_deployment
CONVEX_URL=your_convex_url
```

## Run the convex development server

```bash
npx convex dev
```


## Running the Server

### On Windows

1. Open PowerShell and navigate to the project directory
2. Run the development server:

```powershell
./dev.ps1
```

Additional options:

```powershell
./dev.ps1 --help    # Show help
./dev.ps1 --fix     # Run ruff check --fix
./dev.ps1 format    # Run ruff format
```

### On Linux/MacOS

1. Open terminal and navigate to the project directory
2. Make the script executable (first time only):

```bash
chmod +x dev.sh
```

3. Run the development server:

```bash
./dev.sh
```

## What the Scripts Do

Both `dev.ps1` and `dev.sh` perform these tasks:

1. Check for existing virtual environment
2. Create virtual environment if it doesn't exist
3. Activate the virtual environment
4. Install/update dependencies using `uv`
5. Start the FastAPI server using uvicorn

## Server Details

- The server runs on `http://0.0.0.0:8000`
- API documentation available at `http://0.0.0.0:8000/docs`
- Health check endpoint: `http://0.0.0.0:8000/health`

## Development Commands

### Run the FastAPI server

### Format Code

Windows:

```powershell
./dev.ps1 format
```

Linux/MacOS:

```bash
./dev.sh format
```

### Fix Linting Issues

Windows:

```powershell
./dev.ps1 --fix
```

## Troubleshooting

1. If you get permission errors on Linux/MacOS:

```bash
chmod +x dev.sh
```

2. If virtual environment isn't activating on Windows:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. If `uv` is not found:

```bash
# Install uv
pip install uv
```

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── routes.py
│   │   └── pipeline.py
│   └── main.py
├── dev.ps1
├── dev.sh
├── pyproject.toml
├── .env.template
└── .env.local
```
