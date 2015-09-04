import visa

__all__ = ['TempStage', 'TMS91', 'TMS94']

# Original code kindly contributed by Filip Dominec <dominecf@fzu.cz>
# See http://www.fzu.cz/~dominecf/python/FDLabInstruments.py


class TempStage(object, visa.SerialInstrument):
    """Base class for Linkam temperature stages."""

    def __init__(self, *args, **kwargs):
        visa.SerialInstrument.__init__(self, *args, **kwargs)
        self.term_chars = visa.CR
        self.rate = 20

    # Dummy context manager
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    @property
    def temp(self):
        """Temperature in deg C"""
        raise NotImplementedError

    @property
    def status(self):
        """Current status byte"""
        raw_string = self.ask('T')
        return ord(raw_string[0])

    @property
    def rate(self):
        """Rate of temperature change (deg C/min); default is 20"""
        return self._rate

    @rate.setter
    def rate(self, value):
        self._rate = abs(value)


class TMS91(TempStage):
    def __init__(self, *args, **kwargs):
        super(TMS91, self).__init__(*args, **kwargs)
        # From Linkam91 manual: 9600 baud, 8 data bits, 1 stop bit, no parity,
        # using an RTS / CTS handshake.
        # Serial cable (linkam D25 -> serial D9) pins: 2-2 3-3 4-8 5-7 7-5;
        # connect 6,4 of PC together.
        self.baud_rate = 9600
        self.timeout = 20

    @property
    def temp(self):
        raw_string = self.ask('T')
        return float(raw_string[1:])

    @temp.setter
    def temp(self, value):
        self.write('R1{:d}'.format(self.rate))  # Sets rate
        self.write('L1{:d}'.format(value))  # Sets target temperature
        self.write('R20')  # End of current profile
        self.write('S')  # Starts action


class TMS94(TempStage):
    def __init__(self, *args, **kwargs):
        super(TMS94, self).__init__(*args, **kwargs)
        # From Linkam94 manual: 19200 baud, 8 data bits, 1 stop bit, no parity
        # using an RTS / CTS handshake.
        # All commands from the PC must end with a carriage return.
        # NOTE: When probed at baud_rate=9600, this model freezes.
        self.baud_rate = 19200
        self.timeout = 3

    @property
    def temp(self):
        raw_string = self.ask('T')
        return int(raw_string[6:10], 16) / 10.0

    @temp.setter
    def temp(self, value):
        self.write('R1{:04d}'.format(self.rate * 100))  # Sets rate
        self.write('L1{:04d}'.format(value * 10))  # Sets target temperature
        self.write('S')  # Starts action
