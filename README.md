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
- **User Authentication**: Simple login/logout functionality
- **Audio Generation**: Convert generated scripts into lifelike audio using text-to-speech technology

## 🚀 Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python 3.9+
- Claude API access
- Cartesia API access for text-to-speech

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
# Create a .env file with your API keys
echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" > .env
echo "CARTESIA_API_KEY=your-cartesia-api-key-here" >> .env
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
claude-yap/
├── backend/                 # Python backend with Claude API integration
│   ├── app.py               # Main Flask application
│   ├── requirements.txt     # Python dependencies
│   ├── routes/              # API route handlers
│   │   ├── audio_generation.py  # Audio generation endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── pdf_processing.py # PDF handling and script generation
│   │   ├── podcasts.py      # Podcast management
│   │   └── script_generation.py # Script generation logic
│   ├── services/            # External service integrations
│   │   ├── claude_client.py # Claude API client
│   │   └── tts_client.py    # Text-to-speech service client
│   ├── utils/               # Utility functions
│   │   └── auth_helpers.py  # Authentication helper functions
│   ├── data/                # Data storage
│   │   ├── podcasts.json    # Saved podcast data
│   │   ├── prompts.json     # User prompts data
│   │   └── users.json       # User account data
│   ├── static/              # Static files
│   │   └── audio/           # Generated audio files
│   └── outputs/             # Script output files
└── frontend/                # React frontend
    ├── app/                 # Application code
    │   ├── routes/          # Page components
    │   │   ├── create.tsx   # Podcast creation page
    │   │   ├── dashboard.tsx # Main dashboard
    │   │   ├── login.tsx    # Login page
    │   │   ├── profile.tsx  # User profile page
    │   │   └── register.tsx # Registration page
    │   ├── app.css          # Global styles
    │   ├── root.tsx         # Root component
    │   └── routes.ts        # Route definitions
    ├── public/              # Public assets
    ├── package.json         # Node dependencies
    ├── tsconfig.json        # TypeScript configuration
    └── vite.config.ts       # Vite configuration
```

## 🧩 How It Works

1. **Create an Account**: Register and login to access all features and save your podcasts
2. **Select a Podcast Format**: Choose between debate, conversation, or educational styles
3. **Choose Number of Participants**: Select one, two, or three speakers
4. **Select Content Source**: Either AI research or PDF document summary
5. **Provide Input**: Enter research topic or upload PDF files
6. **Generate Script**: Claude processes your request and generates a podcast script
7. **Convert to Audio**: The system transforms your script into lifelike audio using TTS
8. **Download & Share**: Access your finished podcast from your profile and share it

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
- Cartesia API for high-quality text-to-speech
- PDF processing libraries
