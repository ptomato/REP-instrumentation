import visa
from pyvisa import vpp43
from pyvisa.vpp43_constants import _to_int
from pyvisa.vpp43_attributes import attributes as _attributes
from pyvisa import vpp43_types
from pyvisa.visa_messages import completion_and_error_messages \
    as _completion_and_error_messages
import numpy as N
import struct


class OceanOpticsError(Exception):
    pass

# OceanOptics extended error code?
OO_ERROR_SYNC            = _to_int(0xBFFC0801L)
OO_ERROR_MODEL_NOT_FOUND = _to_int(0xBFFC0803L)
_completion_and_error_messages.update({
    OO_ERROR_SYNC: ("OO_ERROR_SYNC",
        "Instrument not synchronized properly. Power cycle the instrument."),
    OO_ERROR_MODEL_NOT_FOUND: ("OO_ERROR_MODEL_NOT_FOUND",
        "Instrument Model not found. This may mean that you selected the wrong "
        "instrument or your instrument did not respond.  You may also be using "
        "a model that is not officially supported by this driver.")
})

# NI USB-RAW extended attributes

VI_ATTR_USB_BULK_OUT_PIPE   = _to_int(0x3FFF01A2L)
VI_ATTR_USB_BULK_IN_PIPE    = _to_int(0x3FFF01A3L)
VI_ATTR_USB_INTR_IN_PIPE    = _to_int(0x3FFF01A4L)
VI_ATTR_USB_CLASS           = _to_int(0x3FFF01A5L)
VI_ATTR_USB_SUBCLASS        = _to_int(0x3FFF01A6L)
VI_ATTR_USB_ALT_SETTING     = _to_int(0x3FFF01A8L)
VI_ATTR_USB_END_IN          = _to_int(0x3FFF01A9L)
VI_ATTR_USB_NUM_INTFCS      = _to_int(0x3FFF01AAL)
VI_ATTR_USB_NUM_PIPES       = _to_int(0x3FFF01ABL)
VI_ATTR_USB_BULK_OUT_STATUS = _to_int(0x3FFF01ACL)
VI_ATTR_USB_BULK_IN_STATUS  = _to_int(0x3FFF01ADL)
VI_ATTR_USB_INTR_IN_STATUS  = _to_int(0x3FFF01AEL)
VI_ATTR_USB_CTRL_PIPE       = _to_int(0x3FFF01B0L)

VI_USB_PIPE_STATE_UNKNOWN = -1
VI_USB_PIPE_READY         = 0
VI_USB_PIPE_STALLED       = 1

VI_USB_END_NONE           = 0
VI_USB_END_SHORT          = 4
VI_USB_END_SHORT_OR_COUNT = 5

_attributes[VI_ATTR_USB_BULK_OUT_PIPE]   = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_BULK_IN_PIPE]    = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_INTR_IN_PIPE]    = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_CLASS]           = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_SUBCLASS]        = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_ALT_SETTING]     = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_END_IN]          = vpp43_types.ViUInt16
_attributes[VI_ATTR_USB_NUM_INTFCS]      = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_NUM_PIPES]       = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_BULK_OUT_STATUS] = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_BULK_IN_STATUS]  = vpp43_types.ViInt16
_attributes[VI_ATTR_USB_INTR_IN_STATUS]  = vpp43_types.ViInt16


class OceanOptics(object):

    def __init__(self, resource_name, timeout=10000):
        self._resource_name = resource_name
        self._timeout = timeout

        # Check model code to make sure we are using the right command language
        vi = vpp43.open(visa.resource_manager.session, resource_name)
        model_code = vpp43.get_attribute(vi, vpp43.VI_ATTR_MODEL_CODE)
        vpp43.close(vi)
        if model_code != self._model_code:
            raise OceanOpticsError('The spectrometer reported a different '
                'model code ({}) than the driver expected '
                '({}).'.format(model_code, self._model_code))

        self._vi = None  # connection not currently open

    def open(self):
        # Open instrument
        self._vi = vpp43.open(visa.resource_manager.session,
            self._resource_name)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_TMO_VALUE, self._timeout)
        # Timeout value should always be higher than integration time

        # Assign endpoint
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, self._in_pipe)
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_OUT_PIPE, self._out_pipe)

        # Initialize
        vpp43.write(self._vi, '\x01')  # Reset command

    def close(self):
        vpp43.close(self._vi)
        self._vi = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()
        return False  # don't suppress exceptions

    def _query_status(self):
        vpp43.write(self._vi, '\xFE')
        return vpp43.read(self._vi, 17)

    def _query_eeprom(self, configuration_index):
        vpp43.write(self._vi, '\x05' + chr(configuration_index))
        answer = vpp43.read(self._vi, 18)
        return answer[2:answer.find('\x00', 2)]  # from byte 3 to the next null

    def read_spectrum(self):
        # Request spectrum
        vpp43.write(self._vi, '\x09')
        return self._read_spectrum_data()

    def _read_spectrum_data(self):
        raise NotImplementedError

    @property
    def serial_number(self):
        return self._query_eeprom(0)

    @property
    def wavelength_calibration_coefficients(self):
        return (float(self._query_eeprom(1)),
            float(self._query_eeprom(2)),
            float(self._query_eeprom(3)),
            float(self._query_eeprom(4)))

    @property
    def wavelengths(self):
        p = N.arange(self.num_pixels)
        a, b, c, d = self.wavelength_calibration_coefficients
        return a + b * p + c * p ** 2.0 + d * p ** 3.0

    @property
    def num_pixels(self):
        return struct.unpack('<H', self._query_status()[0:2])[0]

    @property
    def integration_time(self):
        raise NotImplementedError

    @integration_time.setter
    def integration_time(self, value):
        raise NotImplementedError

    @property
    def lamp_enabled(self):
        return NotImplementedError

    @property
    def trigger_mode_value(self):
        return NotImplementedError

    @property
    def data_ready(self):
        """Whether data are available."""
        return self._query_status()[8] != '\x00'


class OceanOptics2k(OceanOptics):
    _in_pipe = 0x87
    _out_pipe = 0x02
    _min_integration_time = 3e-3
    max_counts = 4096

    def __init__(self, *args, **kwargs):
        OceanOptics.__init__(self, *args, **kwargs)

    def open(self):
        OceanOptics.open(self)
        # Reset must be followed by reading the acquired spectrum
        self._read_spectrum_data()

    @property
    def integration_time(self):
        """Integration time in seconds"""
        return int(self._query_status()[2:4].encode('hex'), 16) * 1e-3

    @integration_time.setter
    def integration_time(self, value):
        if value < self._min_integration_time:
            raise ValueError('Minimum integration time is '
                '{}'.format(self._min_integration_time))
        packed_value = struct.pack('<H', value * 1e3)
        vpp43.write(self._vi, '\x02' + packed_value)

    @property
    def lamp_enabled(self):
        """Whether the lamp signal is HIGH (True) or LOW (False)."""
        return self._query_status()[4] != '\x00'

    @property
    def trigger_mode_value(self):
        """Whatever this is"""
        return ord(self._query_status()[5])

    @property
    def request_in_progress(self):
        """Whether a request for a spectrum is in progress"""
        return self._query_status()[6] != '\x00'

    @property
    def timer_swap(self):
        """16-bit timer for integration time (0) or 8-bit timer (1)."""
        return ord(self._query_status()[7])

    def _read_spectrum_data(self):

        # Assign endpoint
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, 0x82)

        data = ''
        for i in range(32):
            lsbs = vpp43.read(self._vi, 64)
            msbs = vpp43.read(self._vi, 64)

            # Mask MSB high bits - instrument has 12-bit A/D
            msbs = ''.join([chr(ord(byte) & 0x0F) for byte in msbs])

            bs = bytearray(128)
            bs[::2] = lsbs
            bs[1::2] = msbs
            data += str(bs)

        # Read sync packet to check if properly synchronized
        sync_byte = vpp43.read(self._vi, 1)
        if sync_byte != '\x69' or len(data) != 4096:
            raise visa.VisaIOError(OO_ERROR_SYNC)

        # Reassign endpoint
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, 0x87)

        return N.fromstring(data, N.int16)


class OceanOptics4k(OceanOptics):
    _in_pipe = 0x81
    _out_pipe = 0x01
    _min_integration_time = 1e-5
    max_counts = 65536

    def __init__(self, *args, **kwargs):
        OceanOptics.__init__(self, *args, **kwargs)
        self._usb_speed = None
        self._saturation_level = None

    @property
    def integration_time(self):
        """Integration time in seconds"""
        return struct.unpack('<I', self._query_status()[2:6])[0] * 1e-6

    @integration_time.setter
    def integration_time(self, value):
        if value < self._min_integration_time:
            raise ValueError('Minimum integration time is '
                '{}'.format(self._min_integration_time))
        packed_value = struct.pack('<I', value * 1e6)
        vpp43.write(self._vi, '\x02' + packed_value)

    @property
    def lamp_enabled(self):
        """Whether the lamp signal is HIGH (True) or LOW (False)."""
        return self._query_status()[6] != '\x00'

    @property
    def trigger_mode_value(self):
        """Whatever this is"""
        return ord(self._query_status()[7])

    @property
    def num_packets(self):
        """Number of packets in spectrum"""
        return ord(self._query_status()[9])

    @property
    def power_on_status(self):
        """Whatever this is"""
        return ord(self._query_status()[10])

    @property
    def packet_count(self):
        """Whatever this is"""
        return ord(self._query_status()[11])

    @property
    def usb_speed(self):
        """USB speed, 'high' = 480 Mbps; 'full' = 12 Mbps"""
        usb_speed = ord(self._query_status()[14])
        # Cache the result
        self._usb_speed = 'high' if usb_speed == 128 else 'full'
        return self._usb_speed

    def _read_spectrum_data(self):
        usb_speed = self._usb_speed
        # Only query the value if there is no cached value
        if usb_speed is None:
            usb_speed = self.usb_speed

        n_packets, packet_length = (8, 512) if usb_speed == 'high' else (64, 64)
        # Assign endpoint
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, 0x82)

        data = ''
        for i in range(n_packets):
            data += vpp43.read(self._vi, packet_length)

        # Read sync packet to check if properly synchronized
        sync_byte = vpp43.read(self._vi, 1)
        if sync_byte != '\x69' or len(data) != 4096:
            raise visa.VisaIOError(OO_ERROR_SYNC)

        # Reassign endpoint
        vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, 0x81)

        spectrum = N.fromstring(data, N.dtype('<u2'))

        # Query and cache the saturation level if it is not cached
        if self._saturation_level is None:
            vpp43.write(self._vi, '\x05\x11')
            autonull_info = vpp43.read(self._vi, 17)
            self._saturation_level = (65536.0
                / struct.unpack('<H', autonull_info[6:8])[0])
            # Hmmm, it seems that this is an OceanOptics trick to sell
            # spectrometers with much less dynamic range than advertised!

        return spectrum * self._saturation_level


class OceanOpticsNIRQuest(OceanOptics):
    def __init__(self, *args, **kwargs):
        OceanOptics.__init__(self, *args, **kwargs)


class OceanOpticsMaya(OceanOptics):
    def __init__(self, *args, **kwargs):
        OceanOptics.__init__(self, *args, **kwargs)
