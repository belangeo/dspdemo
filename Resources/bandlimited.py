# Copyright 2018 Olivier Belanger
#
# This file is part of pyo-tools.
#
# pyo-tools is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyo-tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pyo-tools. If not, see <http://www.gnu.org/licenses/>.
import math
from pyo64 import *

class DSPDemoBLOsc(PyoObject):
    """
    Band-limited oscillator that can crossfade between multiple waveforms.

    This oscillator can produce, according to its `shape` argument, a waveform
    that crossfades between a sawtooth, a square and a triangle waveform. The
    harmonics of the signal will never exceed the nyquist frequency (half the
    sampling rate).

    The sawtooth, square and triangle shapes are obtained by manipulating a
    Band-Limited Impulse Train (BLIT) with integration processes and comb filters.

    :Parent: :py:class:`PyoObject`

    :Args:

        freq: float or PyoObject, optional
            Fundamental frequency in cycles per second. Fundamental must be in
            the range 20 to 4000 Hz. Defaults to 100.
        bright: float or PyoObject, optional
            Brightness of the waveform, used to compute the number of harmonics
            for the given fundamental frequency. If set to 1, all harmonics below
            the nyquist frequency will be present. 0 means only a few harmonics.
            Defaults to 1.
        shape: float or PyoObject, optional
            Shape of the waveform. The range 0 to 1 will produce a crossfade
            between a sawtooth, a square and a triangle waveform.
            Defaults to 0.
        
    >>> s = Server().boot()
    >>> s.start()
    >>> from pyotools import *
    >>> bright = Sine(freq=[.1,.15]).range(0.1, 0.9)
    >>> shape = Sine(freq=[.2,.25]).range(0, 1)
    >>> blo = BLOsc(freq=200, bright=bright, shape=shape, mul=0.3).out()
    
    """
    def __init__(self, freq=100, bright=1, shape=0, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        # Raw arguments so that we can retrieve them with the attribute syntax.
        self._freq = freq
        self._bright = bright
        self._shape = shape
        # Audio conversions to facilitate computation.
        self._afreq = Sig(self._freq)
        self._abright = Sig(self._bright)
        self._ashape = Sig(self._shape)
        # Clipping values.
        self._cfreq = Clip(self._afreq, 20, 4000)
        self._cbright = Clip(self._abright, min=0, max=1, mul=0.99, add=0.001)
        self._cshape = Clip(self._ashape, min=0, max=1, mul=0.9999)

        sr = self._afreq.getSamplingRate()
        oneOverSr = 1.0 / sr

        # Compute the number of harmonics to generate.
        self._harms = sr / 2.1 / self._cfreq * self._cbright
        self._charms = Max(self._harms, 1.0)
        self._charms2 = self._charms + 1
        self._frac = self._charms - Floor(self._charms)

        # Scaling.
        self._ampscl = Scale(self._cbright, outmin=0.02, outmax=1)
        self._sqrscl = Scale(self._cfreq, 20, 4000, 0.0625, 0.125)
        self._triscl = Scale(self._cfreq, 20, 4000, 0.01, 0.5)

        # zero-centered impulse train.
        self._blit1 = Blit(freq=self._cfreq, harms=self._charms)
        self._blit2 = Blit(freq=self._cfreq, harms=self._charms2)
        self._blit = Interp(self._blit1, self._blit2, self._frac)
        self._train = DCBlock(self._blit)

        # Integrated impulse train = sawtooth.
        self._saw = DCBlock(Delay(self._train, oneOverSr, 1, oneOverSr))

        # sawtooth + comb filter = square wave.
        self._dlay = 1.0 / self._cfreq * 0.5
        self._sqr = Delay(self._saw, self._dlay, 0, 0.03, -1, self._saw)
        self._sqr2 = Delay(self._sqr, self._dlay, 0, 0.03, -1, self._sqr)
        self._sqr3 = Delay(self._sqr2, self._dlay, 0, 0.03, -1, self._sqr2)
        self._sqr4 = Delay(self._sqr3, self._dlay, 0, 0.03, -1, self._sqr3)
        self._square = self._sqr4 * self._sqrscl

        # Integrated square wave = triangle wave.
        self._tri = DCBlock(Delay(self._square, oneOverSr, 1, oneOverSr))

        # Linearly interpolate between the three waveforms.
        self._trntab = LinTable([(0,1), (200,0), (400,0), (800,0)], size=800)
        self._sawtab = LinTable([(0,0), (200,1), (400,0), (800,0)], size=800)
        self._sqrtab = LinTable([(0,0), (200,0), (400,1), (800,0)], size=800)
        self._tritab = LinTable([(0,0), (200,0), (400,0), (800,1)], size=800)
        self._index = Scale(self._cshape, exp=1)
        self._trngain = Pointer(self._trntab, self._index)
        self._sawgain = Pointer(self._sawtab, self._index)
        self._sqrgain = Pointer(self._sqrtab, self._index)
        self._trigain = Pointer(self._tritab, self._index)
        self._choose = (self._train * self._trngain + self._saw * self._sawgain + 
                        self._square * self._sqrgain + self._tri * self._triscl * 
                        self._trigain) * self._ampscl

        # A Sig is the best way to properly handle "mul" and "add" arguments.        
        self._output = Sig(self._choose, mul, add)
        # Create the "_base_objs" attribute. This is the object's audio output.
        self._base_objs = self._output.getBaseObjects()

    def setFreq(self, x):
        """
        Replace the `freq` attribute.

        :Args:

            x: float or PyoObject
                New `freq` attribute.

        """
        self._freq = x
        self._afreq.value = x

    def setBright(self, x):
        """
        Replace the `bright` attribute.

        :Args:

            x: float or PyoObject
                New `bright` attribute.

        """
        self._bright = x
        self._abright.value = x

    def setShape(self, x):
        """
        Replace the `shape` attribute.

        :Args:

            x: float or PyoObject
                New `shape` attribute.

        """
        self._shape = x
        self._ashape.value = x

    def play(self, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def ctrl(self, map_list=None, title=None, wxnoserver=False):
        self._map_list = [SLMap(20, 4000, "log", "freq", self._freq),
                          SLMap(0, 1, "lin", "bright", self._bright),
                          SLMap(0, 1, "lin", "shape", self._shape),
                          SLMapMul(self._mul)]
        PyoObject.ctrl(self, map_list, title, wxnoserver)

    @property
    def freq(self):
        """float or PyoObject. Fundamental frequency in cycles per second.""" 
        return self._freq
    @freq.setter
    def freq(self, x): self.setFreq(x)

    @property
    def bright(self):
        """float or PyoObject. Brightness between 0 and 1.""" 
        return self._bright
    @bright.setter
    def bright(self, x): self.setBright(x)

    @property
    def shape(self):
        """float or PyoObject. Waveform shape between 0 and 1.""" 
        return self._shape
    @shape.setter
    def shape(self, x): self.setShape(x)

class SchroederVerb1:
    def __init__(self, input, size=0.5, damp=0.5):
        self.input = input
        self.size = SigTo(size)
        self.damp = SigTo(damp)
        self.sizeFactor = Scale(self.size, outmin=0.7, outmax=1.3)
        self.dampFactor = Scale(self.damp, outmin=10000, outmax=500)
        self.comb1 = Delay(self.input, [0.0297,0.0277], self.sizeFactor*0.65)
        self.comb2 = Delay(self.input, [0.0371,0.0393], self.sizeFactor*0.51)
        self.comb3 = Delay(self.input, [0.0411,0.0409], self.sizeFactor*0.5)
        self.comb4 = Delay(self.input, [0.0137,0.0155], self.sizeFactor*0.73)

        self.combsum = self.input+self.comb1+self.comb2+self.comb3+self.comb4

        self.all1 = Allpass(self.combsum, [.005,.00507], self.sizeFactor*0.75)
        self.all2 = Allpass(self.all1, [.0117,.0123], self.sizeFactor*0.61)
        self.output = Tone(self.all2, freq=self.dampFactor, mul=.4)

    def setSize(self, x):
        self.size.value = x

    def setDamp(self, x):
        self.damp.value = x

class SchroederVerb2:
    def __init__(self, input, size=0.5, damp=0.5):
        self.input = input
        self.size = SigTo(size)
        self.damp = SigTo(damp)
        self.sizeFactor = Scale(self.size, outmin=0.5, outmax=1.5)
        self.dampFactor = Scale(self.damp, outmin=1.75, outmax=0.25)
        self.b1 = Allpass(self.input, [.0204,.02011], self.sizeFactor*0.35)
        self.b2 = Allpass(self.b1, [.06653,.06641], self.sizeFactor*0.41)
        self.b3 = Allpass(self.b2, [.035007,.03504], self.sizeFactor*0.5)
        self.b4 = Allpass(self.b3, [.023021 ,.022987], self.sizeFactor*0.65)

        self.c1 = Tone(self.b1, self.dampFactor*5000, mul=0.7)
        self.c2 = Tone(self.b2, self.dampFactor*3000, mul=0.7)
        self.c3 = Tone(self.b3, self.dampFactor*1500, mul=0.7)
        self.c4 = Tone(self.b4, self.dampFactor*500, mul=0.7)

        self.output = self.c1+self.c2+self.c3+self.c4

    def setSize(self, x):
        self.size.value = x

    def setDamp(self, x):
        self.damp.value = x

class TriTable(PyoTableObject):
    """
    Square waveform generator.
    Generates square waveforms made up of fixed number of harmonics.
    :Parent: :py:class:`PyoTableObject`
    :Args:
        order : int, optional
            Number of harmonics square waveform is made of. The waveform will 
            contains `order` odd harmonics. Defaults to 10.
        size : int, optional
            Table size in samples. Defaults to 8192.
    >>> s = Server().boot()
    >>> s.start()
    >>> t = TriTable(order=15).normalize()
    >>> a = Osc(table=t, freq=[199,200], mul=.2).out()
    """
    def __init__(self, order=10, size=8192):
        PyoTableObject.__init__(self, size)
        self._order = order
        self._tri_table = HarmTable(self._create_list(order), size)
        self._base_objs = self._tri_table.getBaseObjects()
        self.normalize()

    def _create_list(self, order):
        # internal method used to compute the harmonics's weight
        l = []
        ph = 1.0
        for i in range(1,order*2):
            if i % 2 == 0:
                l.append(0)
            else:
                l.append(ph / (i*i))
                ph *= -1
        return l
    
    def setOrder(self, x):
        """
        Change the `order` attribute and redraw the waveform.
        
        :Args:
        
            x : int
                New number of harmonics
        """      
        self._order = x
        self._tri_table.replace(self._create_list(x))
        self.normalize()
        self.refreshView()

    @property
    def order(self): 
        """int. Number of harmonics triangular waveform is made of."""
        return self._order
    @order.setter
    def order(self, x): self.setOrder(x)

class AdditivePartial:
    def __init__(self):
        self.env = Adsr(attack=0.01, decay=0.1, sustain=0.7, release=0.5, dur=0)
        self.freq = SigTo(200, time=0.001)
        self.ampi = Randi(-1, 1, 1)
        self.amph = Randh(-1, 1, 1)
        self.ampn = BrownNoise()
        self.ampvar = Selector([self.ampi, Port(self.amph, 0.001, 0.001), self.ampn], voice=0.00, mul=0, add=1)
        self.frqi = Randi(-1, 1, 1)
        self.frqh = Randh(-1, 1, 1)
        self.frqn = BrownNoise()
        self.frqvar = Selector([self.frqi, Port(self.frqh, 0.001, 0.001), self.frqn], voice=0.00, mul=0, add=1)
        self.amplitude = self.env * self.ampvar
        self.frequency = self.freq * self.frqvar
        self.output = Osc(HarmTable(), freq=self.frequency, mul=self.amplitude)

    def setAmpVarAmp(self, x):
        self.ampvar.mul = x

    def setAmpVarFreq(self, x):
        self.ampi.freq = x
        self.amph.freq = x

    def setAmpVarType(self, x):
        self.ampvar.voice = x

    def setFreqVarAmp(self, x):
        self.frqvar.mul = x

    def setFreqVarFreq(self, x):
        self.frqi.freq = x
        self.frqh.freq = x

    def setFreqVarType(self, x):
        self.frqvar.voice = x

    def setWaveform(self, table):
        self.output.table = table

    def play(self):
        self.env.play()

    def stop(self):
        self.env.stop()

class AdditiveSynthesis:
    def __init__(self, partials=30, attack=0.01, decay=0.1, sustain=0.7, release=0.5,
                 adamp=0.9, tdamp=0.9, freq=200, spread=1, avara=0, avarf=1,
                 avart=0, fvara=0, fvarf=1, fvart=0, wave=0):
        self.partials = partials
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.adamp = adamp
        self.tdamp = tdamp
        self.freq = freq
        self.spread = spread
        self.avara = avara
        self.avarf = avarf
        self.avart = avart
        self.fvara = fvara
        self.fvarf = fvarf
        self.fvart = fvart
        self.wave = wave

        self.tables = [HarmTable(), SawTable(5), SawTable(15), SawTable(30), SawTable(60),
                      SquareTable(5), SquareTable(15), SquareTable(30), SquareTable(60),
                      TriTable(3), TriTable(6), TriTable(12), TriTable(24)]

        self.oscils = [AdditivePartial() for i in range(60)]
        self.output = Sig(sum([oscil.output for oscil in self.oscils]))

    def setPartials(self, x):
        self.partials = x

    def setWaveform(self, which):
        [oscil.setWaveform(self.tables[which]) for oscil in self.oscils]

    def setAttack(self, x):
        self.attack = x

    def setDecay(self, x):
        self.decay = x

    def setSustain(self, x):
        self.sustain = x

    def setRelease(self, x):
        self.release = x

    def setAmpDamp(self, x):
        self.adamp = x

    def setTimeDamp(self, x):
        self.tdamp = x

    def setAmpVarAmp(self, x):
        [oscil.setAmpVarAmp(x) for oscil in self.oscils]

    def setAmpVarFreq(self, x):
        [oscil.setAmpVarFreq(x) for oscil in self.oscils]

    def setAmpVarType(self, x):
        [oscil.setAmpVarType(x) for oscil in self.oscils]

    def setFreqVarAmp(self, x):
        [oscil.setFreqVarAmp(x) for oscil in self.oscils]

    def setFreqVarFreq(self, x):
        [oscil.setFreqVarFreq(x) for oscil in self.oscils]

    def setFreqVarType(self, x):
        [oscil.setFreqVarType(x) for oscil in self.oscils]

    def computeEnvelopes(self):
        amp = 1.0
        sustain = self.sustain
        attack = self.attack
        decay = self.decay
        release = self.release
        for i in range(self.partials):
            self.oscils[i].env.mul = amp
            self.oscils[i].env.sustain = sustain
            amp *= self.adamp
            sustain *= self.adamp
            self.oscils[i].env.attack = attack
            self.oscils[i].env.decay = decay
            self.oscils[i].env.release = release
            attack *= self.tdamp
            decay *= self.tdamp
            release *= self.tdamp
            
    def computeFrequencies(self):
        for i in range(self.partials):
            self.oscils[i].freq.value = self.freq * (i+1) ** self.spread

    def setFreq(self, freq):
        self.freq = freq
        self.computeFrequencies()

    def setSpread(self, spread):
        self.spread = spread
        self.computeFrequencies()

    def stop(self):
        [oscil.stop() for oscil in self.oscils]

    def play(self):
        self.output.mul = 0.25 * math.sqrt(1.0 / self.partials) / self.adamp
        self.computeFrequencies()
        self.computeEnvelopes()
        [self.oscils[i].play() for i in range(self.partials)]

class PWM(PyoObject):
    """
    Pulse-Width-Modulation oscillator with optional linear-phase lowpass filter.

    This generator will oscillate between 1 and -1 according to its frequency,
    phase and duty cycle arguments, producing an idealized square wave. The
    term duty cycle describes the proportion of 'on' time to the regular
    interval or 'period' of time, that is the time spent on the positive value
    inside a single cycle.

    :Parent: :py:class:`PyoObject`

    :Args:

        freq: float or PyoObject, optional
            Frequency in cycles per second. Defaults to 100.
        phase: float or PyoObject, optional
            Phase of sampling, expressed as a fraction of a cycle (0 to 1).
            Defaults to 0.
        duty: float or PyoObject, optional
            Duty cycle, ie. the fraction of the whole period, between 0 and 1
            spent on the positive value. Defaults to 0.5.
        damp: int, optional
            Length, in samples, of the filter kernel used for lowpass filtering.
            The actual kernel length will be twice this value. Defaults to 0.
        
    >>> s = Server().boot()
    >>> s.start()
    >>> from pyotools import *
    >>> duty = Sine(freq=[.1, .15]).range(0.25, 0.75)
    >>> pwm = PWM(freq=100, phase=0, duty=duty, damp=6, mul=0.3).out()
    
    """
    def __init__(self, freq=100, phase=0, duty=0.5, damp=0, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        # Raw arguments so that we can retrieve them with the attribute syntax.
        self._freq = freq
        self._phase = phase
        self._duty = duty
        self._damp = damp
        # Audio conversion to declare the comparison only once.
        self._aduty = Sig(self._duty)
        # Cycle running phase.
        self._cycle = Phasor(freq, phase)
        # Split the cycle in two parts, 0 and 1.
        self._sqr = self._cycle < self._aduty
        # Convert to bipolar waveform.
        self._square = Sig(self._sqr, mul=2, add=-1)
        # Apply the lowpass filter.
        self._filter = IRWinSinc(self._square, freq=0, order=damp*2)
        # A Sig is the best way to properly handle "mul" and "add" arguments.        
        self._output = Sig(self._filter, mul, add)
        # Create the "_base_objs" attribute. This is the object's audio output.
        self._base_objs = self._output.getBaseObjects()

    def setFreq(self, x):
        """
        Replace the `freq` attribute.

        :Args:

            x: float or PyoObject
                New `freq` attribute.

        """
        self._freq = x
        self._cycle.freq = x

    def setPhase(self, x):
        """
        Replace the `phase` attribute.

        :Args:

            x: float or PyoObject
                New `phase` attribute.

        """
        self._phase = x
        self._cycle.phase = x

    def setDuty(self, x):
        """
        Replace the `duty` attribute.

        :Args:

            x: float or PyoObject
                New `duty` attribute.

        """
        self._duty = x
        self._aduty.value = x

    def setDamp(self, x):
        """
        Replace the `damp` attribute.

        :Args:

            x: int
                New `damp` attribute.

        """
        if x == self._damp:
            return
        self._damp = x
        self._filter = IRWinSinc(self._square, freq=0, order=x*2)
        self._output.value = self._filter

    def play(self, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def ctrl(self, map_list=None, title=None, wxnoserver=False):
        self._map_list = [SLMapFreq(self._freq),
                          SLMapPhase(self._phase),
                          SLMap(0, 1, "lin", "duty", self._duty),
                          SLMap(0, 32, "lin", "damp", self._damp, res="int", dataOnly=True),
                          SLMapMul(self._mul)]
        PyoObject.ctrl(self, map_list, title, wxnoserver)

    @property
    def freq(self):
        """float or PyoObject. Fundamental frequency in cycles per second.""" 
        return self._freq
    @freq.setter
    def freq(self, x): self.setFreq(x)

    @property
    def phase(self):
        """float or PyoObject. Phase of sampling between 0 and 1.""" 
        return self._phase
    @phase.setter
    def phase(self, x): self.setPhase(x)

    @property
    def duty(self):
        """float or PyoObject. Duty cycle between 0 and 1.""" 
        return self._duty
    @duty.setter
    def duty(self, x): self.setDuty(x)

    @property
    def damp(self):
        """int. High frequencies damping factor, in samples.""" 
        return self._damp
    @damp.setter
    def damp(self, x): self.setDamp(x)

class OscSync(PyoObject):
    """
    A soft sync oscillator which is reset according to a master frequency.

    Oscillator sync is a feature in some synthesizers with two or more
    oscillators. One oscillator (the master) will restart the period of another
    oscillator (the slave), so that they will have the same base frequency.
    This can produce a sound rich with harmonics. The timbre can be altered
    by varying the slave frequency. This object implement the overlap sync
    method to produce a soft sync oscillator. The `xfade` argument control
    the crossfade time between the two overlap. To produce a hard sync
    oscillator, set the `xfade` argument to 0. 

    :Parent: :py:class:`PyoObject`

    :Args:

        table: PyoTableObject
            The table to use as the oscillator waveform.
        master: float or PyoObject, optional
            Master frequency in cycles per second. Defaults to 100.
        slave: float or PyoObject, optional
            Slave frequency in cycles per second. Defaults to 110.
        xfade: float or PyoObject, optional
            Crossfade time in milliseconds, between 0 and 5. Defaults to 0.5.
        
    >>> s = Server().boot()
    >>> s.start()
    >>> from pyotools import *
    >>> table = HarmTable([1, .5, .33, .25, .2, .167, .143, .125, .111, .1])
    >>> master = Sig([80, 80], mul=Randi(min=0.99, max=1.01, freq=[1.3, 1.2]))
    >>> slave = Sine([0.1, 0.15], mul=master, add=master*2)
    >>> sosc = OscSync(table, master, slave, xfade=0.5, mul=0.3).out()
    
    """
    def __init__(self, table, master=100, slave=110, xfade=0.5, mul=1, add=0):
        PyoObject.__init__(self, mul, add)
        # Raw arguments so that we can retrieve them with the attribute syntax.
        self._table = table
        self._master = master
        self._slave = slave
        self._xfade = xfade
        # Audio conversion to facilitate the computation of the crossfade time.
        self._axfade = Sig(xfade)
        # The master running phase.
        self._phase = Phasor(master)
        # Output a trigger at the beginning of the cycle.
        self._trig = Select(self._phase < Delay1(self._phase), 1)
        # Overlap number (0 or 1)
        self._olap = Counter(self._trig, max=2)
        # Create a ramp from the overlap number.
        self._rtime = Clip(self._axfade, 0, 5, mul=0.001)
        self._ramp = SigTo(self._olap, time=self._rtime)
        # Amplitudes for the crossfade
        self._amp1 = Sig(1 - self._ramp, mul=0.5)
        self._amp2 = Sig(self._ramp, mul=0.5)
        # Triggers used to reset the oscillators
        self._trig1 = Select(self._olap, value = 0)
        self._trig2 = Select(self._olap, value = 1)
        # Two oscillators with independant reset and envelope
        self._osc1 = OscTrig(table, self._trig1, slave, interp=4, mul=self._amp1)
        self._osc2 = OscTrig(table, self._trig2, slave, interp=4, mul=self._amp2)
        # A Sig is the best way to properly handle "mul" and "add" arguments.        
        self._output = DCBlock(self._osc1 + self._osc2, mul, add)
        # Create the "_base_objs" attribute. This is the object's audio output.
        self._base_objs = self._output.getBaseObjects()

    def setTable(self, x):
        """
        Replace the `table` attribute.

        :Args:

            x: PyoTableObject
                New `table` attribute.

        """
        self._table = x
        self._osc1.table = x
        self._osc2.table = x

    def setMaster(self, x):
        """
        Replace the `master` attribute.

        :Args:

            x: float or PyoObject
                New `master` attribute.

        """
        self._master = x
        self._phase.freq = x

    def setSlave(self, x):
        """
        Replace the `slave` attribute.

        :Args:

            x: float or PyoObject
                New `slave` attribute.

        """
        self._slave = x
        self._osc1.freq = x
        self._osc2.freq = x

    def setXfade(self, x):
        """
        Replace the `xfade` attribute.

        :Args:

            x: float or PyoObject
                New `xfade` attribute.

        """
        self._xfade = x
        self._axfade.value = x

    def play(self, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.play(self, dur, delay)

    def stop(self):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].stop()
        return PyoObject.stop(self)

    def out(self, chnl=0, inc=1, dur=0, delay=0):
        for key in self.__dict__.keys():
            if isinstance(self.__dict__[key], PyoObject):
                self.__dict__[key].play(dur, delay)
        return PyoObject.out(self, chnl, inc, dur, delay)

    def ctrl(self, map_list=None, title=None, wxnoserver=False):
        self._map_list = [SLMap(20, 5000, "log", "master", self._master),
                          SLMap(20, 5000, "log", "slave", self._slave),
                          SLMap(0, 5, "lin", "xfade", self._xfade),
                          SLMapMul(self._mul)]
        PyoObject.ctrl(self, map_list, title, wxnoserver)

    @property
    def table(self):
        """PyoTableObject. The table to use as the oscillator waveform.""" 
        return self._table
    @table.setter
    def table(self, x): self.setTable(x)

    @property
    def master(self):
        """float or PyoObject. Master frequency in cycles per second.""" 
        return self._master
    @master.setter
    def master(self, x): self.setMaster(x)

    @property
    def slave(self):
        """float or PyoObject. Slave frequency in cycles per second.""" 
        return self._slave
    @slave.setter
    def slave(self, x): self.setSlave(x)

    @property
    def xfade(self):
        """float or PyoObject. Crossfade time in milliseconds, between 0 and 5.""" 
        return self._xfade
    @xfade.setter
    def xfade(self, x): self.setXfade(x)
