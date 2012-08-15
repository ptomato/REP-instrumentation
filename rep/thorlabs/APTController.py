import time
import struct
import numpy as N
import d2xx


def _encode_packet(msgid, param=(0, 0), data=[], dest=0x50, source=0x01):
    return struct.pack('<HBBBB', msgid, param[0], param[1], dest, source)


class APTController(object):

    def __init__(self, serial_number):
        self._dev = d2xx.openEx(serial_number)

        # Recommended setup from Thorlabs APT Programming Guide
        self._dev.setBaudRate(d2xx.BAUD_115200)
        self._dev.setDataCharacteristics(d2xx.BITS_8, d2xx.STOP_BITS_1,
            d2xx.PARITY_NONE)
        time.sleep(50e-3)  # Wait 50 ms before and after purge
        self._dev.purge()  # Clear I/O queue
        time.sleep(50e-3)
        self._dev.resetDevice()
        self._dev.setRts()  # Assert the request-to-send line

    def identify_yourself(self):
        """
        Identify the controller by telling it to flash its front panel LED.
        """
        self._dev.write(_encode_packet(0x0223))

if __name__ == '__main__':
    dev = APTController('83823336')
    dev.identify_yourself()
