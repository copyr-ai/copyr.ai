#!/bin/bash

# copyr.ai Development Setup Script
echo "🚀 Starting copyr.ai development environment..."

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "📦 Loading environment variables from .env"
    export $(cat .env | xargs)
else
    echo "⚠️  No .env file found, using .env.example as template"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example template"
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists node; then
    echo "❌ Node.js is required but not installed. Please install Node.js 18+"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed. Please install npm"
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.9+"
    exit 1
fi

if ! command_exists pip; then
    echo "❌ pip is required but not installed. Please install pip"
    exit 1
fi

echo "✅ All dependencies found"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd apps/frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi
cd ../..

# Install backend dependencies
echo "🐍 Installing backend dependencies..."
cd apps/backend
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
cd ../..

echo "✅ All dependencies installed successfully"

# Function to kill processes on script exit
cleanup() {
    echo "🛑 Shutting down development servers..."
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start backend server
echo "🐍 Starting FastAPI backend on port 8000..."
cd apps/backend
uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ../..

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "⚛️  Starting Next.js frontend on port 3000..."
cd apps/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# Wait a moment for servers to start
sleep 3

echo ""
echo "🎉 Development environment is ready!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all servers"

# Try to open browser (works on most systems)
if command_exists xdg-open; then
    xdg-open http://localhost:3000 >/dev/null 2>&1
elif command_exists open; then
    open http://localhost:3000 >/dev/null 2>&1
elif command_exists start; then
    start http://localhost:3000 >/dev/null 2>&1
fi

# Wait for user to stop the script
wait