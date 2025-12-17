#!/bin/bash

# Start script for Super Personal Agent

echo "🚀 Starting Super Personal Agent..."
echo ""

# Check if backend dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing backend dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
fi

# Start backend
echo "🔧 Starting FastAPI backend on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "🌐 Starting frontend server on http://localhost:8080"
echo "💡 Open http://localhost:8080 in your browser"
echo ""
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Web UI is running!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait

