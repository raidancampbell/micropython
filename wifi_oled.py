import network
import micropython_ssd1306
from machine import I2C
from machine import Pin


class WifiOled:

    def __init__(self):
        Pin(16, Pin.OUT).value(1)
        
        self.i2c = I2C(sda=Pin(4), scl=Pin(15))

        self.oled = micropython_ssd1306.SSD1306_I2C(128, 32, self.i2c, addr=60)
        self.oled.fill(0)
        self.oled.show()
        self.fill = self.oled.fill

    def run(self):
        sta_if = network.WLAN(network.STA_IF)
        sta_if.scan()
        # sta_if.ifconfig() returns a 4-tuple:
        # IP address, subnet mask, gateway and DNS server
        self.oled.text('ip:' + sta_if.ifconfig()[0], 0, 0)
        self.oled.show()

    def disp(self, _str, row=0):
        self.oled.text(_str, 0, row*10)
        self.oled.show()
