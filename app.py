from flask import Flask, request, jsonify, render_template_string
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
import requests

load_dotenv()

# Your OpenRouter API key and headers
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",  # Set this to your site if hosted
    "X-Title": "PDF Quiz Generator"
}

app = Flask(__name__)

# === FRONTEND HTML (you can replace with a template if preferred) ===
with open("templates/index.html", encoding="utf-8") as f:
    HTML = f.read()

# === Function to extract text from PDF (with OCR fallback) ===
def extract_text(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        page_text = page.get_text()
        if page_text.strip() == "":
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
        text += page_text
    return text

# === Function to call DeepSeek API ===
def generate_quiz(text):
    prompt = f"""
Create 5 multiple-choice questions based on the following content. Each question should have:
- 4 answer choices labeled A–D
- The correct answer labeled like "Answer: B"

Only show questions and options, not explanations.

Content:
{text[:1000]}
"""

    data = {
        "model": "deepseek/deepseek-r1",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json=data
    )

    try:
        result = response.json()
        print("=== DEBUG API RESPONSE ===")
        print(result)

        # Defensive check to prevent crash
        if "choices" in result:
            return result['choices'][0]['message']['content']
        else:
            return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# === ROUTES ===
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/generate_quiz', methods=['POST'])
def quiz():
    if 'pdf_file' not in request.files:
        return jsonify({"quiz": "No file uploaded!"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"quiz": "No selected file!"}), 400

    try:
        text = extract_text(file)
        quiz = generate_quiz(text)
        return jsonify({"quiz": quiz})
    except Exception as e:
        return jsonify({"quiz": f"An error occurred: {str(e)}"}), 500

# === Run Flask App ===
if __name__ == '__main__':
    app.run(debug=True)
