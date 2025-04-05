import wifi
import time
import socketpool
from adafruit_httpserver import Server, Request, Response, POST
import ipaddress

# Set access point credentials
ap_ssid = "TCam"
ap_password = "securepassword"



# Enable WiFi radio and start the access point
wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)

time.sleep(1)  # Allow time for the access point to start
ipv4 = ipaddress.IPv4Address("192.168.4.1")
netmask = ipaddress.IPv4Address("255.255.255.0")
gateway = ipaddress.IPv4Address("192.168.4.1")
wifi.radio.set_ipv4_address_ap(ipv4=ipv4, netmask=netmask, gateway=gateway)


# Print access point settings
print("Access point created with SSID: {}, password: {}".format(ap_ssid, ap_password))
print("My IP address is", wifi.radio.ipv4_address_ap)

# Create a socket pool and initialize the HTTP server
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

# HTML content to serve
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to TCam</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #f0f0f0;
        }
        h1 {
            color: deeppink;
        }
        .button {
            background-color: black;
            color: white;
            padding: 15px 30px;
            font-size: 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Welcome to the TCam Web Interface</h1>
    <p>This is a simple HTML page served from the Raspberry Pi Pico W.</p>
    <button class="button" onclick="location.href='/led/on'">Turn LED ON</button><br>
    <button class="button" onclick="location.href='/led/off'">Turn LED OFF</button>
</body>
</html>
"""

# Serve the HTML page on the root route
@server.route("/")
def base(request: Request):
    return Response(request, html_content, content_type="text/html")

# Handle LED control via GET requests
@server.route("/led/on")
def led_on(request: Request):
    # Turn on the onboard LED (for example)
    print("LED turned ON")
    return Response(request, "<h1>LED is ON</h1><a href='/'>Go Back</a>", content_type="text/html")

@server.route("/led/off")
def led_off(request: Request):
    # Turn off the onboard LED (for example)
    print("LED turned OFF")
    return Response(request, "<h1>LED is OFF</h1><a href='/'>Go Back</a>", content_type="text/html")

# Start the HTTP server
print("Starting server...")
try:
    server.start(str(wifi.radio.ipv4_address_ap))
    print(f"Listening on http://{wifi.radio.ipv4_address_ap}:80")
except OSError:
    print("Error starting the server!")
    time.sleep(5)

while True:
    # Poll the server for requests
    server.poll()
