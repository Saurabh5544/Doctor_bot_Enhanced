# 🏥 Medical Chatbot — Enhanced Edition

An AI-powered medical assistant chatbot built with **Flask**, **LangChain**, **Pinecone**, and **GPT-4o-mini**. Ask health-related questions and get intelligent answers based on verified medical literature using RAG (Retrieval-Augmented Generation).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Medical Q&A** | RAG-based answers from medical textbooks via Pinecone + GPT-4o-mini |
| 🔐 **User Authentication** | Register/Login with hashed passwords and session management |
| 🗄️ **SQLite Database** | Persistent storage for users and chat history |
| 💬 **Chat History** | View, resume, and delete past conversations via sidebar |
| 🎙️ **Voice Input** | Speech-to-text for hands-free questions |
| 🔊 **Voice Output** | Text-to-speech for bot responses |
| 🌙 **Dark/Light Mode** | Theme toggle with smooth transitions |
| ⚕️ **Medical Disclaimer** | Legal notice that this is not real medical advice |
| 📱 **Responsive Design** | Works on desktop, tablet, and mobile |
| 🛡️ **XSS Protection** | All user input sanitized before rendering |
| ⏳ **Typing Indicator** | Animated dots while bot is thinking |
| 🎯 **Quick Prompts** | Pre-built health questions for easy start |

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-Login, Flask-WTF
- **AI/ML:** LangChain, OpenRouter (GPT-4o-mini), HuggingFace Embeddings
- **Vector DB:** Pinecone (Serverless)
- **Database:** SQLite
- **Frontend:** HTML5, CSS3 (Glassmorphism), Vanilla JavaScript
- **APIs:** Web Speech API (STT/TTS)

---

## 📁 Project Structure

```
Doctor_bot_Enhanced/
├── app.py                 # Main Flask application
├── db.py                  # SQLite database module
├── store_index.py         # One-time Pinecone indexing script
├── setup.py               # Package setup
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (DO NOT COMMIT)
├── .env.example           # Environment template (safe to commit)
├── .gitignore             # Git ignore rules
├── Data/
│   ├── Medical_book.pdf          # Medical reference PDF
│   └── National Formulary of India.pdf
├── src/
│   ├── __init__.py
│   ├── helper.py          # PDF loading, text splitting, embeddings
│   └── prompt.py          # System prompt for medical AI
├── static/
│   ├── style.css          # Chat page styles (dark/light themes)
│   └── auth.css           # Login/Register page styles
├── templates/
│   ├── chat.html          # Main chat interface
│   ├── login.html         # Login page
│   └── register.html      # Registration page
└── research/
    └── trials.ipynb       # Research notebook
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Pinecone account (free tier works)
- OpenRouter API key

### 1. Clone & Setup Environment
```bash
git clone <your-repo-url>
cd Doctor_bot_Enhanced

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Index Medical Data (First Time Only)
```bash
python store_index.py
```
This reads PDFs from `Data/`, splits them into chunks, and uploads to your Pinecone index.

### 4. Run the Application
```bash
python app.py
```
Visit **http://localhost:8000** in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/login` | ❌ | Login page |
| POST | `/login` | ❌ | Authenticate user |
| GET | `/register` | ❌ | Register page |
| POST | `/register` | ❌ | Create account |
| GET | `/logout` | ✅ | Logout user |
| GET | `/` | ✅ | Chat interface |
| POST | `/get` | ✅ | Send message & get AI response |
| GET | `/history` | ✅ | Get all chat sessions |
| GET | `/history/<id>` | ✅ | Get session messages |
| DELETE | `/history/<id>` | ✅ | Delete a session |
| DELETE | `/history` | ✅ | Delete all history |

---

## ⚠️ Medical Disclaimer

> This chatbot provides **general health information only**. It is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions regarding a medical condition.

---

## 👨‍💻 Author

**Saurabh Sharma**  
📧 sharmasaurabh1105@gmail.com

---

## 📄 License

This project is for educational purposes.