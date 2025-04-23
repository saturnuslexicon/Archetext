from flask import Flask, render_template, request, jsonify, session
import os
import requests
from dotenv import load_dotenv
from flask_session import Session

# --- Semantic Kernel (SK 1.x) ---
from semantic_kernel import Kernel
from semantic_kernel.connectors.memory.chroma import ChromaMemoryStore
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

# --- Init App + Load Keys ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
print("🔑 Loaded GROQ key:", API_KEY[:10] if API_KEY else "❌ NOT FOUND")

app = Flask(__name__)
app.config["SECRET_KEY"] = "archetext_super_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# --- Semantic Kernel Memory Setup ---
kernel = Kernel()
memory_store: MemoryStoreBase = ChromaMemoryStore(persist_directory="memory_store")


# --- GROQ Request Wrapper ---
def generate_story(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system",
                "content": "You are the Archetext Oracle. You respond poetically, symbolically, and intelligently to the user's inner world."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error while summoning the story: {e}"


# --- Oracle Terminal Route ---
@app.route("/", methods=["GET", "POST"])
def index():
    if "messages" not in session:
        session["messages"] = []

    if request.method == "POST":
        prompt = request.form.get("prompt")
        if prompt:
            response = generate_story(prompt)
            session["messages"].append({"role": "user", "content": prompt})
            session["messages"].append({"role": "oracle", "content": response})
            session.modified = True

    return render_template("index.html", messages=session["messages"])


# --- Lore Search Route (SK 1.x) ---
@app.route("/search-lore", methods=["GET"])
def search_lore():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query required"}), 400

    try:
        results = memory_store.search("night_job_lore", query, limit=3)
        lore_matches = [r.text for r in results]
        return jsonify({"query": query, "results": lore_matches})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Run App ---
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
