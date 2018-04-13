import micropython_ssd1306
from machine import I2C
from machine import Pin

Pin(16, Pin.OUT).value(1)

i2c = I2C(sda=Pin(4), scl=Pin(15))
oled = micropython_ssd1306.SSD1306_I2C(128, 32, i2c)
oled.fill(0)
oled.show()


def draw_line(x0, y0, x1, y1, col=1):
    """Bresenham's line algorithm"""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    _x, _y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    if dx > dy:
        err = dx >> 1
        while _x != x1:
            oled.pixel(_x, _y, col)
            err -= dy
            if err < 0:
                _y += sy
                err += dx
            _x += sx
    else:
        err = dy >> 1
        while _y != y1:
            oled.pixel(_x, _y, col)
            err -= dx
            if err < 0:
                _x += sx
                err += dy
            _y += sy
    oled.pixel(_x, _y, col)


def draw_circle(x0, y0, radius, col=1):
    _x = radius - 1
    _y = 0
    dx = 1
    dy = 1
    err = dx - (radius << 1)
    while _x >= _y:
        oled.pixel(x0 + _x, y0 + _y, col)
        oled.pixel(x0 + _y, y0 + _x, col)
        oled.pixel(x0 - _y, y0 + _x, col)
        oled.pixel(x0 - _x, y0 + _y, col)
        oled.pixel(x0 - _x, y0 - _y, col)
        oled.pixel(x0 - _y, y0 - _x, col)
        oled.pixel(x0 + _y, y0 - _x, col)
        oled.pixel(x0 + _x, y0 - _y, col)
        if err <= 0:
            _y += 1
            err += dy
            dy += 2
        if err > 0:
            _x -= 1
            dx += 2
            err += dx - (radius << 1)


def render_rotating_line(x0, y0, bool_x, bool_y, _x_inc=1, _y_inc=1):
    if bool_y:
        if y0 + _y_inc > oled.height or y0 + _y_inc < 0:
            _y_inc *= -1
            bool_y = False
            bool_x = True
        else:
            y0 += _y_inc
    if bool_x:
        if bool_x and x0 + _x_inc > oled.width or x0 + _x_inc < 0:
            _x_inc *= -1
            bool_x = False
            bool_y = True
        else:
            x0 += _x_inc
    return x0, y0, bool_x, bool_y, _x_inc, _y_inc


# 320 border pixels
x_arr = [0, 32, 64, 96, 128]
y_arr = [0, 0, 0, 0, 0]
x_inc_arr = [1, 1, 1, 1, 1]
y_inc_arr = [1, 1, 1, 1, 1]
do_x_arr = [True, True, True, True, True]
do_y_arr = [False, False, False, False, False]
color = True
movements_since_last_toggle = 0

# TODO: tighten this control loop
while True:
    for i, args in enumerate(list(zip(x_arr, y_arr, x_inc_arr, y_inc_arr, do_x_arr, do_y_arr))):

        x, y, do_x, do_y, x_inc, y_inc = render_rotating_line(args[0], args[1], args[4], args[5])

        x_arr[i] = x
        y_arr[i] = y
        x_inc_arr[i] = x_inc
        y_inc_arr[i] = y_inc
        do_x_arr[i] = do_x
        do_y_arr[i] = do_y

        if i == 0 and (oled.width + oled.height) == (movements_since_last_toggle * len(x_arr)):
            color = not color
            movements_since_last_toggle = 0

        draw_line(x, y, oled.width - x, oled.height - y, color * 1)
    movements_since_last_toggle += 1
    oled.show()
