from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# ESP32-Cam Access Point IP address
ESP32_IP = "192.168.4.1"

@app.route('/')
def index():
    # Pass the ESP32 streaming URL to the HTML template
    # Note: Stream runs on port 81 by default in this architecture
    stream_url = f"http://{ESP32_IP}:81/stream"
    return render_template('index.html', stream_url=stream_url)

@app.route('/gamepad-action', methods=['POST'])
def gamepad_action():
    data = request.json
    print(f"Received from gamepad: {data}")
    print(f"Action: {data['action']}")
    return jsonify({"status": "success"})

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.get_json()
    action = data.get('action') # e.g., "forward", "left", "stop"
    
    if not action:
        return jsonify({"status": "error", "message": "No action provided"}), 400

    try:
        # Forward command to the ESP32-Cam control endpoint using the modified app_httpd.cpp logic
        control_url = f"http://{ESP32_IP}/control?var=move&val={action}"
        response = requests.get(control_url, timeout=2.0)
        
        if response.status_code == 200:
            return jsonify({"status": "success", "action": action})
        else:
            return jsonify({"status": "error", "message": "ESP32-Cam rejected command"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run Flask app locally on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)