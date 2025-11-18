# Raspberry Pi LED Control Server

This directory contains the code that runs on the Raspberry Pi to control the LEDs for Gollum detection notifications.

## Hardware Setup

### Components
- Raspberry Pi (any model with GPIO pins)
- Red LED + 220Ω resistor → GPIO18 (Pin 12)
- Green LED + 220Ω resistor → GPIO13 (Pin 33)
- Optional: Button → GPIO17 (Pin 11) for manual LED control

### Wiring Diagram
```
Red LED:
  GPIO18 (Pin 12) → 220Ω Resistor → LED Anode (+) → LED Cathode (-) → Ground

Green LED:
  GPIO13 (Pin 33) → 220Ω Resistor → LED Anode (+) → LED Cathode (-) → Ground

Optional Button:
  GPIO17 (Pin 11) → Button → Ground
```

## Software Setup

### 1. Install Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip -y

# Install required packages
pip3 install -r requirements.txt
```

### 2. Test the API

```bash
# Run the API manually to test
python3 api.py
```

The API will start on `http://0.0.0.0:5000`

Test with:
```bash
# Turn red LED on
curl -X POST http://10.0.0.106:5000/led/red/on

# Turn red LED off
curl -X POST http://10.0.0.106:5000/led/red/off

# Turn green LED on
curl -X POST http://10.0.0.106:5000/led/green/on

# Turn green LED off
curl -X POST http://10.0.0.106:5000/led/green/off
```

### 3. Set Up as a Service (Auto-start on Boot)

```bash
# Copy service file to systemd directory
sudo cp led-api.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the service (start on boot)
sudo systemctl enable led-api.service

# Start the service
sudo systemctl start led-api.service

# Check status
sudo systemctl status led-api.service
```

### 4. Verify on Your Network

From your main computer:
```bash
curl http://10.0.0.106:5000/
```

You should see the API documentation.

## API Endpoints

### `GET /`
Returns API documentation and available endpoints.

### `POST /led/<color>/on`
Turn on the specified LED.
- **color**: `red` or `green`
- **Response**: `{"status": "success", "color": "red", "led": "on"}`

### `POST /led/<color>/off`
Turn off the specified LED.
- **color**: `red` or `green`
- **Response**: `{"status": "success", "color": "red", "led": "off"}`

### `POST /led/<color>/toggle`
Toggle the LED state.
- **color**: `red` or `green`
- **Response**: `{"status": "success", "color": "red", "led": "on"}`

### `GET /led/<color>/status`
Get the current LED state.
- **color**: `red` or `green`
- **Response**: `{"color": "red", "led": "on"}`

## Files

- **`api.py`**: Flask API server for LED control
- **`program.py`**: Simple button-controlled LED program (optional)
- **`requirements.txt`**: Python dependencies
- **`led-api.service`**: Systemd service file for auto-start
- **`README.md`**: This file

## Troubleshooting

### LEDs not working
1. Check wiring connections
2. Verify GPIO pin numbers in code match your wiring
3. Test with `program.py` to verify hardware setup

### API not accessible from network
1. Check Raspberry Pi IP address: `hostname -I`
2. Verify firewall settings: `sudo ufw status`
3. Check if service is running: `sudo systemctl status led-api.service`

### Service won't start
1. Check logs: `sudo journalctl -u led-api.service -f`
2. Verify permissions: `ls -la /home/gollum/Projects/Blinker/api.py`
3. Test manually: `python3 api.py`

### Permission errors
If you get GPIO permission errors, add user to gpio group:
```bash
sudo usermod -a -G gpio gollum
```
Then logout and login again.

## Integration with Main App

The backend Flask server (`backend/server.py`) connects to this API at:
- **URL**: `http://10.0.0.106:5000`
- **Red LED**: Gollum detected
- **Green LED**: No Gollum detected

## Network Configuration

Current setup:
- **Raspberry Pi IP**: `10.0.0.106`
- **Username**: `gollum`
- **API Port**: `5000`

To change the IP or if your Pi has a different IP:
1. Find your Pi's IP: `hostname -I` on the Pi
2. Update `LED_BASE_URL` in `backend/server.py`
