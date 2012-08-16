import time
import struct
import numpy as N
import d2xx


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

    def _send_packet(self, msgid, param=(0, 0), data=None, dest=0x50, source=1):
        packet = struct.pack('<HBBBB', msgid, param[0], param[1], dest, source)
        self._dev.write(packet)

    def _read_packet(self, expected_msgid):
        header = self._dev.read(6)
        msgid, length, dest, source = struct.unpack('<HHBB', header)
        if msgid != expected_msgid:
            raise IOError('Expected message ID {}, but received {}'.format(
                msgid, expected_msgid))
        if dest & 0x80:
            # Data following the packet - make sure there are enough bytes
            # available for reading to cover the expected data length
            rx_queue_length, _, _ = self._dev.getStatus()
            if length > rx_queue_length:
                raise IOError('Expected {} bytes, but only {} available'.format(
                    length, rx_queue_length))
            return self._dev.read(length)

    def _get_hardware_info(self):
        dev._send_packet(0x0005)
        data = dev._read_packet(0x0006)
        (serial_number, model_number, hw_type, minor_ver, interim_ver,
            major_ver, _, notes, _, hw_ver, hw_mod_state, n_channels) = \
            struct.unpack('<L8sHBBBB48s12sHHH', data)
        self._serial_number = hex(serial_number)[2:-1]  # strip 0x...L
        self._model_number = model_number.strip('\0')
        self._software_version = '{}.{}.{}'.format(major_ver, interim_ver,
            minor_ver)
        self._hardware_version = '{}.{}'.format(hw_ver, hw_mod_state)
        self._notes = notes.strip()
        self._n_channels = n_channels
        self._hardware_type = hw_type

    def _hardware_property(attr_name, docstring):
        def getter(self):
            try:
                return getattr(self, attr_name)
            except AttributeError:
                self._get_hardware_info()
                return getattr(self, attr_name)
        return property(fget=getter, doc=docstring)

    model_number = _hardware_property('_model_number',
        """Controller's model number.""")
    serial_number = _hardware_property('_serial_number',
        """
        According to the documentation, this should be a unique serial number.
        But it isn't. Don't rely on it.
        """)
    software_version = _hardware_property('_software_version',
        """Controller's software version.""")
    hardware_version = _hardware_property('_hardware_version',
        """
        Controller's hardware version (in the form
        <version>.<modification state>).
        """)
    device_info = _hardware_property('_notes',
        """Arbitrary information that the controller provides.""")
    n_channels = _hardware_property('_n_channels',
        """Number of channels available on this controller.""")
    hardware_type = _hardware_property('_hardware_type',
        """
        Controller hardware type. Specified values are:
        44 = brushless DC controller
        45 = multi-channel controller motherboard
        However, it doesn't seem to be confined to those two values.
        """)

    def identify_yourself(self):
        """
        Identify the controller by telling it to flash its front panel LED.
        """
        self._send_packet(0x0223)

if __name__ == '__main__':
    dev = APTController('83823336')
    dev.identify_yourself()
    print dev.hardware_type
