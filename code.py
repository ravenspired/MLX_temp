# import wifi module
import wifi
import time

# set access point credentials
ap_ssid = "TCam"
ap_password = "securepassword"

# You may also need to enable the wifi radio with wifi.radio.enabled(true)

# configure access point
wifi.radio.start_ap(ssid=ap_ssid, password=ap_password)

"""
start_ap arguments include: ssid, password, channel, authmode, and max_connections
"""

# print access point settings
print("Access point created with SSID: {}, password: {}".format(ap_ssid, ap_password))

# print IP address
print("My IP address is", wifi.radio.ipv4_address)


time.sleep(100)