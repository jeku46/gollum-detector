from flask import Flask, jsonify
from gpiozero import LED

app = Flask(__name__)

# Initialize LEDs for different colors
leds = {
    'red': LED(18),
    'green': LED(13)
}

@app.route('/led/<color>/on', methods=['POST'])
def led_color_on(color):
    color = color.lower()
    if color not in leds:
        return jsonify({'status': 'error', 'message': f'Invalid color. Available colors: {list(leds.keys())}'}), 400

    leds[color].on()
    return jsonify({'status': 'success', 'color': color, 'led': 'on'}), 200

@app.route('/led/<color>/off', methods=['POST'])
def led_color_off(color):
    color = color.lower()
    if color not in leds:
        return jsonify({'status': 'error', 'message': f'Invalid color. Available colors: {list(leds.keys())}'}), 400

    leds[color].off()
    return jsonify({'status': 'success', 'color': color, 'led': 'off'}), 200

@app.route('/led/<color>/toggle', methods=['POST'])
def led_color_toggle(color):
    color = color.lower()
    if color not in leds:
        return jsonify({'status': 'error', 'message': f'Invalid color. Available colors: {list(leds.keys())}'}), 400

    leds[color].toggle()
    state = 'on' if leds[color].is_lit else 'off'
    return jsonify({'status': 'success', 'color': color, 'led': state}), 200

@app.route('/led/<color>/status', methods=['GET'])
def led_color_status(color):
    color = color.lower()
    if color not in leds:
        return jsonify({'status': 'error', 'message': f'Invalid color. Available colors: {list(leds.keys())}'}), 400

    state = 'on' if leds[color].is_lit else 'off'
    return jsonify({'color': color, 'led': state}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'LED Control API',
        'endpoints': {
            'POST /led/<color>/on': 'Turn LED on (red=GPIO18, green=GPIO13)',
            'POST /led/<color>/off': 'Turn LED off',
            'POST /led/<color>/toggle': 'Toggle LED state',
            'GET /led/<color>/status': 'Get LED status'
        },
        'available_colors': list(leds.keys())
    }), 200

if __name__ == '__main__':
    print('Starting LED Control API on port 5000...')
    print(f'Available colors: {list(leds.keys())}')
    app.run(host='0.0.0.0', port=5000, debug=False)
