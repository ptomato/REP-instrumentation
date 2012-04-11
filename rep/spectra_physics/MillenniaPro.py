import visa

class MillenniaPro(visa.SerialInstrument, object):
	"""Millennia Pro Laser"""
	def __init__(self, com_port=1, *args, **kwargs):
		visa.SerialInstrument.__init__(self,
			'COM{}'.format(com_port),
			term_chars=visa.LF)
	
	@property
	def model(self):
		_, model_name, _, _ = self.ask('*idn?').split(',')
		return model_name
	
	@property
	def warmup_percentage(self):
		return int(self.ask('?warmup%')[:-1]) # strip trailing % character

if __name__ == '__main__':
	laser = MillenniaPro()
	print laser.model
	print laser.warmup_percentage, '% warm'
