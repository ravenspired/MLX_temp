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
        #heatmap {
            width: 640px; /* Adjust for 32x24 grid with larger pixel size */
            height: 480px; /* Adjust for 32x24 grid with larger pixel size */
            border: 4px solid #ccc;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <h1>Thermal Camera View</h1>
    <p>This is a HTML page served from the Raspberry Pi Pico W. It uses javascript in your browser to upscale and render the thermal image.</p>
    <canvas id="heatmap" width="640" height="480"></canvas>

    <script>
function drawHeatmap(data) {
    console.log("Drawing heatmap with data:", data);  // Log received data for inspection
    
    // Check if data is a 2D array with 24 rows and 32 columns
    if (!Array.isArray(data) || data.length !== 24) {
        console.error("Invalid data structure: Expected 24 rows.");
        return;
    }

    for (let i = 0; i < 24; i++) {
        if (!Array.isArray(data[i]) || data[i].length !== 32) {
            console.error(`Invalid data structure: Row ${i} does not have 32 columns.`);
            return;
        }
    }

    const canvas = document.getElementById('heatmap');
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(640, 480);  // Create a blank image data object for 32x24 grid

    // Iterate through the heatmap data and map each value to a color
    const pixelWidth = 20;  // Pixel width in the canvas (larger size for 32x24 grid)
    const pixelHeight = 20;  // Pixel height in the canvas (larger size for 32x24 grid)
    for (let y = 0; y < 24; y++) {
        for (let x = 0; x < 32; x++) {
            let value = data[y] && data[y][x];  // Safeguard against undefined
            if (value === undefined) {
                console.error(`Missing value at [${y}][${x}]`);
                continue;  // Skip if data is missing
            }
            let colorValue = Math.floor((value - 20) * 255 / 10);  // Map value to color
            let index = ((y * pixelHeight) * 640 + (x * pixelWidth)) * 4;

            // Set RGB values (from blue to red)
            imageData.data[index] = colorValue;     // Red
            imageData.data[index + 1] = 0;          // Green
            imageData.data[index + 2] = 255 - colorValue;  // Blue
            imageData.data[index + 3] = 255;        // Alpha (full opacity)

            // Now expand the current pixel to the 10x10 block in the canvas
            for (let dy = 0; dy < pixelHeight; dy++) {
                for (let dx = 0; dx < pixelWidth; dx++) {
                    let expandedIndex = ((y * pixelHeight + dy) * 640 + (x * pixelWidth + dx)) * 4;
                    imageData.data[expandedIndex] = colorValue;     // Red
                    imageData.data[expandedIndex + 1] = 0;          // Green
                    imageData.data[expandedIndex + 2] = 255 - colorValue;  // Blue
                    imageData.data[expandedIndex + 3] = 255;        // Alpha (full opacity)
                }
            }
        }
    }

    // Put the image data onto the canvas
    ctx.putImageData(imageData, 0, 0);
}

function updateHeatmap() {
    fetch('/heatmap')
        .then(response => response.json())
        .then(data => {
            console.log("Received data:", data);  // Debugging step to log received data
            drawHeatmap(data);
        });

}

// Update the heatmap every 0.5 seconds
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
