# reusable Mini Spectrometer component for testing

import numpy as N
from traits.api import HasTraits, Str, Int, Float, Array, Instance
from traitsui.api import View, Item, HGroup, VGroup, Handler
from chaco.api import Plot, ArrayPlotData
from enable.api import ComponentEditor
from pyface.timer.api import Timer
from rep.ocean_optics import autodetect_spectrometer

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
					format_str='%i pixels'),
				Item('integration_time', label='Integration time (s)')
			),
			Item('graph', editor=ComponentEditor(), show_label=False)
		),
		width=640, height=480, resizable=True,
		title='Mini Spectrometer',
		handler=WindowCloseHandler
	)

	def __init__(self, *args, **kwargs):
		super(MiniSpectrometer, self).__init__(*args, **kwargs)
		self._sm = autodetect_spectrometer('USB2000')
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
		graph.value_range.high_setting = self._sm.max_counts
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