# Claude Yap - AI Podcast Generator

## 🎧 Overview

Claude Yap is an AI-powered podcast generator that leverages Claude AI to create engaging audio content. It offers two primary modes of operation:

- **File Summary Mode**: Upload PDFs and Claude will summarize and discuss their content in podcast format
- [TODO: coming next] **AI Research Mode**: Claude researches a topic you provide and generates podcast content based on that research

The application supports various podcast formats (debate, conversation, educational) with different numbers of participants, allowing for a wide range of audio content styles.

## ✨ Features

- **Multiple Podcast Formats**: Choose between debate-style, conversational podcast, or educational formats
- **Customizable Participants**: Select between one, two, or three speakers for your podcast
- **PDF Processing**: Upload PDF documents for Claude to analyze and discuss

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python 3.9+
- Claude API access

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/claude-yap.git
cd claude-yap
```

2. Set up the backend

```bash
cd backend
pip install -r requirements.txt
# Create a .env file with your Claude API key
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

3. Set up the frontend

```bash
cd ../frontend
npm install
```

### Running the Application

1. Start the backend server

```bash
cd backend
python app.py
```

2. Start the frontend development server

```bash
cd ../frontend
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

## 🏗️ Project Structure

```
clause-yap/
├── backend/            # Python backend with Claude API integration
│   ├── app.py          # Main Flask application
│   └── requirements.txt # Python dependencies
└── frontend/           # React frontend
    ├── app/            # Application code
    │   ├── routes/     # Page components
    │   └── app.css     # Global styles
    └── package.json    # Node dependencies
```

## 🧩 How It Works

1. **Select a Podcast Format**: Choose between debate, conversation, or educational styles
2. **Choose Number of Participants**: Select one, two, or three speakers
3. **Select Content Source**: Either AI research or PDF document summary
4. **Provide Input**: Enter research topic or upload PDF files
5. **Generate Podcast**: Claude processes your request and generates audio content
6. **Download & Enjoy**: Get your AI-generated podcast ready to share

## 🖼️ Screenshots

TODO: 

## 🛠️ Technologies Used

### Frontend
- React with React Router
- Tailwind CSS for styling
- Framer Motion for animations

### Backend
- Python with Flask
- Claude API for AI content generation
- PDF processing libraries


