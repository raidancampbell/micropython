# Ported from the MIT-licensed adafruit_max31865 library, originally implemented by Tony DiCola. License below
# The MIT License (MIT)
#
# Copyright (c) 2017 Tony DiCola for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
module for the MAX31865 platinum RTD temperature sensor
"""
import math
import time

from micropython import const

#pylint: disable=bad-whitespace
# Register and other constant values:
_MAX31865_CONFIG_REG          = const(0x00)
_MAX31865_CONFIG_BIAS         = const(0x80)
_MAX31865_CONFIG_MODEAUTO     = const(0x40)
_MAX31865_CONFIG_MODEOFF      = const(0x00)
_MAX31865_CONFIG_1SHOT        = const(0x20)
_MAX31865_CONFIG_3WIRE        = const(0x10)
_MAX31865_CONFIG_24WIRE       = const(0x00)
_MAX31865_CONFIG_FAULTSTAT    = const(0x02)
_MAX31865_CONFIG_FILT50HZ     = const(0x01)
_MAX31865_CONFIG_FILT60HZ     = const(0x00)
_MAX31865_RTDMSB_REG          = const(0x01)
_MAX31865_RTDLSB_REG          = const(0x02)
_MAX31865_HFAULTMSB_REG       = const(0x03)
_MAX31865_HFAULTLSB_REG       = const(0x04)
_MAX31865_LFAULTMSB_REG       = const(0x05)
_MAX31865_LFAULTLSB_REG       = const(0x06)
_MAX31865_FAULTSTAT_REG       = const(0x07)
_MAX31865_FAULT_HIGHTHRESH    = const(0x80)
_MAX31865_FAULT_LOWTHRESH     = const(0x40)
_MAX31865_FAULT_REFINLOW      = const(0x20)
_MAX31865_FAULT_REFINHIGH     = const(0x10)
_MAX31865_FAULT_RTDINLOW      = const(0x08)
_MAX31865_FAULT_OVUV          = const(0x04)
_RTD_A = 3.9083e-3
_RTD_B = -5.775e-7
#pylint: enable=bad-whitespace


class MAX31865:
    """Driver for the MAX31865 thermocouple amplifier."""

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _WRITE_BUFFER = bytearray(3)
    _READ_BUFFER = bytearray(3)

    def __init__(self, spi, rtd_nominal=100, ref_resistor=430.0, wires=2, cs=None):
        self.rtd_nominal = rtd_nominal
        self.ref_resistor = ref_resistor
        self._cs = cs

        self._device = spi
        self._device.init()

        # Set wire config register based on the number of wires specified.
        if wires not in (2, 3, 4):
            raise ValueError('Wires must be a value of 2, 3, or 4!')
        if not cs:
            raise ValueError('active-low Chip Select must be given')
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if wires == 3:
            config |= _MAX31865_CONFIG_3WIRE
        else:
            # 2 or 4 wire
            config &= ~_MAX31865_CONFIG_3WIRE
        self._write_u8(_MAX31865_CONFIG_REG, config)
        # Default to no bias and no auto conversion.
        self.bias = False
        self.auto_convert = False

    # pylint: disable=no-member
    def _read_u8(self, address):
        self._cs.value(0)
        # Read an 8-bit unsigned value from the specified 8-bit address.
        self._WRITE_BUFFER[0] = address & 0x7F
        self._device.write(self._WRITE_BUFFER[:1])
        self._device.readinto(self._READ_BUFFER)
        print('read 8 bits: ' + str(self._READ_BUFFER[:1]))
        self._cs.value(1)
        return self._READ_BUFFER[0]

    def _read_u16(self, address):
        # Read a 16-bit BE unsigned value from the specified 8-bit address.
        self._cs.value(0)
        self._WRITE_BUFFER[0] = address & 0x7F
        self._device.write(self._WRITE_BUFFER[:1])
        self._device.readinto(self._READ_BUFFER)
        print('read 16 bits: ' + str(self._READ_BUFFER[:2]))
        self._cs.value(1)
        return (self._READ_BUFFER[0] << 8) | self._READ_BUFFER[1]

    def _write_u8(self, address, val):
        # Write an 8-bit unsigned value to the specified 8-bit address.
        self._cs.value(0)
        self._WRITE_BUFFER[0] = (address | 0x80) & 0xFF
        self._WRITE_BUFFER[1] = val & 0xFF
        self._device.write(self._WRITE_BUFFER[:2])
        self._cs.value(1)
    # pylint: enable=no-member

    @property
    def bias(self):
        """The state of the sensor's bias (True/False)."""
        return bool(self._read_u8(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_BIAS)

    @bias.setter
    def bias(self, val):
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if val:
            config |= _MAX31865_CONFIG_BIAS  # Enable bias.
        else:
            config &= ~_MAX31865_CONFIG_BIAS  # Disable bias.
        self._write_u8(_MAX31865_CONFIG_REG, config)

    @property
    def auto_convert(self):
        """The state of the sensor's automatic conversion
        mode (True/False).
        """
        return bool(self._read_u8(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_MODEAUTO)

    @auto_convert.setter
    def auto_convert(self, val):
        config = self._read_u8(_MAX31865_CONFIG_REG)
        if val:
            config |= _MAX31865_CONFIG_MODEAUTO   # Enable auto convert.
        else:
            config &= ~_MAX31865_CONFIG_MODEAUTO  # Disable auto convert.
        self._write_u8(_MAX31865_CONFIG_REG, config)

    @property
    def fault(self):
        """The fault state of the sensor.  Use ``clear_faults()`` to clear the
        fault state.  Returns a 6-tuple of boolean values which indicate if any
        faults are present:

        - HIGHTHRESH
        - LOWTHRESH
        - REFINLOW
        - REFINHIGH
        - RTDINLOW
        - OVUV
        """
        faults = self._read_u8(_MAX31865_FAULTSTAT_REG)
        #pylint: disable=bad-whitespace
        highthresh = bool(faults & _MAX31865_FAULT_HIGHTHRESH)
        lowthresh  = bool(faults & _MAX31865_FAULT_LOWTHRESH)
        refinlow   = bool(faults & _MAX31865_FAULT_REFINLOW)
        refinhigh  = bool(faults & _MAX31865_FAULT_REFINHIGH)
        rtdinlow   = bool(faults & _MAX31865_FAULT_RTDINLOW)
        ovuv       = bool(faults & _MAX31865_FAULT_OVUV)
        #pylint: enable=bad-whitespace
        return (highthresh, lowthresh, refinlow, refinhigh, rtdinlow, ovuv)

    def clear_faults(self):
        """Clear any fault state previously detected by the sensor."""
        config = self._read_u8(_MAX31865_CONFIG_REG)
        config &= ~0x2C
        config |= _MAX31865_CONFIG_FAULTSTAT
        self._write_u8(_MAX31865_CONFIG_REG, config)

    def read_rtd(self):
        """Perform a raw reading of the thermocouple and return its 15-bit
        value.  You'll need to manually convert this to temperature using the
        nominal value of the resistance-to-digital conversion and some math.  If you just want
        temperature use the temperature property instead.
        """
        self.clear_faults()
        self.bias = True
        time.sleep(0.01)
        config = self._read_u8(_MAX31865_CONFIG_REG)
        config |= _MAX31865_CONFIG_1SHOT
        self._write_u8(_MAX31865_CONFIG_REG, config)
        time.sleep(0.065)
        rtd = self._read_u16(_MAX31865_RTDMSB_REG)
        # Remove fault bit.
        rtd >>= 1
        return rtd

    @property
    def resistance(self):
        """Read the resistance of the RTD and return its value in Ohms."""
        resistance = self.read_rtd()
        resistance /= 32768
        resistance *= self.ref_resistor
        return resistance

    @property
    def temperature(self):
        """Read the temperature of the sensor and return its value in degrees
        Celsius.
        """
        # This math originates from:
        # http://www.analog.com/media/en/technical-documentation/application-notes/AN709_0.pdf
        # To match the naming from the app note we tell lint to ignore the Z1-4
        # naming.
        # pylint: disable=invalid-name
        raw_reading = self.resistance
        Z1 = -_RTD_A
        Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
        Z3 = (4 * _RTD_B) / self.rtd_nominal
        Z4 = 2 * _RTD_B
        temp = Z2 + (Z3 * raw_reading)
        temp = (math.sqrt(temp) + Z1) / Z4
        if temp >= 0:
            return temp
        rpoly = raw_reading
        temp = -242.02
        temp += 2.2228 * rpoly
        rpoly *= raw_reading  # square
        temp += 2.5859e-3 * rpoly
        rpoly *= raw_reading  # ^3
        temp -= 4.8260e-6 * rpoly
        rpoly *= raw_reading  # ^4
        temp -= 2.8183e-8 * rpoly
        rpoly *= raw_reading  # ^5
        temp += 1.5243e-10 * rpoly
        return temp