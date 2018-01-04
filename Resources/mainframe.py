import wx
from pyo import *
from .modules import *
from .utils import audio_config, dump_func
from .widgets import HeadTitle, Knob

class MainFrame(wx.Frame):
    def __init__(self, parent, title, pos=(50, 50), size=(1200, 800)):
        wx.Frame.__init__(self, parent, -1, title, pos, size)

        self.menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        moduleMenu = wx.Menu()
        for i, mod in enumerate(MODULES):
            moduleMenu.Append(MODULE_FIRST_ID+i, mod[0])
            moduleMenu.Bind(wx.EVT_MENU, self.loadModule, id=MODULE_FIRST_ID+i)
        fileMenu.AppendSubMenu(moduleMenu, "Modules")
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT, "Quit\tCtrl+Q")
        fileMenu.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)
        self.menubar.Append(fileMenu, "File")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_CLOSE, self.on_quit)

        # Setup audio server.
        sr, outdev = audio_config()
        self.server = Server(sr=sr, nchnls=AUDIO_NCHNLS, buffersize=512, duplex=0)
        self.server.setOutputDevice(outdev)
        self.server.boot()

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(APP_BACKGROUND_COLOUR)

        self.module = OscilModule(self.panel)
        self.module.SetBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.module.processing()

        # Audio vizualizers.
        self.outgain = SigTo(0.7)
        self.outsig = Sig(self.module.output, mul=self.outgain).out()
        self.outspec = Spectrum(self.outsig, function=dump_func)
        self.outspec.function = None
        self.outscope = Scope(self.outsig, function=dump_func)
        self.outscope.function = None

        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        leftbox = wx.BoxSizer(wx.VERTICAL)
        rightbox = wx.BoxSizer(wx.VERTICAL)

        leftboxup = wx.BoxSizer(wx.VERTICAL)
        self.leftboxmid = wx.BoxSizer(wx.VERTICAL)
        leftboxdown = wx.BoxSizer(wx.VERTICAL)

        sizer1 = self.createControlBox()
        sizer2 = self.createOutputBox()
        sizer5 = self.createSpectrum()
        sizer6 = self.createScope()

        leftboxup.Add(sizer1, 1, wx.ALL | wx.EXPAND, 5)

        head = HeadTitle(self.panel, "Interface du Module")
        self.leftboxmid.Add(head, 0, wx.EXPAND|wx.ALL, 5)
        self.leftboxmid.Add(self.module, 1, wx.EXPAND|wx.ALL, 5)

        leftboxdown.Add(sizer2, 1, wx.ALL | wx.EXPAND, 5)

        leftbox.Add(leftboxup, 0, wx.EXPAND)
        leftbox.Add(self.leftboxmid, 1, wx.EXPAND)
        leftbox.Add(leftboxdown, 0, wx.EXPAND)

        rightbox.Add(sizer5, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5)
        rightbox.Add(sizer6, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5)

        mainsizer.Add(leftbox, 1, wx.TOP|wx.BOTTOM|wx.LEFT | wx.EXPAND, 2)
        mainsizer.Add(rightbox, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 2)
        self.panel.SetSizerAndFit(mainsizer)

    def loadModule(self, evt):
        index = evt.GetId() - MODULE_FIRST_ID
        self.leftboxmid.Detach(self.module)
        self.module = MODULES[index][1](self.panel)
        self.module.SetBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.module.processing()
        self.leftboxmid.Add(self.module, 1, wx.EXPAND|wx.ALL, 5)
        self.leftboxmid.Layout()
        wx.GetTopLevelParent(self).SetTitle(MODULES[index][0])
        self.outsig.value = self.module.output
        
    def on_quit(self, evt):
        if self.server.getIsStarted():
            self.server.stop()
            time.sleep(0.25)
        self.Destroy()

    def createControlBox(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Contrôles Audio")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        rowbox = wx.BoxSizer(wx.HORIZONTAL)
            
        self.onOff = wx.ToggleButton(self.panel, label="Activer")
        rowbox.Add(self.onOff, 1, wx.ALL, 2)
        self.onOff.Bind(wx.EVT_TOGGLEBUTTON, self.handleAudio)
        self.rec = wx.ToggleButton(self.panel, label="Enregistrer")
        rowbox.Add(self.rec, 1, wx.ALL, 2)
        self.rec.Bind(wx.EVT_TOGGLEBUTTON, self.handleRec)

        sizer.Add(rowbox, 0, wx.EXPAND | wx.ALL, 2)

        return sizer

    def createOutputBox(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Sortie Audio")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        amplabel = wx.StaticText(self.panel, -1, "Volume (dB)")
        self.amp = PyoGuiControlSlider(self.panel, -60, 18, -12,
                                       orient=wx.HORIZONTAL)
        self.amp.setBackgroundColour(APP_BACKGROUND_COLOUR)

        self.amp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)
        self.meter = PyoGuiVuMeter(parent=self.panel, nchnls=AUDIO_NCHNLS,
                                   size=(5*AUDIO_NCHNLS, 200),
                                   orient=wx.HORIZONTAL)
        self.server.setMeter(self.meter)

        sizer.Add(amplabel, 0, wx.ALL | wx.EXPAND, 4)
        sizer.Add(self.amp, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        sizer.Add(self.meter, 0, wx.ALL | wx.EXPAND, 5)
        return sizer

    def createSpectrum(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Spectrogramme")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        toolbox = wx.BoxSizer(wx.HORIZONTAL)

        self.specFreeze = wx.ToggleButton(self.panel, -1, label="Freeze")
        self.specFreeze.Bind(wx.EVT_TOGGLEBUTTON, self.specFreezeIt)
        toolbox.Add(self.specFreeze, 1, wx.TOP|wx.LEFT, 5)

        self.specFreq = wx.ToggleButton(self.panel, -1, label="Freq Log")
        self.specFreq.SetValue(0)
        self.specFreq.Bind(wx.EVT_TOGGLEBUTTON, self.specFreqScale)
        toolbox.Add(self.specFreq, 1, wx.TOP|wx.LEFT, 5)

        self.specMag = wx.ToggleButton(self.panel, -1, label="Mag Log")
        self.specMag.SetValue(1)
        self.specMag.Bind(wx.EVT_TOGGLEBUTTON, self.specMagScale)
        toolbox.Add(self.specMag, 1, wx.TOP|wx.LEFT, 5)

        winchoices = ["Rectangular", "Hamming", "Hanning", "Bartlett", 
                      "Blackman 3-term", "Blackman-Harris 4", 
                      "Blackman-Harris 7", "Tuckey", "Half-sine"]
        self.specWin = wx.Choice(self.panel, -1, choices=winchoices)
        self.specWin.SetSelection(2)
        self.specWin.Bind(wx.EVT_CHOICE, self.specWinType)
        toolbox.Add(self.specWin, 1, wx.TOP|wx.LEFT, 5)

        sizechoices = ["64", "128", "256", "512", "1024",
                       "2048", "4096", "8192", "16384"]
        self.specSize = wx.Choice(self.panel, -1, choices=sizechoices)
        self.specSize.SetSelection(4)
        self.specSize.Bind(wx.EVT_CHOICE, self.specSetSize)
        toolbox.Add(self.specSize, 1, wx.TOP|wx.LEFT, 5)

        self.specAmp = Knob(self.panel, outFunction=self.specSetAmp)
        self.specAmp.SetBackgroundColour(APP_BACKGROUND_COLOUR)
        toolbox.Add(self.specAmp, 0.1, wx.TOP|wx.LEFT|wx.RIGHT, 7)
        
        sizer.Add(toolbox, 0, wx.EXPAND)

        self.spectrum = PyoGuiSpectrum(parent=self.panel, mscaling=1)
        self.spectrum.setAnalyzer(self.outspec)
        self.zoomH = HRangeSlider(self.panel, minvalue=0, maxvalue=0.5,
                                  valtype='float', function=self.specZoom, 
                                  backColour=APP_BACKGROUND_COLOUR)
        sizer.Add(self.spectrum, 1, wx.LEFT | wx.TOP | wx.EXPAND, 5)
        sizer.Add(self.zoomH, 0, wx.EXPAND|wx.LEFT, 5)

        return sizer

    def createScope(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Oscilloscope")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        toolbox = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self.panel, -1, label="Window length (ms):")
        toolbox.Add(label, 0, wx.LEFT|wx.TOP, 11)

        self.scopeLength = PyoGuiControlSlider(self.panel, 10, 1000, 50,
                                               log=True, orient=wx.HORIZONTAL)
        self.scopeLength.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.scopeSetLength)

        self.scopeLength.setBackgroundColour(APP_BACKGROUND_COLOUR)
        toolbox.Add(self.scopeLength, 1, wx.TOP|wx.LEFT, 14)

        self.scopeAmp = Knob(self.panel, outFunction=self.scopeSetAmp)
        self.scopeAmp.SetBackgroundColour(APP_BACKGROUND_COLOUR)
        toolbox.Add(self.scopeAmp, 0.1, wx.TOP|wx.LEFT|wx.RIGHT, 7)

        self.scope = PyoGuiScope(parent=self.panel)
        self.scope.setAnalyzer(self.outscope)

        sizer.Add(toolbox, 0, wx.EXPAND)
        sizer.Add(self.scope, 1, wx.LEFT | wx.TOP | wx.EXPAND, 5)
        return sizer

    ### Control methods ###
    def handleAudio(self, evt):
        if evt.GetInt():
            self.server.start()
        else:
            self.server.stop()

    def handleRec(self, evt):
        pass

    ### Spectrum methods ###
    def specFreezeIt(self, evt):
        if evt.GetInt() == 1:
            self.spectrum.obj.poll(0)
            self.specFreeze.SetLabel("Live")
        else:
            self.spectrum.obj.poll(1)
            self.specFreeze.SetLabel("Freeze")

    def specFreqScale(self, evt):
        if evt.GetInt() == 1:
            self.spectrum.setFscaling(1)
        else:
            self.spectrum.setFscaling(0)

    def specMagScale(self, evt):
        if evt.GetInt() == 1:
            self.spectrum.setMscaling(1)
        else:
            self.spectrum.setMscaling(0)

    def specWinType(self, evt):
        self.spectrum.obj.wintype = evt.GetInt()

    def specSetSize(self, evt):
        self.spectrum.obj.size = 1 << (evt.GetInt() + 6)

    def specZoom(self, values):
        self.spectrum.setLowFreq(self.spectrum.obj.setLowbound(values[0]))
        self.spectrum.setHighFreq(self.spectrum.obj.setHighbound(values[1]))

    def specSetAmp(self, value):
        value = rescale(value, ymin=0.0625, ymax=16, ylog=True)
        self.spectrum.obj.setGain(value)

    ### Scope methods ###
    def scopeSetLength(self, evt):
        length = evt.value * 0.001
        self.outscope.setLength(length)
        self.scope.setLength(length)

    def scopeSetAmp(self, value):
        self.scope.setGain(rescale(value, ymin=0.0445, ymax=10, ylog=True))

    ### Audio Output methods ###
    def changeGain(self, evt):
        self.outgain.value = pow(10, evt.value * 0.05)
