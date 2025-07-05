# Podcast Machine - AI Podcast Generator

## 🎧 Overview

Podcast Machine transforms PDFs and research topics into engaging, multi-voice podcasts using Claude AI and advanced text-to-speech technology. The app creates natural-sounding conversations in various formats, with custom voices for each speaker and automatically-generated cover art.

## ✨ Key Features

- **Intelligent PDF Analysis**: Upload PDFs and Podcast Machine will analyze, summarize, and transform them into conversational podcasts
- **Multiple Podcast Formats**:
  - **Podcast Style**: Traditional host/guest conversational format
  - **Debate Style**: Two perspectives debating topics from the source material
  - **Duck Mode**: Educational teacher/student dialogue format
- **Multi-Speaker Natural Voices**: Uses Cartesia TTS API to generate distinctly different voices for each speaker
- **Automated Cover Art**: Creates custom podcast covers using Claude's artifact generation or Stable Diffusion
- **Advanced Audio Player**: Professional-grade player with keyboard shortcuts, playback speed control, and progress tracking
- **Video Conference Integration**: Discuss podcasts via video call through Tavus API integration
- **Real-Time Progress Tracking**: Monitor podcast generation progress with detailed status updates

## 🚀 Getting Started

### Prerequisites

- Node.js (v16+)
- Python 3.9+
- Claude API key (Anthropic)
- Cartesia API key (for text-to-speech)
- Hugging Face API token (for cover art generation)
- Tavus API credentials (for video conference)

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
# Create .env file using example template
cp .env.example .env
# Fill in your API keys in the .env file
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

## 🖥️ Technologies Used

### Frontend
- React with React Router
- Framer Motion for animations
- Advanced HTML5 audio player

### Backend
- Python with Flask
- Claude 3.7 Sonnet and Claude 3 Opus for content generation
- Cartesia API for high-quality multi-speaker text-to-speech
- Claude artifacts tool and Hugging Face Stable Diffusion for cover art
- Tavus API for video conference integration
- FFmpeg for audio processing

## 🧩 How It Works

1. **Upload Content**: Submit PDFs for analysis or provide a research topic
2. **Select Format**: Choose between podcast, debate, or educational "duck" mode
3. **Script Generation**: Claude analyzes content and creates a conversational script
4. **Voice Assignment**: The system automatically assigns distinct voices to each speaker
5. **Audio Generation**: Cartesia TTS converts the script into natural-sounding multi-voice audio
6. **Cover Art Creation**: Automatically generates custom cover art for each podcast
7. **Playback & Sharing**: Listen to your podcast with advanced playback controls
8. **AI Video Discussion**: Have 1-on-1 video calls with AI personalities to discuss your podcasts

See example generated script in example_script.txt

## 🎮 Advanced Features

### Audio Player Controls
- Keyboard shortcuts for playback control (space, arrows, number keys)
- Variable playback speed (0.5x to 2x)
- Jump forward/backward functionality

### Video Conference
Discuss podcasts with AI personalities through Tavus API video conference integration

### Library Management
- Track listened/unlistened podcasts
- Rename and organize your podcast collection

## 🛠️ Development

### Project Structure

- **Frontend**: React SPA with responsive UI and advanced audio player
- **Backend**: Flask API with Claude integration, audio processing, and data management

### Key Components

- **Claude Integration**: Uses both Claude 3.7 Sonnet and Claude 3 Opus for different tasks
- **Script Processing**: Intelligently parses scripts to identify speakers and dialogue
- **TTS Engine**: Uses Cartesia's advanced TTS API for natural multi-speaker audio
- **Cover Art Generation**: Uses either Claude artifacts (SVG) or Stable Diffusion (PNG)

