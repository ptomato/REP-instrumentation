import numpy as N
import visa

# Original code kindly contributed by Filip Dominec <dominecf@fzu.cz>
# See http://www.fzu.cz/~dominecf/python/FDLabInstruments.py


class Oscilloscope(object, visa.GpibInstrument):
    """A Tektronix digital sampling oscilloscope."""

    def __init__(self, *args, **kwargs):
        visa.GpibInstrument.__init__(self, *args, **kwargs)
        # Tektronix scope identifies as USB0::0x699::0x0401::C021641... etc.

    # Dummy context manager
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    @property
    def id_string(self):
        return self.ask('*IDN?')

    @property
    def event_status_register(self):
        return self.ask('*ESR?')

    def _get_waveform_from_channel(self, channel):
        # The channel must be selected first, TODO
        self.write(':DATA:SOU CH{};'.format(channel))

        # Get info about the waveform settings
        self.write(':DAT:WID 2;')
        y_multiplier = float(self.ask(':WFMP:YMU?'))
        y_offset = float(self.ask(':WFMP:YOF?'))
        y_zero = float(self.ask(':WFMP:YZE?'))

        # Retrieve waveform for selected channel as a long string with number of
        # samples prepended
        raw_wform = self.ask(':CURV?')
        data_points_num_digits = int(raw_wform[1])

        # Convert bytes to waveform
        wform = N.fromstring(raw_wform[(data_points_num_digits + 2):],
            N.dtype('>i2'))
        return (wform - y_offset) * y_multiplier - y_zero

    def get_waveforms(self, channels):
        """
        Retrieves the waveforms from the given channels as a numpy.ndarray.
        Returns an array of ndarrays, of length len(channels) + 1, with the
        timebase as the last element.
        @channels: array of integers (e.g. [1, 2])
        """

        # Configure scope record length (100kS and more causes lags)
        self.write(':HOR:RECORDL 10000')  # record length: (1k 10k ... 10M)

        self.write(':ACQ:STATE ON;')
        self.write(':ACQ:STATE OFF;')

        x_increment = float(self.ask(':WFMP:XIN?'))

        wforms = [self._get_waveform_from_channel(channel)
            for channel in channels]

        self.write(':ACQ:STATE ON;')

        # Generate linear timebase (matching the last wform)
        npoints = len(wforms[-1])
        timebase = N.linspace(0, x_increment * (npoints - 1), num=npoints)
        wforms.append(timebase)

        return wforms
