from .ocean_optics import (OceanOptics2k, OceanOptics4k, OceanOpticsNIRQuest,
	OceanOpticsMaya)

class USB2000(OceanOptics2k):
	_model_code = 4098
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

	# USB2000 reverses the endianness of its number of pixels?!?!
	@property
	def num_pixels(self):
		return struct.unpack('>H', self._query_status()[0:2])[0]

class ADC1000(OceanOptics2k):
	_model_code = 4100
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

class HR2000(OceanOptics2k):
	_model_code = 4106
	def __init__(self, *args, **kwargs):
		OceanOptics2k.__init__(self, *args, **kwargs)

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

class NIRQuest512(OceanOpticsNIRQuest):
	_model_code = 4134
	def __init__(self, *args, **kwargs):
		OceanOpticsNIRQuest.__init__(self, *args, **kwargs)

class NIRQuest256(OceanOpticsNIRQuest):
	_model_code = 4136
	def __init__(self, *args, **kwargs):
		OceanOpticsNIRQuest.__init__(self, *args, **kwargs)

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
