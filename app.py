import json
from main.modules.Recommender import ContentBasedFilteringModel
from main.modules.Recommender import CollaborativeFilteringModel
from flask import Flask, request, abort, jsonify    
from werkzeug.exceptions import BadRequest
from main.modules.ChatBot import ChatBot
from main.modules.Recommender import getRecommendation


with open(r'.\config\config.json', 'r') as f:
    config = json.load(f)

app = Flask(__name__)

@app.route("/", methods=['GET'])
def index():
    print('hello')
    response = {
        "Message": "Welcome to Book-Bazaar backend APIs",
        "ApiStatus": {
            "isActive":True,
            "baseURL": "http://127.168.192.5:3001"
        },
        "Status": 200
    }
    return jsonify(response)

@app.route("/api/bbchatbot", methods=['POST'])
def getAnswer():
    if request.method == 'POST':
        try:
            print("CHATBOT")
            data = request.get_json()
            print(data)
            if data is None or 'prompt' not in data:
                raise BadRequest(description='Invalid JSON format or missing [prompt] field')
            prompt = data['prompt']
            response = ChatBot.getAnswer(prompt)
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
            data = request.get_json()
            print(data)
            if data is None or 'title' not in data:
                raise BadRequest(description='Invalid JSON format or missing [recommend] field')
            title = data['title']
            response = getRecommendation(title)
            return jsonify(response)
        
        except BadRequest as e:
            return abort(400, description=str(e))
        
        except Exception as e:
            print("Error in Recommender API:", e)
            return abort(500, description="Internal Server Error")

if __name__ == '__main__':
    app.run(host=config[0]['host'], port=config[0]['port'], debug=True)