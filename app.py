import json
from flask import Flask, request, abort, jsonify    
from main.modules.ChatBot import ChatBot
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

@app.route("/", methods=['GET'])
def index():
    print('hello')
    return "Welcome to Book Bazaar"

@app.route("/api/bbchatbot", methods=['POST'])
def getAnswer():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(data)
            if data is None or 'prompt' not in data:
                raise BadRequest(description='Invalid JSON format or missing "prompt" field')
            prompt = data['prompt']
            chatbot = ChatBot()
            response = chatbot.getAnswer(prompt=prompt)
            print(response)
            return jsonify(response)
        
        except BadRequest as e:
            return abort(400, description=str(e))
        
        except Exception as e:
            print("Error in Chatbot API:", e)
            return abort(500, description="Internal Server Error")

@app.route("/api/recommender", methods=['POST'])
def recommendation():
    if request.method == 'POST':
        try:
            print("RECOMMENDER")
        
        except BadRequest as e:
            return abort(400, description=str(e))
        
        except Exception as e:
            print("Error in Chatbot API:", e)
            return abort(500, description="Internal Server Error")

if __name__ == '__main__':
    app.run(debug=True)