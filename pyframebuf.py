# Pure python implementation of MicroPython framebuf module.
# This is intended for boards with limited flash memory and the inability to
# use the native C version of the framebuf module.  This python module can be
# added to the board's file system to provide a functionally identical framebuf
# interface but at the expense of speed (this python version will be _much_
# slower than the C version).
# This is a direct port of the framebuf module C code to python:
#   https://github.com/micropython/micropython/blob/master/extmod/modframebuf.c
# Original file created by Damien P. George.
# Python port below created by Tony DiCola, and modified by Aidan Campbell

from res.font_petme128_8x8 import font_petme128_8x8

# Framebuf format constants:
MVLSB = 0  # Single bit displays (like SSD1306 OLED)
RGB565 = 1  # 16-bit color displays
GS4_HMSB = 2  # Unimplemented!


class MVLSBFormat:

    def setpixel(self, fb, x, y, color):
        index = (y >> 3) * fb.stride + x
        offset = y & 0x07
        fb.buf[index] = (fb.buf[index] & ~(0x01 << offset)) | ((color != 0) << offset)

    def getpixel(self, fb, x, y):
        index = (y >> 3) * fb.stride + x
        offset = y & 0x07
        return (fb.buf[index] >> offset) & 0x01

    def fill_rect(self, fb, x, y, width, height, color):
        while height > 0:
            index = (y >> 3) * fb.stride + x
            offset = y & 0x07
            for ww in range(width):
                fb.buf[index + ww] = (fb.buf[index + ww] & ~(0x01 << offset)) | ((color != 0) << offset)
            y += 1
            height -= 1


class RGB565Format:

    def setpixel(self, fb, x, y, color):
        index = (x + y * fb.stride) * 2
        fb.buf[index] = (color >> 8) & 0xFF
        fb.buf[index + 1] = color & 0xFF

    def getpixel(self, fb, x, y):
        index = (x + y * fb.stride) * 2
        return (fb.buf[index] << 8) | fb.buf[index + 1]

    def fill_rect(self, fb, x, y, width, height, color):
        while height > 0:
            for ww in range(width):
                index = (ww + x + y * fb.stride) * 2
                fb.buf[index] = (color >> 8) & 0xFF
                fb.buf[index + 1] = color & 0xFF
            y += 1
            height -= 1


class FrameBuffer:

    def __init__(self, buf, width, height, buf_format=MVLSB, stride=None):
        self.buf = buf
        self.width = width
        self.height = height
        self.stride = stride
        if self.stride is None:
            self.stride = width
        if buf_format == MVLSB:
            self.format = MVLSBFormat()
        elif buf_format == RGB565:
            self.format = RGB565Format()
        else:
            raise ValueError('invalid format')
        self.font_data = font_petme128_8x8

    def fill(self, color):
        self.format.fill_rect(self, 0, 0, self.width, self.height, color)

    def fill_rect(self, x, y, width, height, color):
        if width < 1 or height < 1 or (x + width) <= 0 or (y + height) <= 0 or y >= self.height or x >= self.width:
            return
        xend = min(self.width, x + width)
        yend = min(self.height, y + height)
        x = max(x, 0)
        y = max(y, 0)
        self.format.fill_rect(self, x, y, xend - x, yend - y, color)

    def pixel(self, x, y, color=None):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        if color is None:
            return self.format.getpixel(self, x, y)
        else:
            self.format.setpixel(self, x, y, color)

    def hline(self, x, y, width, color):
        self.fill_rect(x, y, width, 1, color)

    def vline(self, x, y, height, color):
        self.fill_rect(x, y, 1, height, color)

    def rect(self, x, y, width, height, color):
        self.fill_rect(x, y, width, 1, color)
        self.fill_rect(x, y + height, width, 1, color)
        self.fill_rect(x, y, 1, height, color)
        self.fill_rect(x + width, y, 1, height, color)

    def line(self):
        raise NotImplementedError()

    def blit(self):
        raise NotImplementedError()

    def scroll(self):
        raise NotImplementedError()

    def text(self, text, x, y0, color=1):
        for char in text:
            ascii_val = ord(char)
            if ascii_val < 32 or ascii_val > 127:
                ascii_val = 127
            start_index = (ascii_val - 32) * 8
            char_data = self.font_data[start_index: start_index + 8]

            for byte in char_data:
                if 0 <= x < self.width:  # clip x
                    vline_data = byte  # each byte is a column of 8 pixels, LSB at top
                    y = y0
                    while vline_data:
                        if vline_data & 1:
                            if 0 <= y < self.height:  # clip y
                                self.pixel(x, y, color)
                        vline_data >>= 1
                        y += 1
                x += 1


class FrameBuffer1(FrameBuffer):
    def blit(self):
        super().blit()

    def scroll(self):
        super().scroll()

    def line(self):
        super().line()
