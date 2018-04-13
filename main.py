from wifi_oled import WifiOled
from res import secrets
from machine import Pin
import time
import network
import sys

try:
    import urequests as requests
except ImportError:
    import requests

sta_if = network.WLAN(network.STA_IF)
STATUS_LED = Pin(25, Pin.OUT)
MANUAL_UPDATE_BUTTON = Pin(0, Pin.IN)


def do_connect():
    """connects to the given SSID in the secrets file, with the given password"""
    # if we're already connected, skip everything
    if sta_if.isconnected():
        return
    STATUS_LED.value(1)
    sta_if.active(True)
    if not sta_if.isconnected():
        print('connecting to network: ', secrets.ssid)
        sta_if.connect(secrets.ssid, secrets.password)

        # while we haven't finished the handshake, OR if we don't have an IP
        while not sta_if.isconnected() or sta_if.ifconfig()[0] == '0.0.0.0':
            # stall for a little bit
            time.sleep(0.05)
            pass
    print('network config: ', sta_if.ifconfig())


def do_disconnect():
    """disconnects from any wifi"""
    # if we're already disconnected, skip everything
    if not sta_if.isconnected():
        return
    STATUS_LED.value(0)
    print('disconnecting from network...')
    sta_if.disconnect()
    sta_if.active(False)
    while sta_if.isconnected():
        time.sleep(0.05)
        pass


def control_loop(iteration, inst, resp):
    try:
        # update the data every 60 iterations, turning on the wifi radio only if needed
        if iteration % 60 == 0:
            do_connect()
            resp = requests.get(secrets.endpoint).json()
            print(str(resp['latest']))
            iteration = 0

        do_disconnect()

        # every-other iteration displays different data
        if iteration % 2 == 0:
            inst.fill(0)
            inst.disp('temp: {:3.1f}'.format(resp['latest']['temperature']), row=0)
            inst.disp('gravity: {:3.4f}'.format(resp['latest']['specificGravity']), row=1)
            inst.disp('abv: {:3.2f}'.format(resp['latest']['abv']*100), row=2)
        else:
            inst.fill(0)
            inst.disp('views: {}'.format(resp['latest']['viewCount']), row=1)
            inst.disp('atten.: {:1.4f}'.format(resp['latest']['attenuation']), row=2)
    except Exception as e:
        sys.print_exception(e)
    return iteration+1, inst, resp


oled = WifiOled()
i = 0
default_response = None  # populated on first execution
last_button_state = MANUAL_UPDATE_BUTTON.value()
do_connect()
while True:
    i, oled, default_response = control_loop(i, oled, default_response)
    for _ in range(0, 50, 1):
        time.sleep(0.1)
        # with 100ms waits, debouncing logic isn't needed
        if MANUAL_UPDATE_BUTTON.value() == 0 and last_button_state == 1:
            do_connect()  # yes, this will throw the usual time off.
            default_response = requests.get(secrets.endpoint).json()
            print(str(default_response['latest']))
            i = 1
        last_button_state = MANUAL_UPDATE_BUTTON.value()
