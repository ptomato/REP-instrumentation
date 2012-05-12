General examples
================

This is the general pattern for controlling an instrument.
Wherever possible, modules implement the context manager protocol.
For example, to control the fictional Frobnitz StuffMeasurer 3000::

    from rep.frobnitz import StuffMeasurer3000
    with StuffMeasurer3000(port=3) as instrument:
        data = instrument.measure_stuff()

If it's not feasible to use the context manager protocol in your program, you can also initialize and shut down the instruments like this::

    instrument = StuffMeasurer3000(port=3)
    instrument.open()
    data = instrument.measure_stuff()
    instrument.close()

Instrument settings
-------------------

Instrument settings correspond to properties in Python.
That is, you can get and set them just like any ordinary attribute, but all the necessary communication goes on behind the scenes.
For example, to control the frequency of the Frobnitz StuffMeasurer::

    instrument.frequency = 440.0  # in Hertz
    print 'Frequency is now {:.1f}'.format(instrument.frequency)

Actions
-------

Actions — like recording a measurement, or resetting the instrument — correspond to methods in Python.
For example, the following code resets the StuffMeasurer before starting a new measurement::

    instrument.reset()
    instrument.measure_stuff()
