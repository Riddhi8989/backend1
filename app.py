from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from utils.db import db
from utils.ai_utils import get_ai_guidance
from models.user import User
from models.failcourse import FailCourse
from models.careerpath import CareerPath
from models.question import Question
from models.answer import Answer
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import SqliteDatabase, Model, CharField
from playhouse.shortcuts import model_to_dict
from flask_cors import cross_origin
import openai
import os
import json
import traceback
import re

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"  # ✅ OpenRouter endpoint

app = Flask(__name__)

# ✅ Replace with your actual frontend URL (Vercel or localhost)
CORS(app, origins=["https://frontend1-3b762akez-riddhi8989s-projects.vercel.app"])

# === Database Setup ===
@app.before_request
def before_request():
    if db.is_closed():
        db.connect(reuse_if_open=True)

@app.teardown_request
def teardown_request(exc):
    if not db.is_closed():
        db.close()

# === Create Tables Once ===
with db:
    db.create_tables([User], safe=True)

# === Routes ===
@app.route('/')
def home():
    return '✅ Backend is live', 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    bio = data.get('bio', '')

    if not name or not email or not password:
        return jsonify({'error': 'Missing name, email or password'}), 400

    if User.get_or_none(User.email == email):
        return jsonify({'error': 'Email already exists'}), 400

    hashed_password = generate_password_hash(password)

    user = User.create(
        name=name,
        email=email,
        password=hashed_password,
        bio=bio
    )

    return jsonify({'user': user.to_dict()}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.get_or_none(User.email == email)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"user": user.to_dict()}), 200



@app.route('/me')
def get_profile_by_email():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.get_or_none(User.email == email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())


# ---------- AI Quote ----------
@app.route('/ai-quote', methods=['POST'])
def ai_quote():
    try:
        data = request.get_json()
        topic = data.get("topic", "failure")

        prompt = f"Give me a short motivational quote about {topic}."
        quote = get_ai_guidance(prompt, expect_json=False)

        return jsonify({"quote": quote})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "AI quote failed", "details": str(e)}), 500


from flask import send_from_directory

@app.route('/ai-guidance', methods=['POST'])
def ai_guidance():
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'error': 'Input text is required'}), 400

    result = get_ai_guidance(text)
    return jsonify({'result': result})



@app.route('/update-career', methods=['POST'])
def update_career():
    try:
        data = request.get_json()
        email = data.get("email")
        career = data.get("career")

        if not email or not career:
            return jsonify({"error": "Email and career are required"}), 400

        user = User.get_or_none(User.email == email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.career = career
        user.save()

        return jsonify({"message": "Career updated successfully"}), 200

    except Exception as e:
        print("Error in /update-career:", e)
        return jsonify({"error": "Failed to update career", "details": str(e)}), 500
    



# ---------- Fail Stories ----------
@app.route('/stories', methods=['GET'])
def get_stories():
    try:
        stories = [
            {
                "id": s.id,
                "user": s.user.name,
                "title": s.title,
                "story": s.story,
                "lesson": s.lesson,
                "tags": s.tags
            }
            for s in FailCourse.select().join(User)
        ]
        return jsonify(stories)

    except Exception as e:
        print("Error in /stories:", e)
        return jsonify({"error": "Failed to fetch stories", "details": str(e)}), 500
    



# ---------- Career ----------
@app.route('/career-paths', methods=['GET'])
def get_career_paths():
    try:
        paths = [
            {
                "id": cp.id,
                "title": cp.title,
                "steps": cp.steps,
                "pitfalls": cp.pitfalls,
                "resources": cp.resources
            }
            for cp in CareerPath.select()
        ]
        return jsonify(paths)

    except Exception as e:
        print("Error in /career-paths:", e)
        return jsonify({"error": "Failed to fetch career paths", "details": str(e)}), 500
    
@app.route('/ai-guide', methods=['POST'])
def ai_guide_post():
    data = request.get_json()
    prompt = data.get('prompt') or data.get('text')
    if not OPENROUTER_API_KEY:
          print("❌ API key not loaded.")
          return "Server misconfiguration. Try again later."


    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    result = get_ai_guidance(prompt, expect_json=False)
    return jsonify({'answer': result})


@app.route('/career-details', methods=['POST'])
def career_details():
    try:
        data = request.get_json()
        title = data.get("title")
        if not title:
            return jsonify({"error": "Career title is required"}), 400

        career = CareerPath.get_or_none(CareerPath.title == title)
        if career:
            return jsonify({
                "title": career.title,
                "description": career.description,
                "steps": career.steps,
                "pitfalls": career.pitfalls,
                "resources": career.resources
            }), 200

        prompt = f"Explain how to build a career in {title}. List the steps, pitfalls, and resources."
        ai_result = get_ai_guidance(prompt, expect_json=False)

        return jsonify({
            "title": title,
            "description": "(AI Generated)",
            "ai_result": ai_result
        }), 200

    except Exception as e:
        print("Error in /career-details:", e)
        return jsonify({"error": "Failed to fetch career detail", "details": str(e)}), 500


@app.route('/career-options', methods=['GET'])
def career_options():
    try:
        titles = [c.title for c in CareerPath.select()]
        return jsonify({"options": titles})
    except Exception as e:
        print("Error in /career-options:", e)
        return jsonify({"error": "Failed to load career titles", "details": str(e)}), 500


@app.route('/career-search', methods=['GET'])
def career_search():
    try:
        keyword = request.args.get("q", "")
        if not keyword:
            return jsonify({"error": "Search keyword is required"}), 400

        results = CareerPath.select().where(CareerPath.title.contains(keyword))
        return jsonify([{
            "id": c.id,
            "title": c.title,
            "description": c.description
        } for c in results])
    except Exception as e:
        print("Error in /career-search:", e)
        return jsonify({"error": "Search failed", "details": str(e)}), 500


@app.route('/ai-careers', methods=['POST'])
def ai_careers():
    try:
        data = request.get_json()
        keyword = data.get("keyword") or "technology"

        prompt = f"""
Suggest 6 career paths for someone interested in "{keyword}".
Each with:
- title
- short description
- 3 steps to get started
- 2 pitfalls
- 2 free online resources

Respond ONLY as valid JSON array.
"""

        response = get_ai_guidance(prompt, expect_json=False)

        match = re.search(r"\[\s*{.*}\s*]", response, re.DOTALL)
        if not match:
            raise ValueError("Could not parse valid JSON array from AI response.")

        careers = json.loads(match.group())
        return jsonify({"careers": careers})

    except Exception as e:
        print("AI Error:", e)
        return jsonify({"error": "AI suggestion failed", "details": str(e)}), 500
    
@app.route('/profile', methods=['GET'])
def get_profile():
    email = request.args.get('email')
    user = User.get_or_none(User.email == email)
    if user:
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "role": user.role
        }), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    bio = data.get('bio')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    try:
        user = User.get(User.email == email)
        user.name = name or user.name
        user.bio = bio or user.bio
        user.save()

        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'email': user.email,
                'name': user.name,
                'bio': user.bio,
                'role': user.role
            }
        }), 200
    except User.DoesNotExist:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500



def seed_default_user():
    from models.user import User
    import hashlib

    email = "admin@example.com"
    password = "admin123"
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if not User.get_or_none(User.email == email):
        User.create(
            name="Admin",
            email=email,
            password=hashed_password,
            role="admin",
            bio="System administrator"
        )
        print("✅ Admin user created")
    else:
        print("ℹ️ Admin user already exists")

@app.route('/user-stories', methods=['GET'])
def get_user_stories():
    try:
        email = request.args.get("email")
        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.get_or_none(User.email == email)
        if not user:
            return jsonify({"error": "User not found"}), 404

        stories = FailCourse.select().where(FailCourse.user == user)
        result = [{
            "id": s.id,
            "title": s.title,
            "story": s.story,
            "lesson": s.lesson,
            "tags": s.tags
        } for s in stories]

        return jsonify(result), 200

    except Exception as e:
        print("Error in /user-stories:", e)
        return jsonify({"error": "Failed to fetch stories", "details": str(e)}), 500


@app.route('/ai-guide', methods=['POST'])
def ai_guide():
    data = request.get_json()
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # You can call your AI utility here to generate a response
    answer = get_ai_guidance(prompt)  # Implement this in ai_utils.py
    return jsonify({'answer': answer})


def get_ai_failure_stories():
    prompt = (
        "Generate 10 inspiring Indian stories of individuals who initially failed in education, UPSC, or business, "
        "but later achieved significant success. Each story should be written in 3 to 4 paragraphs, not as bullet points. "
        "Include realistic characters with background, failure, turning point, and final growth. Avoid using real names like 'Narendra Modi' or 'Ambani'. "
        "Return the stories as a JSON array of objects with the keys: 'title', 'story', and optional 'tags'. "
        "Each 'story' field should contain a well-written paragraph-style narrative. "
        "Do not return markdown or code formatting."
    )

    raw_stories = get_ai_guidance(prompt, expect_json=True)

    # Clean and validate
    stories = []
    for item in raw_stories:
        if (
            isinstance(item, dict)
            and item.get("title")
            and item.get("story")
            and isinstance(item["story"], str)
            and len(item["story"].split()) > 50  # ensure it's more than a few lines
        ):
            stories.append(item)

    return stories[:10]  # Return up to 10 medium-length stories

from flask import jsonify
from utils.ai_utils import get_ai_failure_stories  # ensure this import works

@app.route("/ai-stories", methods=["GET"])
def ai_stories():
    try:
        stories = get_ai_failure_stories()
        return jsonify({"stories": stories}), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch stories", "details": str(e)}), 500

@app.route('/save-career', methods=['POST'])
def save_career():
    try:
        data = request.get_json()
        email = data.get('email')
        title = data.get('title')
        description = data.get('description')
        steps = data.get('steps', [])
        pitfalls = data.get('pitfalls', [])
        resources = data.get('resources', [])

        if not email or not title:
            return jsonify({'error': 'Missing required fields'}), 400

        user = User.get_or_none(User.email == email)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.career_title = title
        user.career_description = description
        user.career_steps = json.dumps(steps)
        user.career_pitfalls = json.dumps(pitfalls)
        user.career_resources = json.dumps(resources)
        user.save()

        return jsonify({'message': 'Career updated successfully'}), 200

    except Exception as e:
        print("Error in /save-career:", e)
        return jsonify({'error': 'Failed to save career', 'details': str(e)}), 500


# ---------- Test ----------
@app.route('/test-tables')
def test_tables():
    try:
        FailCourse.select().first()
        CareerPath.select().first()
        Question.select().first()
        Answer.select().first()
        return jsonify({"status": "All tables accessible ✅"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Admin Bootstrap ----------
def ensure_admin_exists():
    try:
        if not User.select().where(User.email == "admin@failed.com").exists():
            User.create_user({
                "name": "Admin",
                "email": "admin@failed.com",
                "password": "admin123",
                "role": "admin",
                "bio": "Platform administrator"
            })
    except Exception as e:
        print("Admin creation failed:", e)

ensure_admin_exists()

# ---------- Run ----------
if __name__ == '__main__':
    db.connect()
    db.create_tables([User], safe=True)
    seed_default_user()
    app.run(debug=True)
