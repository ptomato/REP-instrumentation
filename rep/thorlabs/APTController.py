import time
import struct
import numpy as N
import d2xx


class APTController(object):

    def __init__(self, serial_number):
        self._channel_num = 1  # only support single-channel devices for now
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

        # Conversion units
        #self._position_units = 20000.0  # 1 mm = 20000 counts
        self._velocity_units = 767369.78  # 1 mm/s = 767369.78 counts/s ?
        self._acceleration_units = 262.0  # 1 mm/s^2 = 262 counts/s^2 ?
        #self._jerk_units = 92.2337  # 1 mm/s^3 = 92.2337 counts/s^3

    def _send_packet(self, msgid, param=(0, 0), data=None, dest=0x50, source=1):
        if data is None:
            packet = struct.pack('<HBBBB',
                msgid, param[0], param[1], dest, source)
            self._dev.write(packet)
        else:
            packet = struct.pack('<HHBB', msgid, len(data), dest | 0x80, source)
            self._dev.write(packet)
            self._dev.write(data)

    def _read_packet(self, expected_msgid):
        header = self._dev.read(6)
        #print map(hex, map(ord, header))
        msgid, length, dest, source = struct.unpack('<HHBB', header)
        if msgid != expected_msgid:
            raise IOError('Expected message ID {:04X}, but received {:04X}'.format(
                expected_msgid, msgid))
        if dest & 0x80:
            return self._dev.read(length)
        else:
            param1 = length & 0xFF
            param2 = (length >> 0xFF) & 0xFF
            return param1, param2

    def _get_hardware_info(self):
        self._send_packet(0x0005)  # MGMSG_HW_REQ_INFO
        data = self._read_packet(0x0006)  # MGMSG_HW_GET_INFO
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

    @property
    def channel_enabled(self):
        #if self._channel_num > self.n_channels:
        #    raise ValueError('Invalid channel number {}'.self._channel_num)
        self._send_packet(0x0211, param=(self._channel_num, 0))
        # MGMSG_MOD_REQ_CHANENABLESTATE
        chan, state = self._read_packet(0x0212)  # MGMSG_MOD_GET_CHANENABLESTATE
        if chan != self._channel_num:
            raise IOError('Requested state of channel {}, '
                'but device returned channel {}'.format(
                    self._channel_num, chan))
        if state in (0, 1):  # apparently 0 is valid as well?!
            return True
        elif state == 2:
            return False
        else:
            raise IOError('Device returned invalid state {}'.format(state))

    @channel_enabled.setter
    def channel_enabled(self, value):
        state = (2, 1)[int(bool(value))]
        self._send_packet(0x0210, param=(self._channel_num, state))
        # MGMSG_MOD_SET_CHANENABLESTATE

        # A spurious 0 byte is placed in the queue??
        rx_queue_length, _, _ = self._dev.getStatus()
        if rx_queue_length == 1:
            garbage = ord(self._dev.read(1))
            print 'Spurious byte {:02X}'.format(garbage)

    def _get_velocity_parameters(self):
        self._send_packet(0x0414, param=(self._channel_num, 0))
        # MGMSG_MOT_REQ_VELPARAMS
        data = self._read_packet(0x0415)  # MGMSG_MOT_GET_VELPARAMS
        chan, _, accel_counts, max_velocity_counts = struct.unpack('<HIII',
            data)
        if chan != self._channel_num:
            raise IOError('Requested state of channel {}, '
                'but device returned channel {}'.format(
                    self._channel_num, chan))
        self._accel_counts = accel_counts
        self._max_velocity_counts = max_velocity_counts

    @property
    def acceleration(self):
        """Acceleration in mm/s^2."""
        self._get_velocity_parameters()
        return self._accel_counts / self._acceleration_units

    @acceleration.setter
    def acceleration(self, value):
        self._get_velocity_parameters()
        data = struct.pack('<HIII', self._channel_num, 0,
            int(value * self._acceleration_units),
            self._max_velocity_counts)
        self._send_packet(0x0413, data=data)  # MGMSG_MOT_SET_VELPARAMS

    @property
    def max_velocity(self):
        """Maximum velocity in mm/s."""
        self._get_velocity_parameters()
        return self._max_velocity_counts / self._velocity_units

    @max_velocity.setter
    def max_velocity(self, value):
        self._get_velocity_parameters()
        data = struct.pack('<HIII', self._channel_num, 0,
            self._accel_counts,
            int(value * self._velocity_units))
        self._send_packet(0x0413, data=data)  # MGMSG_MOT_SET_VELPARAMS

    def identify_yourself(self):
        """
        Identify the controller by telling it to flash its front panel LED.
        """
        self._send_packet(0x0223)  # MGMSG_MOD_IDENTIFY

if __name__ == '__main__':
    dev = APTController('83823336')
    dev.identify_yourself()
    print dev.device_info
    print dev.max_velocity
    dev.max_velocity = 0.1
    print dev.max_velocity
