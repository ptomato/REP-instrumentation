import visa
from pyvisa import vpp43
from pyvisa.vpp43_constants import _to_int
from pyvisa.vpp43_attributes import attributes as _attributes
from pyvisa import vpp43_types
from pyvisa.visa_messages import completion_and_error_messages \
	as _completion_and_error_messages
import numpy as N

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
	
	if model_code in (4098, 4100, 4106):
		# USB2000, ADC1000, HR2000
		return OceanOptics2k(resource_name, model_code, *args, **kwargs)
	if model_code == 4114:
		return HR4000(resource_name, model_code, *args, **kwargs)
	if model_code == 4118:
		return HR2000Plus(resource_name, model_code, *args, **kwargs)
	if model_code == 4120:
		return QE65000(resource_name, model_code, *args, **kwargs)
	if model_code == 4126:
		return USB2000Plus(resource_name, model_code, *args, **kwargs)
	if model_code == 4130:
		return USB4000(resource_name, model_code, *args, **kwargs)
	if model_code in (4134, 4136):
		# NIRQuest512, NIRQuest256
		return OceanOpticsNIRQuest(resource_name, model_code, *args, **kwargs)
	if model_code in (4138, 4140):
		# Maya Pro, Maya
		return OceanOpticsMaya(resource_name, model_code, *args, **kwargs)
	if model_code == 4160:
		return Torus(resource_name, model_code, *args, **kwargs)

	raise visa.VisaIOError(VI_ERROR_OO_MODEL_NOT_FOUND)


class OceanOptics(object):

	def __init__(self, *args, **kwargs):
		resource_name = args[0]
		model_code = args[1]
		in_pipe = kwargs.pop('in_pipe')
		out_pipe = kwargs.pop('out_pipe')
		timeout = kwargs.pop('timeout', 10000)

		self._model = model_code

		# Open instrument
		self._vi = vpp43.open(visa.resource_manager.session, resource_name)
		vpp43.set_attribute(self._vi, vpp43.VI_ATTR_TMO_VALUE, timeout)
		# Timeout value should always be higher than integration time

		# Assign endpoint
		vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_IN_PIPE, in_pipe)
		vpp43.set_attribute(self._vi, VI_ATTR_USB_BULK_OUT_PIPE, out_pipe)

		# Initialize
		vpp43.write(self._vi, '\x01')  # Reset command
	
	def close(self):
		vpp43.close(self._vi)
	
	def __enter__(self):
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

class OceanOptics2k(OceanOptics):
	def __init__(self, *args, **kwargs):
		kwargs['in_pipe'] = 0x87
		kwargs['out_pipe'] = 0x02
		OceanOptics.__init__(self, *args, **kwargs)
	
	@property
	def num_pixels(self):
		return int(self._query_status()[0:2].encode('hex'), 16)
	
	@property
	def integration_time(self):
	    """Integration time in milliseconds"""
	    return int(self._query_status()[2:4].encode('hex'), 16)
	
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

class OceanOptics4k(OceanOptics):
	def __init__(self, *args, **kwargs):
		kwargs['in_pipe'] = 0x81
		kwargs['out_pipe'] = 0x01
		OceanOptics.__init__(self, *args, **kwargs)

		# Query USB speed
		#usb_speed = ord(self._query_status()[14])
		#self._usb_speed = 'high' if usb_speed == 128 else 'full'
		# 128 = High, 480 Mbps; 0 = Full, 12 Mbps

class HR4000(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class HR2000Plus(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class QE65000(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class USB2000Plus(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class USB4000(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

class OceanOpticsNIRQuest(OceanOptics):
	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)

class OceanOpticsMaya(OceanOptics):
	def __init__(self, *args, **kwargs):
		OceanOptics.__init__(self, *args, **kwargs)

class Torus(OceanOptics4k):
	def __init__(self, *args, **kwargs):
		OceanOptics4k.__init__(self, *args, **kwargs)

if __name__ == '__main__':
	import gtk
	import gobject
	import matplotlib
	matplotlib.use('gtkagg')
	from matplotlib.backends.backend_gtkagg \
		import FigureCanvasGTKAgg as FigureCanvas
	from matplotlib.figure import Figure

	win = gtk.Window()
	win.connect('destroy', gtk.main_quit)
	win.set_default_size(600, 400)
	win.set_title('Mini Spectrometer')

	fig = Figure()
	ax = fig.gca()
	ax.set_xlabel('Wavelength (nm)')
	ax.set_ylabel('Counts')
	ax.set_ylim(0, 4096)

	canvas = FigureCanvas(fig)
	win.add(canvas)

	sm = autodetect_spectrometer('USB2000') 
	title = '{}, {} pixels, {} ms'.format(sm.serial_number,
		sm.num_pixels, sm.integration_time)
	ax.set_title(title)
	x = sm.wavelengths
	y = sm.read_spectrum()
	line, = ax.plot(x, y)

	def update_plot():
		y = sm.read_spectrum()
		line.set_ydata(y)
		fig.canvas.draw()
		return True

	gobject.timeout_add(100, update_plot)
	
	win.show_all()
	gtk.main()
	sm.close()
