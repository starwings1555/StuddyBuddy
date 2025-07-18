from flask import Flask, request, jsonify, render_template_string, redirect
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
import requests
import math
import re
from io import BytesIO
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb.cursors


load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "PDF Quiz Generator"
}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'

mysql = MySQL(app)

CORS(app)


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

def estimate_max_questions(text):
    word_count = len(text.split())
    max_questions = math.floor(word_count / 25)
    return min(max_questions, 20)

def generate_quiz(text, question_count=10, temperature=0.9):
    max_text_length = min(3000, 1000 + (question_count * 100))
    text_sample = text[:max_text_length]

    prompt = f"""
Create exactly {question_count} multiple-choice questions based on the following content. Each question should have:
- 4 answer choices labeled A–D
- The correct answer labeled like "Answer: B" at the bottom of page for each questions

Number the questions from 1 to {question_count}.
Only show questions and options and explanations.

Content:
{text_sample}
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": "google/gemma-3-12b-it:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3000,
            "temperature": temperature
        }
    )

    try:
        result = response.json()
        if "choices" in result:
            quiz_text = result['choices'][0]['message']['content']
            actual_questions = len(re.findall(r'\d+\.', quiz_text))
            if actual_questions < question_count:
                return generate_quiz_backup(text, question_count)
            return quiz_text
        else:
            return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

def generate_quiz_backup(text, question_count=10):
    text_sample = text[:3000]
    prompt = f"""
I need EXACTLY {question_count} multiple-choice questions. No more, no less.

Format each question like this:
1. [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]

2. [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
...

New page:
Answer: 1. [Correct letter]:explanation
        2. [Correct letter]:explanation
...

Generate these questions based on this content:
{text_sample}
"""
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": "google/gemma-3-12b-it:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.5
            }
        )
        result = response.json()
        if "choices" in result:
            return result['choices'][0]['message']['content']
        else:
            return generate_fallback_questions(text, question_count)
    except Exception:
        return generate_fallback_questions(text, question_count)


def generate_fallback_questions(text, question_count):
    words = text.split()
    questions = []
    for i in range(min(question_count, 5)):
        if len(words) < 50:
            break
        start_idx = i * 50
        if start_idx + 30 > len(words):
            break
        questions.append(f"{i+1}. What is the main topic of this passage?\nA. Topic 1\nB. Topic 2\nC. Topic 3\nD. Topic 4\nAnswer: A")
    while len(questions) < question_count:
        questions.append(f"{len(questions)+1}. Which statement best summarizes the text?\nA. Summary 1\nB. Summary 2\nC. Summary 3\nD. Summary 4\nAnswer: B")
    return "\n\n".join(questions)


from flask import Flask, request, render_template


@app.route('/')
def home():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return "No user_id provided. Please log in via PHP.", 400
    
    return render_template("index.html", user_id=user_id)


@app.route('/')
def index():
    user_id = request.args.get('user_id')
    if not user_id:
        return "User ID not provided. Please log in via the PHP system.", 400

    return render_template_string(f"""
        <html>
        <head><title>Quiz Generator</title></head>
        <body>
            <h2>Welcome, User {user_id}</h2>
            <form action="/analyze_pdf" method="post" enctype="multipart/form-data">
                <input type="file" name="pdf_file" required><br><br>
                <input type="hidden" name="user_id" value="{user_id}">
                <button type="submit">Analyze PDF</button>
            </form>
        </body>
        </html>
    """)


@app.route('/analyze_pdf', methods=['POST'])
def analyze_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files['pdf_file']
    user_id = request.form.get('user_id')

    if file.filename == '':
        return jsonify({"error": "No selected file!"}), 400

    try:
        temp_file = BytesIO(file.read())
        text = extract_text(temp_file)
        max_questions = estimate_max_questions(text)

        options = []
        if max_questions >= 5:
            options.append(5)
        if max_questions >= 10:
            options.append(10)
        if max_questions >= 20:
            options.append(20)

        return jsonify({
            "user_id": user_id,
            "max_questions": max_questions,
            "options": options,
            "text_content": text[:5000]  
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/generate_quiz', methods=['POST'])
def quiz():
    try:
        data = request.json
        text = data.get('text_content', '')
        question_count = int(data.get('question_count', 10))
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        quiz = generate_quiz(text, question_count)

        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''
                INSERT INTO quizzes (user_id, quiz_content, question_count, created_at)
                VALUES (%s, %s, %s, NOW())
            ''', (user_id, quiz, question_count))
            mysql.connection.commit()
            cursor.close()
        except Exception as db_error:
            print(f"Database Error: {str(db_error)}")
            return jsonify({"error": f"Database error: {str(db_error)}"}), 500

        return jsonify({"quiz": quiz, "message": "Quiz saved successfully"})
    except Exception as e:
        print(f"Error in quiz generation: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
