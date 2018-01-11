import wx
from pyo import *
from .constants import *

class TestModule(wx.Panel):
    """
    Module: Test
    ------------

    Ce module permet de sélectionner une forme d'onde et 
    de contrôler la fréquence fondamentale, la brillance
    et l'amplitude du son.

    Contrôles:
        Forme d'onde:
            Sélection de la forme d'onde.
        Fréquence en Hertz: 
            Fréquence fondamentale du son.
        Brillance: 
            Contrôle la quantité d'harmonique dans le son.
        Gain en dB:
            Amplitude du son en décibels.

    """
    name = "Test"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        wavelabel = wx.StaticText(self, -1, "Forme d'onde")
        self.wave = wx.Choice(self, -1, choices=["Rampe", "Dent de scie",
                                                 "Carrée", "Triangle",
                                                 "Train d'mpulsions"])
        self.wave.SetSelection(2)
        self.wave.Bind(wx.EVT_CHOICE, self.changeWave)

        labelfr = wx.StaticText(self, -1, "Fréquence en Hertz")
        self.fr = PyoGuiControlSlider(self, 20, 5000, 200, log=True,
                                      orient=wx.HORIZONTAL)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelsh = wx.StaticText(self, -1, "Brillance")
        self.sh = PyoGuiControlSlider(self, 0.01, 1, 0.01, log=True,
                                      orient=wx.HORIZONTAL)
        self.sh.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.sh.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSharp)

        labelga = wx.StaticText(self, -1, "Gain en dB")
        self.gain = PyoGuiControlSlider(self, -60, 12, -3,
                                        orient=wx.HORIZONTAL)
        self.gain.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.gain.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)

        sizer.Add(wavelabel, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.wave, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.fr, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(labelsh, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.sh, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(labelga, 0, wx.LEFT|wx.TOP, 7)
        sizer.Add(self.gain, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def changeWave(self, evt):
        self.output.type = evt.GetInt()

    def changeFreq(self, evt):
        self.output.freq = evt.value

    def changeSharp(self, evt):
        self.output.sharp = evt.value

    def changeGain(self, evt):
        self.output.mul = pow(10, evt.value * 0.05)

    def processing(self):
        self.output = LFO(freq=200, sharp=0.01, type=2, mul=0.707)

MODULES = [TestModule]
