from flask import Flask, request, jsonify, render_template_string
import fitz  # PyMuPDF
import os
from dotenv import load_dotenv
import pytesseract
from PIL import Image
import requests
import math
import re

load_dotenv()

# Your OpenRouter API key and headers
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",  
    "X-Title": "PDF Quiz Generator"
}

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

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

# === Function to estimate maximum possible questions ===
def estimate_max_questions(text):
    # Rough estimate: about 100 characters per question (including options)
    # This is a simplified heuristic - adjust as needed
    word_count = len(text.split())
    
    # Using words as a metric instead of characters
    # Assuming ~20-25 words per question+answer set
    max_questions = math.floor(word_count / 25)
    
    # Cap at reasonable limits for API constraints
    return min(max_questions, 20)

# === Function to call DeepSeek API ===
def generate_quiz(text, question_count=10, temperature=0.9):
    # Ensure we have enough text for the model to work with
    # For smaller question counts, we need less text
    max_text_length = min(3000, 1000 + (question_count * 100))
    text_sample = text[:max_text_length]
    
    prompt = f"""
Create exactly {question_count} multiple-choice questions based on the following content. Each question should have:
- 4 answer choices labeled A–D
- The correct answer labeled like "Answer: B"

Number the questions from 1 to {question_count}.
Only show questions and options, not explanations.

Content:
{text_sample}
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json={
        "model": "deepseek/deepseek-r1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": temperature # Adding some randomness to help with variety
    }
    )

    try:
        result = response.json()
        print("=== DEBUG API RESPONSE ===")
        print(result)

        # Defensive check to prevent crash
        if "choices" in result:
            quiz_text = result['choices'][0]['message']['content']
            
            # Verify question count matches what was requested
            question_count_regex = re.compile(r'\d+\.')
            actual_questions = len(question_count_regex.findall(quiz_text))
            
            # If we don't have enough questions, try again with a more explicit prompt
            if actual_questions < question_count:
                print(f"Got {actual_questions} questions, but expected {question_count}. Retrying...")
                return generate_quiz_backup(text, question_count)
                
            return quiz_text
        else:
            return f"API Error: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# Backup function with more explicit formatting to ensure correct number of questions
def generate_quiz_backup(text, question_count=10):
    text_sample = text[:3000]  # Get a good chunk of text
    
    prompt = f"""
I need EXACTLY {question_count} multiple-choice questions. No more, no less.

Format each question EXACTLY like this:
1. [Question text]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Answer: [Correct letter]

2. [Question text]
...and so on.

Generate these questions based on this content:
{text_sample}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json={
                "model": "deepseek/deepseek-r1",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.5
            }
        )
        
        result = response.json()
        
        if "choices" in result:
            return result['choices'][0]['message']['content']
        else:
            # If API fails, generate simple placeholder questions
            return generate_fallback_questions(text, question_count)
    except Exception as e:
        return generate_fallback_questions(text, question_count)

# Last resort fallback to generate simple questions if API fails
def generate_fallback_questions(text, question_count):
    # Create simple questions from the text
    words = text.split()
    questions = []
    
    for i in range(min(question_count, 5)):  # Limit to 5 questions max for fallback
        if len(words) < 50:
            break
            
        start_idx = i * 50
        if start_idx + 30 > len(words):
            break
            
        sample = " ".join(words[start_idx:start_idx+30])
        
        questions.append(f"{i+1}. What is the main topic of this passage?\nA. Topic 1\nB. Topic 2\nC. Topic 3\nD. Topic 4\nAnswer: A")
    
    # Fill remaining questions with generic ones
    while len(questions) < question_count:
        questions.append(f"{len(questions)+1}. Which statement best summarizes the text?\nA. Summary 1\nB. Summary 2\nC. Summary 3\nD. Summary 4\nAnswer: B")
    
    return "\n\n".join(questions)

# === ROUTES ===
@app.route('/')
def index():
    with open("templates/index.html", encoding="utf-8") as f:
        HTML = f.read()
    return render_template_string(HTML)

@app.route('/analyze_pdf', methods=['POST'])
def analyze_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"error": "No selected file!"}), 400

    try:
        # Save a copy of the file stream
        file_content = file.read()
        file.seek(0)  # Reset stream position
        
        # Create a temporary file-like object
        from io import BytesIO
        temp_file = BytesIO(file_content)
        
        # Extract text and estimate max questions
        text = extract_text(temp_file)
        max_questions = estimate_max_questions(text)
        
        # Determine available options
        options = []
        if max_questions >= 5:
            options.append(5)
        if max_questions >= 10:
            options.append(10)
        if max_questions >= 20:
            options.append(20)
            
        # Store text in session or cache for later use
        # For simplicity, we'll return it to the client, but in production
        # you should store it server-side (session, cache, etc.)
        
        return jsonify({
            "max_questions": max_questions,
            "options": options,
            "text_content": text[:5000]  # Limit for demo purposes
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/generate_quiz', methods=['POST'])
def quiz():
    try:
        data = request.json
        text = data.get('text_content', '')
        question_count = int(data.get('question_count', 10))
        
        quiz = generate_quiz(text, question_count)
        return jsonify({"quiz": quiz})
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# === Run Flask App ===
if __name__ == '__main__':
    app.run(debug=True)
