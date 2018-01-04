import wx
from pyo import *
from .constants import *

class OscilModule(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        labelfr = wx.StaticText(self, -1, "Fréquence en Hertz")
        self.fr = PyoGuiControlSlider(self, 20, 5000, 200, log=True,
                                      orient=wx.HORIZONTAL)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelga = wx.StaticText(self, -1, "Gain en dB")
        self.gain = PyoGuiControlSlider(self, -60, 12, -3,
                                        orient=wx.HORIZONTAL)
        self.gain.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.gain.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.fr, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(labelga, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.gain, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.output.freq = evt.value

    def changeGain(self, evt):
        self.output.mul = pow(10, evt.value * 0.05)

    def processing(self):
        self.output = Sine(freq=200, phase=[0,0], mul=0.707)

class TestModule(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        wavelabel = wx.StaticText(self, -1, "Waveform")
        self.wave = wx.Choice(self, -1, choices=["Ramp", "Sawtooth", "Square",
                                                "Triangle", "Pulse"])
        self.wave.SetSelection(2)
        self.wave.Bind(wx.EVT_CHOICE, self.changeWave)
        sizer.Add(wavelabel, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.wave, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def changeWave(self, evt):
        self.output.type = evt.GetInt()

    def processing(self):
        self.lfo = Sine([0.1, 0.05]).range(0, 1)
        self.lfo2 = Sine([0.2, 0.25]).range(100, 1000)
        self.output = LFO(freq=self.lfo2, sharp=self.lfo, type=2)

MODULES = [("Oscillator", OscilModule), ("Test", TestModule)]
