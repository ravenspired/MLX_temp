from machine import Pin, I2C
import time

# Initialize I2C (try 1 MHz if 400 kHz does not work)
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)  # SCL=GP5, SDA=GP4

MLX90640_I2C_ADDR = 0x33  # MLX90640 default I2C address

def read_register(i2c, register):
    """Reads a 16-bit register from the MLX90640 EEPROM"""
    reg_bytes = register.to_bytes(2, 'big')  # Convert register address to bytes
    i2c.writeto(MLX90640_I2C_ADDR, reg_bytes, False)  # Write register address
    data = i2c.readfrom(MLX90640_I2C_ADDR, 2)  # Read 2 bytes
    return int.from_bytes(data, 'big')  # Convert to integer

# Read the first 16 EEPROM values (basic info + device ID)
print("Reading EEPROM basic information:")
for i in range(0x2400, 0x2410):  
    value = read_register(i2c, i)
    print(f"EEPROM[{hex(i)}] = {hex(value)}")

# Read pixel calibration data (0x2440 - 0x273F)
print("\nReading EEPROM Pixel Calibration Data:")
eeprom_data = []
for i in range(0x2440, 0x2740):  
    eeprom_data.append(read_register(i2c, i))

print("First 16 pixel calibration values:", eeprom_data[:16])
