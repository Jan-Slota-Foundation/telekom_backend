from flask import Flask, jsonify, request
from flask_cors import CORS
import csv
import json
from collections import defaultdict
import aichat



app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

stored = []

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to the Flask Server",
        "status": "running"
    })

@app.route('/analyze', methods=["POST"])
def analyze():
    if request.method == "POST":
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({
                "error": "invalid data format",
                "message": "Please provide valid JSON data",
            }), 400
        
        # Clear the stored list before adding new data
        stored.clear()
        stored.append(data)
        csv_string = stored[0]["content"]

        # Define the output file path
        output_file = "output.csv"
        analyze_link = stored[0]["link"]
        print(analyze_link)
        try:
            # Write the content to the file
            # Using 'w' mode automatically overwrites the existing content
            with open(output_file, "w", encoding='utf-8') as file:
                file.write(csv_string)

            return jsonify({
                "message": "data received successfully",
                "saved_data": data,
                "total_items": len(data),
                "file_path": output_file
            })

        except Exception as e:
            return jsonify({
                "error": "file write error",
                "message": str(e)
            }), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "server": "running"
    })

@app.route("/results")
def results():
    grouped_output = defaultdict(list)  # To group entries by nameofvulnerability
    try:
        with open("output.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                vulnerability = row.get("Vulnerability")
                if vulnerability:  # Ensure the key exists
                    filtered = {
                        "Details": row.get("Details"),
                        "Location": row.get("Location"),
                        "Severity": row.get("Severity"),
                        "Cwe":row.get("CWE"),
                        "Cve":row.get("CVE")
                    }
                    grouped_output[vulnerability].append(filtered)
        return jsonify(grouped_output)
    except Exception as e:
        return jsonify({"error": f"Could not read file: {str(e)}"}), 500
    
def read_alerts():
    with open("message.json", "r") as file:
        data = json.load(file)
        data = data["site"][1]["alerts"]
        res = []
        for i in range(len(data)):
            alert_info = {
                "name": data[i].get("name", "N/A"),
                "riskcode": data[i].get("riskcode", "N/A"),
                "confidence": data[i].get("confidence", "N/A"),
                "riskdesc": data[i].get("riskdesc", "N/A"),
                "desc": data[i].get("desc", "N/A"),
                "instances": data[i].get("instances", "N/A"),
                "count": data[i].get("count", "N/A"),
                "solution": data[i].get("solution", "N/A"),
                "reference": data[i].get("reference", "N/A"),
                "cweid": data[i].get("cweid", "N/A"),
                "wascid": data[i].get("wascid", "N/A")
            }
            res.append(alert_info)  # Append to the list
        return res

@app.route("/zapcheck")
def check():
    res = read_alerts()
    return jsonify(res)

@app.route("/askai", methods=["POST"])
def answer():
    # Example files
    result = request.get_json()["content"]
    file1_path = "output.csv"
    file2_path = "message.json"

    chat_client = aichat.ContextAwareChatClient(
        file1_path,
        file2_path,
        model="gpt-4-turbo-preview",
        max_output_tokens=512,
        max_total_tokens=128000
    )
    
    # print("\nInitial token usage:", chat_client.get_token_usage())
    
    # Example conversation loop
    user_input = result
    response = chat_client.chat(user_input)
    if response:
        print(f"\nAssistant: {response}")
        return response, 200
    
    # Save conversation with analysis
    chat_client.save_conversation("conversation_history.json")
    
    return "404 error",404

@app.route("/aiopinion")
def askai():
    return jsonify("requirements.txt") #replace with output of file maybe have it generate here

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)