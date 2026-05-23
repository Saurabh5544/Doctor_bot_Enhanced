"""
Medical Chatbot — Enhanced Flask Application
Features: User authentication, chat history, RAG-based medical Q&A
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
from db import (
    create_user, authenticate_user, get_user_by_id,
    save_message, get_chat_sessions, get_session_messages,
    delete_chat_session, delete_all_chat_history
)
import os
import uuid

# ─── Flask Setup ────────────────────────────────────────────────

app = Flask(__name__, template_folder="templates")
load_dotenv()

# Secret key for sessions & CSRF
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())

# CSRF Protection
csrf = CSRFProtect(app)

# ─── Flask-Login Setup ──────────────────────────────────────────

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access the medical chatbot."
login_manager.login_message_category = "info"


class User(UserMixin):
    """Flask-Login user model wrapping our DB user."""
    def __init__(self, user_dict):
        self.id = user_dict["id"]
        self.username = user_dict["username"]
        self.email = user_dict["email"]


@login_manager.user_loader
def load_user(user_id):
    user_dict = get_user_by_id(int(user_id))
    if user_dict:
        return User(user_dict)
    return None


# ─── Environment Variables ──────────────────────────────────────

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
api_base = os.getenv("OPENROUTER_API_BASE")

# Validate required env vars
missing_keys = []
if not PINECONE_API_KEY:
    missing_keys.append("PINECONE_API_KEY")
if not OPENROUTER_API_KEY:
    missing_keys.append("OPENROUTER_API_KEY")
if not api_base:
    missing_keys.append("OPENROUTER_API_BASE")

if missing_keys:
    print(f"[WARNING] Missing environment variables: {', '.join(missing_keys)}")
    print("   Please check your .env file. See .env.example for reference.")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY or ""
os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY or ""

# ─── RAG Chain Setup ────────────────────────────────────────────

embeddings = download_hugging_face_embeddings()

index_name = "medical-bot"
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})

llm = ChatOpenAI(
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=api_base,
    model="gpt-4o-mini"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)


# ─── Auth Routes ────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("login.html")

        user_dict = authenticate_user(email, password)
        if user_dict:
            user = User(user_dict)
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not all([username, email, password, confirm_password]):
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        success, message = create_user(username, email, password)
        if success:
            flash(message, "success")
            return redirect(url_for("login"))
        else:
            flash(message, "error")

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ─── Chat Routes ────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("chat.html", username=current_user.username)


@app.route("/get", methods=["POST"])
@login_required
@csrf.exempt  # AJAX calls handle CSRF via header
def chat():
    msg = request.form.get("msg", "").strip()
    session_id = request.form.get("session_id", str(uuid.uuid4()))

    if not msg:
        return jsonify({"error": "Empty message"}), 400

    print(f"[{current_user.username}] User: {msg}")

    # Generate session title from first message (first 50 chars)
    sessions = get_chat_sessions(current_user.id)
    session_exists = any(s["session_id"] == session_id for s in sessions)
    session_title = msg[:50] if not session_exists else None

    # Save user message
    save_message(current_user.id, session_id, "user", msg, session_title)

    try:
        response = rag_chain.invoke({"input": msg})
        answer = str(response["answer"])
        print(f"[{current_user.username}] Bot: {answer[:100]}...")
    except Exception as e:
        print(f"[ERROR] {e}")
        answer = "I'm sorry, I'm having trouble processing your request right now. Please try again later."

    # Save bot response
    save_message(current_user.id, session_id, "bot", answer)

    return jsonify({"answer": answer, "session_id": session_id})


# ─── Chat History API ───────────────────────────────────────────

@app.route("/history")
@login_required
def history():
    """Get all chat sessions for the logged-in user."""
    sessions = get_chat_sessions(current_user.id)
    return jsonify(sessions)


@app.route("/history/<session_id>")
@login_required
def session_messages(session_id):
    """Get all messages for a specific session."""
    messages = get_session_messages(current_user.id, session_id)
    return jsonify(messages)


@app.route("/history/<session_id>", methods=["DELETE"])
@login_required
@csrf.exempt
def delete_session(session_id):
    """Delete a specific chat session."""
    delete_chat_session(current_user.id, session_id)
    return jsonify({"success": True})


@app.route("/history", methods=["DELETE"])
@login_required
@csrf.exempt
def delete_all_history():
    """Delete all chat history for the logged-in user."""
    delete_all_chat_history(current_user.id)
    return jsonify({"success": True})


# ─── Run ────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
