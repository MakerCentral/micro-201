#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import time
import fcntl
import array

class HTU21DError(Exception):
    def __init__(self, message):
        self.message = message

class HTU21D(object):
    # The address of the i2c device - fixed address for the HTU21D
    address = 0x40

    # The commands supported by the module
    class CMD(object): pass
    cmd = CMD()
    cmd.read_temp_nohold = "\xF3"
    cmd.read_humd_nohold = "\xF5"
    cmd.read_temp_hold   = "\xE3" # Dont use this on raspberry pi due to scl hold bug
    cmd.read_humd_hold   = "\xE5" # Dont use this on raspberry pi due to scl hold bug
    cmd.write_register   = "\xE6"
    cmd.read_register    = "\xE7"
    cmd.reset = "\xFE"

    def __init__(self, bus = 1):
        # Open handles to the i2c device on the given bus
        self.dev_r = io.open("/dev/i2c-{0}".format(bus), "rb", buffering=0)
        self.dev_w = io.open("/dev/i2c-{0}".format(bus), "wb", buffering=0)

        # Set the device address (used by reads and writes)
        fcntl.ioctl(self.dev_r, 0x0703, HTU21D.address)
        fcntl.ioctl(self.dev_w, 0x0703, HTU21D.address)

        # Reset the device to initial state
        self.dev_w.write(HTU21D.cmd.reset)
        time.sleep(0.1)

    def __del__(self):
        self.dev_r.close()
        self.dev_w.close()

    def crc8(self, value):
        remainder = (value[0] << 16) | (value[1] << 8) | value[2]
        divisor   = 0x988000
        for i in range(0, 16):
            if (remainder & 1 << (23 - i)):
                remainder ^= divisor
            divisor = divisor >> 1
        return remainder == 0

    @property
    def temperature(self):
        self.dev_w.write(HTU21D.cmd.read_temp_nohold)
        time.sleep(0.1)

        data = self.dev_r.read(3)
        data = array.array('B', data)

        if self.crc8(data):
            data = (data[0] << 8 | data[1]) & 0xFFFC
            return -46.85 + (175.72 * (data / 65536.0))
        else:
            raise HTU21DError("Temperature transmission error")

    @property
    def humidity(self):
        self.dev_w.write(HTU21D.cmd.read_humd_nohold)
        time.sleep(0.1)

        data = self.dev_r.read(3)
        data = array.array('B', data)

        if self.crc8(data):
            data = (data[0] << 8 | data[1]) & 0xFFFC
            return -6.0 + (125.0 * (data / 65536.0))
        else:
            raise HTU21DError("Humidity transmission error")
