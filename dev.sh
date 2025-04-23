username=$(whoami)

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Virtual environment found. Activating..."
    source .venv/bin/activate
else
    echo "$username, Bro you do not have a virtual environment set up yet. so i have to create one and then install the dependencies... such a pain in ass"
    echo "while i am Creating a virtual environment...,you understand this when ever you have to  run ./dev.sh to run the server"
    uv venv
    source .venv/bin/activate
    uv sync
fi

# uvicorn main:app --host 0.0.0.0 --port 8000 --reload

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload