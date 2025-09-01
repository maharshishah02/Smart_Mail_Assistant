import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS # Used to handle Cross-Origin Resource Sharing

app = Flask(__name__)
CORS(app) 

# --- IMPORTANT FOR LOCAL EXECUTION ---
# You MUST replace "" with your actual Gemini API Key here for the backend to work.
API_KEY = "AIzaSyCmB24WXjbiqREBuOjCq5MFgtsaTF9zEIg"

def call_gemini_api(prompt: str) -> dict:
    """
    Calls the Gemini API (gemini-2.0-flash) to generate content based on the given prompt.
    """
    if not API_KEY or "YOUR_SUPER_SECRET" in API_KEY:
        print("Error: Gemini API Key is not set in email_api.py. Please update it.")
        return {"error": "Server error: Gemini API Key not configured."}

    chat_history = [{"role": "user", "parts": [{"text": prompt}]}]
    payload = {"contents": chat_history}
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    try:
        response = requests.post(
            api_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        if result.get('candidates') and result['candidates'][0].get('content', {}).get('parts'):
            text = result['candidates'][0]['content']['parts'][0].get('text')
            return {"generated_text": text if text else "Generated content is empty."}
        else:
            print(f"Error: Unexpected Gemini API response structure: {result}")
            return {"error": f"AI generation failed: Unexpected response structure."}
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error calling Gemini API: {http_err} - {http_err.response.text}")
        return {"error": f"AI service error: {http_err.response.status_code}. Check API Key and limits."}
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred during Gemini API request: {req_err}")
        return {"error": f"An unknown error occurred with AI service: {req_err}"}
    except Exception as e:
        print(f"An unexpected error occurred in call_gemini_api: {e}")
        return {"error": f"An unexpected server error occurred: {e}"}

def build_prompt(email_text, tone, style, keywords, document_text, action):
    """Builds a detailed prompt for the Gemini API."""
    tone_and_style = f"{tone} and {style}" if style != 'Default' else tone
    
    keywords_instruction = f"Naturally incorporate the following keywords: {keywords}." if keywords else ""
    
    document_instruction = ""
    if document_text:
        document_instruction = f"""
Use the following document to inform the email's content. Refer to the skills, experiences, or other details from this document to make the email more personalized and relevant.
---DOCUMENT CONTEXT---
{document_text}
---END DOCUMENT---
"""

    if action == 'complete':
        return f"""As an AI assistant, complete the email below. Maintain a {tone_and_style} tone. This email is for a job application or recruiter message. {keywords_instruction}
{document_instruction}
Email start: '{email_text}'
Complete the email naturally. The output should only be the completed email text."""
    
    elif action == 'refine':
        return f"""As an AI assistant, refine the email below. Make it {tone_and_style}. Correct grammar and improve clarity, professionalism, and confidence for a job application or recruiter message. {keywords_instruction}
{document_instruction}
Original Email: '{email_text}'
Refined Email:"""
    
    return "" # Should not happen

@app.route('/complete_email', methods=['POST'])
def complete_email_endpoint():
    try:
        data = request.get_json()
        if not data.get('email_text') or not data.get('tone'):
            return jsonify({"error": "Missing required fields."}), 400
        
        prompt = build_prompt(
            data.get('email_text'), data.get('tone'), data.get('style', 'Default'),
            data.get('keywords', ''), data.get('document_text', ''), 'complete'
        )
        response_from_gemini = call_gemini_api(prompt)
        return jsonify(response_from_gemini)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

@app.route('/refine_email', methods=['POST'])
def refine_email_endpoint():
    try:
        data = request.get_json()
        if not data.get('email_text') or not data.get('tone'):
            return jsonify({"error": "Missing required fields."}), 400

        prompt = build_prompt(
            data.get('email_text'), data.get('tone'), data.get('style', 'Default'),
            data.get('keywords', ''), data.get('document_text', ''), 'refine'
        )
        response_from_gemini = call_gemini_api(prompt)
        return jsonify(response_from_gemini)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

@app.route('/summarize_email', methods=['POST'])
def summarize_email_endpoint():
    try:
        data = request.get_json()
        email_text = data.get('email_text')
        if not email_text:
            return jsonify({"error": "Missing 'email_text' in request."}), 400

        prompt = f"""Summarize the following text concisely. Highlight the key information, main points, and any questions being asked. Present the summary in clear bullet points.
Text to summarize: '{email_text}'
Summary:"""
        response_from_gemini = call_gemini_api(prompt)
        return jsonify(response_from_gemini)
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)