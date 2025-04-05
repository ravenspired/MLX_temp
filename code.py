import wifi
import time
import socketpool
from adafruit_httpserver import Server, Request, Response
import ipaddress
import random
import json

import board
import busio
import adafruit_mlx90640

import microcontroller
microcontroller.cpu.frequency = 250_000_000  # run at 250 MHz instead of 125 MHz overclock





i2c = busio.I2C(board.GP5, board.GP4, frequency=800000)



mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])

mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ
















# Set access point credentials
ap_ssid = "TCam"
ap_password = "securepassword"

# Enable WiFi radio and start the access point
wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)

time.sleep(1)  # Allow time for the access point to start
ipv4 = ipaddress.IPv4Address("10.0.0.1")
netmask = ipaddress.IPv4Address("255.255.255.0")
gateway = ipaddress.IPv4Address("10.0.0.1")
wifi.radio.set_ipv4_address_ap(ipv4=ipv4, netmask=netmask, gateway=gateway)

# Print access point settings
print("Access point created with SSID: {}, password: {}".format(ap_ssid, ap_password))
print("My IP address is", wifi.radio.ipv4_address_ap)

# Create a socket pool and initialize the HTTP server
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

# Generate a 2D list with random numbers between 20 and 30
def generate_heatmap_data():
    return [[random.randint(20, 30) for _ in range(32)] for _ in range(24)]

# Generate initial heatmap data
heatmap_data = generate_heatmap_data()

# HTML content with an image placeholder
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Anton's Thermal Camera</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background-color: #121212;  /* Dark background */
            color: white;  /* Light text */
        }
        h1 {
            color: deeppink;
        }
        .button {
            background-color: #333;
            color: white;
            padding: 15px 30px;
            font-size: 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        #heatmap {
            width: 640px;
            height: 480px;
            border: 4px solid #444;  /* Dark border */
            margin: 20px auto;
            background-color: #333;  /* Dark background for the canvas */
        }
        #gradientBar {
            width: 640px;
            height: 30px;
            margin: 10px auto;
            background: linear-gradient(to right, black, blue, green, red, yellow, white);
            border: 2px solid #444;  /* Dark border */
        }
        .labels {
            display: flex;
            justify-content: space-between;
            width: 640px;
            margin: auto;
            font-weight: bold;
        }
        .labels span {
            color: #ccc;  /* Light text for labels */
        }
    </style>
</head>
<body>
    <h1>Thermal Camera View</h1>
    <p>This is an HTML page served from the Raspberry Pi Pico W. It uses JavaScript in your browser to upscale and render the thermal image.</p>
    <canvas id="heatmap" width="640" height="480"></canvas>
    <div id="gradientBar"></div>
    <div class="labels">
        <span id="lowTemp">Low</span>
        <span id="midTemp">Medium</span>
        <span id="highTemp">High</span>
    </div>

    <script>
function drawHeatmap(data) {
    console.log("Drawing heatmap with data:", data);

    // Ensure data is a valid 2D array
    if (!Array.isArray(data) || data.length !== 24 || !Array.isArray(data[0]) || data[0].length !== 32) {
        console.error("Invalid data structure: Expected a 24x32 array.");
        return;
    }

    const i_width = 320, i_length = 240;
    const canvas = document.getElementById('heatmap');
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(640, 480);

    // Bilinear Interpolation
    function bilinearInterpolation(image, newWidth, newHeight) {
        const originalHeight = image.length;
        const originalWidth = image[0].length;
        const upscaledImage = Array.from({ length: newHeight }, () => Array(newWidth).fill(0));
        const xScale = (originalWidth - 1) / (newWidth - 1);
        const yScale = (originalHeight - 1) / (newHeight - 1);

        for (let i = 0; i < newHeight; i++) {
            for (let j = 0; j < newWidth; j++) {
                const x = j * xScale, y = i * yScale;
                const x1 = Math.floor(x), y1 = Math.floor(y);
                const x2 = Math.min(x1 + 1, originalWidth - 1);
                const y2 = Math.min(y1 + 1, originalHeight - 1);
                const a = x - x1, b = y - y1;

                upscaledImage[i][j] =
                    (1 - a) * (1 - b) * image[y1][x1] +
                    a * (1 - b) * image[y1][x2] +
                    (1 - a) * b * image[y2][x1] +
                    a * b * image[y2][x2];
            }
        }
        return upscaledImage;
    }

    // Upscale data to 320x240
    data = bilinearInterpolation(data, i_width, i_length);
    
    const min_temp = Math.min(...data.flat());
    const max_temp = Math.max(...data.flat());
    document.getElementById("lowTemp").innerText = min_temp.toFixed(1) + "C";
    document.getElementById("midTemp").innerText = ((min_temp + max_temp) / 2).toFixed(1) + "C";
    document.getElementById("highTemp").innerText = max_temp.toFixed(1) + "C";

    for (let y = 0; y < i_length; y++) {
        for (let x = 0; x < i_width; x++) {
            if (!Array.isArray(data[y]) || data[y][x] === undefined) {
                console.error(`Missing value at [${y}][${x}]`);
                continue;
            }

            let value = data[y][x];
            let normalizedValue = (value - min_temp) / (max_temp - min_temp);
            let r = 0, g = 0, b = 0;

            if (normalizedValue < 0.2) { b = Math.floor(255 * (normalizedValue / 0.2)); }
            else if (normalizedValue < 0.4) { b = Math.floor(255 * (1 - (normalizedValue - 0.2) / 0.2)); g = Math.floor(255 * ((normalizedValue - 0.2) / 0.2)); }
            else if (normalizedValue < 0.6) { g = Math.floor(255 * (1 - (normalizedValue - 0.4) / 0.2)); r = Math.floor(255 * ((normalizedValue - 0.4) / 0.2)); }
            else if (normalizedValue < 0.8) { r = 255; g = Math.floor(255 * ((normalizedValue - 0.6) / 0.2)); }
            else { r = 255; g = 255; b = Math.floor(255 * ((normalizedValue - 0.8) / 0.2)); }

            for (let dy = 0; dy < 2; dy++) {
                for (let dx = 0; dx < 2; dx++) {
                    let expandedIndex = ((y * 2 + dy) * 640 + (x * 2 + dx)) * 4;
                    imageData.data[expandedIndex] = r;
                    imageData.data[expandedIndex + 1] = g;
                    imageData.data[expandedIndex + 2] = b;
                    imageData.data[expandedIndex + 3] = 255;
                }
            }
        }
    }

    ctx.putImageData(imageData, 0, 0);
}

function updateHeatmap() {
    fetch('/heatmap')
        .then(response => response.json())
        .then(data => {
            if (!Array.isArray(data) || data.length !== 24 || !Array.isArray(data[0]) || data[0].length !== 32) {
                console.error("Invalid heatmap data received!");
                return;
            }
            drawHeatmap(data);
        })
        .catch(error => console.error("Error fetching heatmap data:", error));
}

setInterval(updateHeatmap, 250);
    </script>
</body>
</html>


"""

# Serve the HTML page on the root route
@server.route("/")
def base(request: Request):
    return Response(request, html_content, content_type="text/html")

# Serve the heatmap data as JSON
@server.route("/heatmap")
def heatmap(request: Request):
    try:
        global heatmap_data
        return Response(request, json.dumps(heatmap_data), content_type="application/json")
    except:
        print("Whoops! data didnt come out good")



# Start the HTTP server
print("Starting server...")
try:
    server.start(str(wifi.radio.ipv4_address_ap))
    print(f"Listening on http://{wifi.radio.ipv4_address_ap}:80")
except OSError:
    print("Error starting the server!")
    time.sleep(5)


frame = [0] * 768

# Main loop to continuously update the heatmap data every 0.5 seconds
while True:
    # Update heatmap data
    
     
    stamp = time.monotonic()
    try:
        mlx.getFrame(frame)
    except ValueError:
        # these happen, no biggie - retry
        continue
    print("Read 2 frames in %0.2f s" % (time.monotonic() - stamp))
    
    # Create a 2D array (24x32) to store the temperatures
    temperature_array = []
    
    for h in range(24):
        row = []
        for w in range(32):
            t = frame[h * 32 + w]
            row.append(t)
        temperature_array.append(row)
        
    #heatmap_data = generate_heatmap_data()
    heatmap_data = temperature_array
        
        
        
    # Poll the server for requests
    server.poll()
    
    # Update the heatmap data at 2Hz (every 0.5 seconds)
    #time.sleep(0.5)
