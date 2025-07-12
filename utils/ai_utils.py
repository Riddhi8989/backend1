import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct"


def get_ai_guidance(prompt_text, expect_json=False):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an AI mentor helping students who failed in traditional education. "
                        "If asked for careers, return JSON array of objects with title, description, steps, pitfalls, and resources. "
                        "If asked for quotes or guidance, return plain text without quotes or markdown. "
                        "If asked for study goals, ONLY return a raw JSON array of strings like: "
                        "[\"Goal 1\", \"Goal 2\", \"Goal 3\", \"Goal 4\", \"Goal 5\"]"
                    )
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"].strip()

        if expect_json:
            content = content.strip("` \n")
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [v for v in parsed.values() if isinstance(v, str)]
                else:
                    print("⚠️ Unexpected AI response structure:", parsed)
                    return []
            except json.JSONDecodeError as e:
                print("⚠️ JSON decode failed:", e)
                print("🚫 Raw content:\n", content)
                return []
        else:
            return content

    except requests.exceptions.HTTPError as http_err:
        print("❌ OpenRouter HTTP Error:", http_err)
        print("📦 Payload Sent:\n", json.dumps(data, indent=2))
        return [] if expect_json else "AI service failed. Try again later."

    except Exception as e:
        print("❌ General AI Error:", e)
        return [] if expect_json else "Something went wrong. Please try again."


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

    stories = []
    for item in raw_stories:
        if (
            isinstance(item, dict)
            and item.get("title")
            and item.get("story")
            and isinstance(item["story"], str)
            and len(item["story"].split()) > 50
        ):
            stories.append(item)

    return stories[:10]
