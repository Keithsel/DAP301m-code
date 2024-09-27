from flask import Flask, render_template, request, jsonify
import requests
import json

app = Flask(__name__)

OPENROUTER_API_KEY = 'Your_API_Key' # Type your api key here
YOUR_APP_NAME = 'My Chatbot'

def get_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-Title": YOUR_APP_NAME,  
    }
    data = {
        "model": "nousresearch/hermes-3-llama-3.1-405b:free", 
        "messages": [
            {
                "role": "user",
                "content": user_message
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        return "Sorry, something went wrong."

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]
    ai_response = get_ai_response(user_message)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    app.run(debug=True)
