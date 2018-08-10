# micropython
--------------

A collection of useful micropython code I've written.  This code has been written for, and tested working on the following microcontrollers: 
 - ATSAMD21G18
 - ESP8266
 - ESP32
 
 ##### [LineWipe](https://github.com/raidancampbell/micropython/blob/master/line_wipe.py)
 contains the code to draw a rotating white/black design.  Proof-of-concept for framebuffers, and drawing arbitrary lines
 
 ##### [micropython_ssd1306](https://github.com/raidancampbell/micropython/blob/master/micropython_ssd1306.py)
 A micropython driver for the SSD1306 OLED + controller.  Pull the reset pin high if not already tied low on your board.
 
 ##### [pyframebuf](https://github.com/raidancampbell/micropython/blob/master/pyframebuf.py)
 Minor improvements off Adafruit's existing framebuffer implementation, namely adding text support in python.  I would highly recommend using the standard C module instead of this code.
 
 ##### [wifi_oled](https://github.com/raidancampbell/micropython/blob/master/wifi_oled.py)
 A light abstraction over the above SSD1306 driver.  The hardcoded values for enabling, SCL, SDA, and the I2C address are given for Heltec's HTIT-WB32
 
 ##### [main](https://github.com/raidancampbell/micropython/blob/master/main.py)
 Code to query the brewstat.us API for an arbitrary brewing, and display it via an SSD1306 display. URL and wifi credentials must be entered in `res/secrets.py`.  A sample format is [here](https://github.com/raidancampbell/micropython/blob/master/res/default_secrets.py)
