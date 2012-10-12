import visa
import pyvisa.visa_exceptions

__all__ = ['ESP300Error', 'ESP300']


class ESP300Error(Exception):
    def __init__(self, code, timestamp, message):
        self.code = code
        self.timestamp = timestamp
        self.message = message

    def __str__(self):
        return 'Error {0}: {1}'.format(self.code, self.message)


def _command(instrument, command, axis, value):
    instrument.write('{0}{1}{2}'.format(axis, command, float(value)))


class AxisProperty(object):
    def __init__(self, instrument, command, readonly=False):
        self._instrument = instrument
        self._command = command
        self._readonly = readonly

    def __getitem__(self, key):
        try:
            values = self._instrument.ask_for_values('{0}{1}?'.format(key, self._command))
        except pyvisa.visa_exceptions.VisaIOError as e:
            # Check if there is an ESP300 error and if there is,
            # raise it instead
            self._instrument._check_error()
            # If not, re-raise the original exception
            raise e
        return values[0]

    def __setitem__(self, key, value):
        if self._readonly:
            raise AttributeError('Read-only property')
        _command(self._instrument, self._command, key, value)
        self._instrument._check_error()


class ESP300(visa.GpibInstrument, object):
    def __init__(self, *args, **kwargs):
        visa.GpibInstrument.__init__(self, *args, **kwargs)
        self.velocity = AxisProperty(self, 'VA')
        self.acceleration = AxisProperty(self, 'AC')
        self.deceleration = AxisProperty(self, 'AG')
        self.position = AxisProperty(self, 'PA')  # xxPA? is equivalent to xxTP
        self.backlash = AxisProperty(self, 'BA')

        # Clear any errors from the device
        while self.ask('TE?') != '0':
            pass

    # Dummy context manager
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    @property
    def id_string(self):
        return self.ask('*idn?')

    def _check_error(self):
        response = self.ask('TB?').split(',')
        try:
            code, timestamp, message = int(response[0]), int(response[1]), response[2]
            if code != 0:
                raise ESP300Error(code, timestamp, message)
        except ValueError:  # error code garbled
            raise ESP300Error(0, 0, 'An error occurred. '
                'In addition, the error message was garbled.')

    def move_relative(self, distance, axis=1):
        '''PR command - move relative'''
        _command(self, 'PR', axis, distance)
        self._check_error()

    def poll_motion_done(self, axis=1):
        '''MD (motion done status) command in a loop'''
        while self.ask('{0}MD?'.format(axis)) == '0':
            pass
        self._check_error()

    def sync(self, wait_time=0.0, stamp=0, axis=1):
        '''Waits until active commands have finished, then waits another
        @wait_time milliseconds, then sends a service request with the
        lowest five bytes equal to @stamp. Note that this does not pause
        program execution. Use wait_for_srq() to sync with this signal
        and pyvisa.vpp43.read_stb(Instrument.vi) to check the stamp.'''
        _command(self, 'WS', axis, wait_time)
        self.write('RQ{0}'.format(stamp))

if __name__ == '__main__':
    esp = ESP300(2)
    print esp.id_string
    print esp.position[1]
    esp.position[1] = 90.0
    esp.sync()
    esp.wait_for_srq()
