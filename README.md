# copyr.ai

A premium copyright intelligence infrastructure platform that helps creators, publishers, and legal teams access structured, trustworthy copyright metadata.

## 🚀 Overview

copyr.ai provides comprehensive copyright intelligence through:
- **Data Collection**: Scraping and aggregating copyright information from authoritative sources
- **Structured Analysis**: Converting raw copyright data into actionable insights
- **API Access**: RESTful APIs for integrating copyright intelligence into existing workflows
- **User Interface**: Intuitive dashboard for exploring and managing copyright data

## 🏗️ Architecture

This is a monorepo containing:

- **`apps/frontend/`** - Next.js application with Tailwind CSS, shadcn/ui, and Framer Motion
- **`apps/backend/`** - FastAPI service for APIs, scraping logic, and copyright intelligence
- **`data/`** - Static data files (scraped JSON/CSV)
- **`shared/`** - Shared utilities, types, and schemas
- **`scripts/`** - Development tools and setup scripts

## 🛠️ Tech Stack

**Frontend:**
- Next.js (JavaScript)
- Tailwind CSS
- shadcn/ui components
- Framer Motion

**Backend:**
- FastAPI (Python)
- Uvicorn ASGI server
- Requests for web scraping

**Database:**
- Supabase (hosted PostgreSQL)
- Authentication and user management
- Structured data storage

## 💻 Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd copyr-ai
   cp .env.example .env
   ```

2. **Run development environment:**
   ```bash
   ./scripts/dev.sh
   ```

This will:
- Install frontend dependencies
- Install backend dependencies  
- Start frontend on http://localhost:3000
- Start backend on http://localhost:8000

### Manual Setup

**Frontend:**
```bash
cd apps/frontend
npm install
npm run dev
```

**Backend:**
```bash
cd apps/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 🌟 Features

- **Copyright Search**: Query copyright databases and registries
- **Metadata Extraction**: Structured copyright information
- **API Integration**: RESTful endpoints for developers
- **Real-time Updates**: Live data synchronization
- **Export Capabilities**: Multiple format support (JSON, CSV, PDF)

## 📖 API Documentation

Once running, visit:
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 🚦 Project Status

Currently in active development. See individual app directories for specific setup instructions and documentation.

## 📄 License

Copyright © 2024 copyr.ai. All rights reserved.