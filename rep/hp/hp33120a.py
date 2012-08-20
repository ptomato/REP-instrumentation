import visa

__all__ = ['HP33120A']


class HP33120A(visa.GpibInstrument):
    """HP 33120A 15 MHz function and arbitrary waveform generator"""
    def __init__(self, *args, **kwargs):
        super(HP33120A, self).__init__(*args, **kwargs)

    @property
    def id_string(self):
        return self.ask('*idn?')

    def set_dc_voltage(self, voltage):
        """
        Set the function generator to output a DC voltage. Specify the @voltage
        parameter in volts.
        """
        # Must divide by 2, because the offset is in peak-to-peak volts?!
        print 'APPL:DC DEF,DEF,{:f}'.format(voltage / 2.0)
        self.write('APPL:DC DEF,DEF,{:f}'.format(voltage / 2.0))

if __name__ == '__main__':
    dev = HP33120A(10)
    print dev.id_string
    dev.set_dc_voltage(0)
