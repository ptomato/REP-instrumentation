Information and FAQ
===================

What devices can REP control?
-----------------------------

* Apogee CCD cameras (tested on Alta U1)
* Webcams (any that will work with OpenCV or DirectShow)
* Newport ESP300 motion controller
* Ocean Optics spectrometers (tested on USB2000)

Not all functionality of each device is available.
I programmed **REP** according to my own needs in the lab.

Will you add device X?
----------------------

Short answer: **yes, for money.**

Long answer:
**REP** is basically me dumping my lab code onto the internet.
Physics research is my day job, not writing code, so I code only what I have to to get my experiments done.
I make the code presentable and write the documentation in my spare time.

I enjoy writing code, but there are other projects that I'd rather work on in my free time: for one thing, I don't have the resources to hook up lab instruments at home and test them.
So I'd be happy to write code to control your instrument, but my development model is that you hire me **as an external consultant.**
My rates depend on how **complicated** the task is and what your **requirements** are.
In addition, there has to be some way for me to have access to the instrument, to test it.

For an estimate, contact me at **philip (dot) chimento (at) gmail (dot) com**.

If you can't or don't want to pay for development, why not consider writing your instrument driver yourself using the **REP** framework and **contributing it** to the project?
That way, **everybody benefits!**

Is REP bug-free?
----------------

Emphatically not.
**No code, ever, is bug-free.**
This is usually not a problem, but this code is meant to control actual physical machines which can malfunction.
Therefore, it is important that you realize that although I may be an **excellent programmer**, I make **no guarantees whatsoever** that REP will not fry your expensive lab equipment, explode your lab, annoy your cat, or change every ‘e’ in your doctoral thesis to ‘ə’.

Why is it called REP?
---------------------

One day I learned of the device called PPMS_ [1]_, which stands for the ridiculously generic name of “Physical Properties Measurement System.”
Indeed, I can't think of a physics experiment that doesn't measure physical properties.
Instantly, I knew that my instrumentation library would be given the equally ridiculously generic name of **Research in Experimental Physics**.

-----

.. _PPMS: http://www.qdusa.com/products/ppms.html
.. [1] “PPMS” is a trademark of Quantum Design, Inc.
