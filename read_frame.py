from machine import Pin, I2C
import time

# MLX90640 Default I2C Address
MLX90640_I2C_ADDR = 0x33

# Create I2C instance (use correct SDA/SCL pins for Pico)
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)  # 1 MHz for faster reads

def read_register(i2c, register):
    """Read a 16-bit register from the MLX90640."""
    reg_bytes = register.to_bytes(2, 'big')  # Convert register address to bytes
    i2c.writeto(0x33, reg_bytes)  # Send register address
    data = i2c.readfrom(0x33, 2)  # Read 2 bytes
    return int.from_bytes(data, 'big')  # Convert back to integer

def write_register(i2c, register, value):
    """Write a 16-bit value to a MLX90640 register."""
    reg_bytes = register.to_bytes(2, 'big')
    val_bytes = value.to_bytes(2, 'big')
    i2c.writeto(0x33, reg_bytes + val_bytes)


def read_frame():
    """Read a full frame (832 words) from the sensor RAM."""
    frame_data = []
    for i in range(0x2400, 0x2400 + 832):  # Pixel RAM start at 0x2400
        frame_data.append(read_register(i2c, i))  # Read each register
    return frame_data


write_register(i2c, 0x800D, 0x0001)  # Control register to set continuous mode

eeprom_data = []
for i in range(0x2400, 0x2408):  # Read first 8 EEPROM words
    eeprom_data.append(read_register(i2c, i))

print("EEPROM Data:", eeprom_data)


# Test: Read a single frame
print("Reading MLX90640 frame...")
frame = read_frame()
print(frame)
