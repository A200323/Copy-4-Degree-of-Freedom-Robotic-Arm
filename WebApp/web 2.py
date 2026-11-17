"""Flask UI plus the ESP32-CAM action route from the team's web.py template.

/api/command remains the dashboard simulator. /send_command forwards a single
hardware action. Speed and arm mappings require the team's ESP32 firmware.
"""
import requests

from flask import Flask, jsonify, render_template, request
from robot_interface import RobotInterface

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4096
robot = RobotInterface()

# Change this to the ESP32-CAM address shown in your Arduino Serial Monitor.
# For access-point mode your template uses: ESP32_IP = "192.168.4.1"
ESP32_IP = "192.168.4.1"


@app.route('/')
def index():
    stream_url = f"http://{ESP32_IP}:81/stream"
    return render_template('index2.html', stream_url=stream_url)


@app.route('/gamepad-action', methods=['POST'])
def gamepad_action():
    # Like the reference template, this route logs input only.
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('action'), str) or not data['action'].strip():
        return jsonify(status='error', message='Provide a JSON object with an action.'), 400
    print(f"Received from gamepad: {data}")
    print(f"Action: {data['action']}")
    return jsonify(status='success', forwarded=False)


@app.route('/send_command', methods=['POST'])
def send_command():
    # This route DOES send the requested action to the ESP32-CAM.
    # The firmware must support /control?var=move&val=<action>.
    if not request.is_json:
        return jsonify(status='error', message='Send application/json.'), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(status='error', message='Provide a JSON object.'), 400
    action = data.get('action')
    if not isinstance(action, str) or not action.strip():
        return jsonify(status='error', message='No action provided.'), 400
    action = action.strip()
    if len(action) > 64:
        return jsonify(status='error', message='Action is too long.'), 400
    try:
        response = requests.get(
            f"http://{ESP32_IP}/control",
            params={'var': 'move', 'val': action},
            timeout=2.0,
            allow_redirects=False,
        )
    except requests.exceptions.Timeout:
        return jsonify(status='error', message='ESP32-CAM did not respond within 2 seconds.'), 504
    except requests.exceptions.RequestException:
        return jsonify(status='error', message='Cannot reach ESP32-CAM. Check its IP and Wi-Fi connection.'), 502
    if response.status_code != 200:
        return jsonify(status='error', message='ESP32-CAM rejected the command.',
                       device_status=response.status_code), 502
    return jsonify(status='success', action=action)


@app.get('/api/status')
def status():
    return jsonify(robot.status())


def validate_command(data):
    """ Check browser input before passing it to the robot interface."""
    if not isinstance(data, dict):
        raise ValueError('The command must be a JSON object.')
    result = {}
    for part in ('wheel', 'arm'):
        value = data.get(part)
        if not isinstance(value, dict):
            raise ValueError(f'{part} must be an object.')
        speed = value.get('speed')
        direction = value.get('direction')
        if type(speed) is not int or not 0 <= speed <= 100:
            raise ValueError(f'{part} speed must be an integer from 0 to 100.')
        if direction not in ('left', 'right', 'stop'):
            raise ValueError(f'{part} direction must be left, right, or stop.')
        result[part] = {'speed': speed, 'direction': direction}
        if speed == 0:
            result[part]['direction'] = 'stop'
    claw = data['arm'].get('claw')
    if claw not in ('open', 'closed'):
        raise ValueError('arm claw must be open or closed.')
    result['arm']['claw'] = claw
    return result


@app.post('/api/command')
def command():
    if not request.is_json:
        return jsonify(error='Send application/json.'), 415
    try:
        checked = validate_command(request.get_json(silent=True))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    robot.apply_command(checked)
    return jsonify(ok=True, mode='simulation', hardware_connected=False, command=checked)


if __name__ == '__main__':
    # Open http://127.0.0.1:5000 in your browser after starting this file.
    app.run(host='0.0.0.0', port=5000, debug=False)
