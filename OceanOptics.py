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
	OO_ERROR_SYNC: ( "OO_ERROR_SYNC",
		"Instrument not synchronized properly. Power cycle the instrument." ),
	OO_ERROR_MODEL_NOT_FOUND: ( "OO_ERROR_MODEL_NOT_FOUND",
		"Instrument Model not found. This may mean that you selected the wrong "
		"instrument or your instrument did not respond.  You may also be using "
		"a model that is not officially supported by this driver." )
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

# Factory method which creates an appropriate instrument object depending
# on the model code that the unit identifies itself with
def autodetect_spectrometer(resource_name, *args, **kwargs):
	vi = vpp43.open(visa.resource_manager.session, resource_name)
	model_code = vpp43.get_attribute(vi, vpp43.VI_ATTR_MODEL_CODE)
	vpp43.close(vi)
	
	if model_code == 4098:
		return USB2000(resource_name, *args, **kwargs)
	if model_code == 4100:
		return ADC1000(resource_name, *args, **kwargs)
	if model_code == 4106:
		return HR2000(resource_name, *args, **kwargs)
	if model_code == 4114:
		return HR4000(resource_name, *args, **kwargs)
	if model_code == 4118:
		return HR2000Plus(resource_name, *args, **kwargs)
	if model_code == 4120:
		return QE65000(resource_name, *args, **kwargs)
	if model_code == 4126:
		return USB2000Plus(resource_name, *args, **kwargs)
	if model_code == 4130:
		return USB4000(resource_name, *args, **kwargs)
	if model_code == 4134:
		return NIRQuest512(resource_name, *args, **kwargs)
	if model_code == 4136:
		return NIRQuest256(resource_name, *args, **kwargs)
	if model_code == 4138:
		return MayaPro(resource_name, *args, **kwargs)
	if model_code == 4140:
		return Maya(resource_name, *args, **kwargs)
	if model_code == 4160:
		return Torus(resource_name, *args, **kwargs)

	raise visa.VisaIOError(VI_ERROR_OO_MODEL_NOT_FOUND)


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
		# Reset must be followed by reading the acquired spectrum
		self._read_spectrum_data()
	
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

		request_in_progress = False if status_string[6] == '\x00' else True
		timer_swap = ord(status_string[7])
		data_ready = False if status_string[8] == '\x00' else True
	
	def _query_eeprom(self, configuration_index):
		vpp43.write(self._vi, '\x05' + chr(configuration_index))
		answer = vpp43.read(self._vi, 18)
		return answer[2:answer.find('\x00', 2)] # from byte 3 to the next null

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
	def integration_time(self):
	    raise NotImplementedError
	    
	@integration_time.setter
	def integration_time(self, value):
	    raise NotImplementedError

class OceanOptics2k(OceanOptics):
	_in_pipe = 0x87
	_out_pipe = 0x02
	_min_integration_time = 3e-3

	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)
	
	@property
	def num_pixels(self):
		return int(self._query_status()[0:2].encode('hex'), 16)
	
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
	
	@property
	def data_ready(self):
	    """Whether data are available."""
	    return self._query_status()[8] != '\x00'
	
	def read_spectrum(self):

		# Request spectrum
		vpp43.write(self._vi, '\x09')
		return self._read_spectrum_data()

	def _read_spectrum_data(self):

		# Assign endpoint
		vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, 0x82)

		data = ''
		for i in range(32):
			lsbs = vpp43.read(self._vi, 64)
			msbs = vpp43.read(self._vi, 64)
			
			# Mask MSB high bits - instrument has 12-bit A/D
			msbs = ''.join([ chr(ord(byte) & 0x0F) for byte in msbs ])

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

class USB2000(OceanOptics2k):
	_model_code = 4098
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

class ADC1000(OceanOptics2k):
	_model_code = 4100
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

class HR2000(OceanOptics2k):
	_model_code = 4106
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

class OceanOptics4k(OceanOptics):
	_in_pipe = 0x81
	_out_pipe = 0x01
	_min_integration_time = 1e-5

	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)

		# Query USB speed
		#usb_speed = ord(self._query_status()[14])
		#self._usb_speed = 'high' if usb_speed == 128 else 'full'
		# 128 = High, 480 Mbps; 0 = Full, 12 Mbps

	@property
	def integration_time(self):
	    """Integration time in seconds"""
	    return int(self._query_status()[2:6].encode('hex'), 16) * 1e-6

	@integration_time.setter
	def integration_time(self, value):
		if value < self._min_integration_time:
			raise ValueError('Minimum integration time is '
				'{}'.format(self._min_integration_time))
		packed_value = struct.pack('<I', value * 1e6)
		vpp43.write(self._vi, '\x02' + packed_value)

class HR4000(OceanOptics4k):
	_model_code = 4114
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class HR2000Plus(OceanOptics4k):
	_model_code = 4118
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class QE65000(OceanOptics4k):
	_model_code = 4120
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class USB2000Plus(OceanOptics4k):
	_model_code = 4126
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class USB4000(OceanOptics4k):
	_model_code = 4130
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class OceanOpticsNIRQuest(OceanOptics):
	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)

class NIRQuest512(OceanOpticsNIRQuest):
	_model_code = 4134
	def __init__(self, *args, **kwargs):
		OceanOpticsNIRQuest.__init__(self, *args, **kwargs)

class NIRQuest256(OceanOpticsNIRQuest):
	_model_code = 4136
	def __init__(self, *args, **kwargs):
		OceanOpticsNIRQuest.__init__(self, *args, **kwargs)

class OceanOpticsMaya(OceanOptics):
	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)

class MayaPro(OceanOpticsMaya):
	_model_code = 4138
	def __init__(self, *args, **kwargs):
		OceanOpticsMaya.__init__(self, *args, **kwargs)

class Maya(OceanOpticsMaya):
	_model_code = 4140
	def __init__(self, *args, **kwargs):
		OceanOpticsMaya.__init__(self, *args, **kwargs)

class Torus(OceanOptics4k):
	_model_code = 4160
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

# reusable Mini Spectrometer component for testing

if __name__ == '__main__':
	from traits.api import HasTraits, Str, Int, Float, Array, Instance
	from traitsui.api import View, Item, HGroup, VGroup, Handler
	from chaco.api import Plot, ArrayPlotData
	from enable.api import ComponentEditor
	from pyface.timer.api import Timer

	class MiniSpectrometer(HasTraits):
		
		class WindowCloseHandler(Handler):
			def closed(self, info, is_ok):
				info.object.timer.Stop()
				info.object._sm.close()

		# Traits
		serial_number = Str()
		num_pixels = Int()
		integration_time = Float()
		wavelengths = Array()
		spectrum = Array()
		graph = Instance(Plot)
		timer = Instance(Timer)

		# GUI
		view = View(
			VGroup(
				HGroup(
					Item('serial_number', show_label=False, style='readonly',
						format_str='%s,'),
					Item('num_pixels', show_label=False, style='readonly',
						format_str='%i pixels,'),
					Item('integration_time', format_str='%e s')
				),
				Item('graph', editor=ComponentEditor(), show_label=False)
			),
			width=640, height=480, resizable=True,
			title='Mini Spectrometer',
			handler=WindowCloseHandler
		)

		def __init__(self, *args, **kwargs):
			super(MiniSpectrometer, self).__init__(*args, **kwargs)
			self._sm = autodetect_spectrometer('USB2000P')
			self._sm.open()

			self.serial_number = self._sm.serial_number
			self.num_pixels = self._sm.num_pixels
			self.integration_time = self._sm.integration_time
			self.wavelengths = self._sm.wavelengths

		def _graph_default(self):
			self._plotdata = ArrayPlotData(
				wavelengths=self.wavelengths,
				counts=N.zeros(self.num_pixels))
			graph = Plot(self._plotdata)
			self._renderer = graph.plot(('wavelengths', 'counts'),
				type='line')
			graph.index_axis.title = 'Wavelength (nm)'
			graph.value_axis.title = 'Counts'
			graph.value_range.low_setting = 0
			graph.value_range.high_setting = 4096
			return graph

		def _spectrum_changed(self, new_data):
			self._plotdata.set_data('counts', new_data)

		def _integration_time_changed(self, value):
			self._sm.integration_time = value
			self.integration_time = self._sm.integration_time

		def _update_plot(self):
			self.spectrum = self._sm.read_spectrum()

		def configure_traits(self, *args, **kw):
			# Start the timer when showing the window
			self.timer = Timer(100, self._update_plot)
			return super(MiniSpectrometer, self).configure_traits(*args, **kw)

	sm = MiniSpectrometer()
	sm.configure_traits()
