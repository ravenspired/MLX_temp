from machine import Pin, I2C

i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

devices = i2c.scan()
print("I2C devices found:", devices)

if 0x33 in devices:
    print("MLX90640 detected!")
else:
    print("MLX90640 NOT found. Check wiring.")



def read_register(i2c, register):
    """Read a 16-bit register from the MLX90640."""
    reg_bytes = register.to_bytes(2, 'big')
    i2c.writeto(0x33, reg_bytes)
    data = i2c.readfrom(0x33, 2)
    return int.from_bytes(data, 'big')

device_id = read_register(i2c, 0x2407)  # Device ID register
print("Device ID:", hex(device_id))

def write_register(i2c, register, value):
    """Write a 16-bit value to a MLX90640 register."""
    reg_bytes = register.to_bytes(2, 'big')
    val_bytes = value.to_bytes(2, 'big')
    i2c.writeto(0x33, reg_bytes + val_bytes)

# Set MLX90640 to continuous mode
write_register(i2c, 0x800D, 0x0001)  # Control register