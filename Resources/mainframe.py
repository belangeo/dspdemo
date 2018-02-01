import sys
import wx
from wx.adv import AboutDialogInfo, AboutBox
from pyo import *
from .modules import *
from .constants import *
from .utils import audio_config, dump_func
from .widgets import DocFrame, Knob, ShowCapture
from .images import DSPDemo_Icon_Small

class MainFrame(wx.Frame):
    def __init__(self, parent, title, pos=(50, 50), size=(1000, 700)):
        wx.Frame.__init__(self, parent, -1, title, pos, size)

        self.Bind(wx.EVT_CLOSE, self.onQuit)

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(APP_BACKGROUND_COLOUR)

        self.createMenuBar()

        self.createAudioServer()

        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        leftbox = wx.BoxSizer(wx.VERTICAL)
        rightbox = wx.BoxSizer(wx.VERTICAL)

        leftboxup = wx.BoxSizer(wx.VERTICAL)
        self.leftboxmid = wx.BoxSizer(wx.VERTICAL)
        leftboxdown = wx.BoxSizer(wx.VERTICAL)

        if WITH_VIDEO_CAPTURE:
            leftboxcam = self.createCaptureBox()

        sizer1 = self.createControlBox()
        sizer2 = self.createOutputBox()
        sizer5 = self.createSpectrum()
        sizer6 = self.createScope()

        self.loadInitModule()

        leftboxup.Add(sizer1, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)

        self.leftboxmid.Add(self.module, 1, wx.EXPAND|wx.ALL, 5)

        leftboxdown.Add(sizer2, 1, wx.ALL|wx.EXPAND, 5)

        leftbox.Add(leftboxup, 0, wx.EXPAND)
        leftbox.Add(self.leftboxmid, 1, wx.EXPAND)
        if WITH_VIDEO_CAPTURE:
            leftbox.Add(leftboxcam, 0, wx.EXPAND)
        leftbox.Add(leftboxdown, 0, wx.EXPAND)

        rightbox.Add(sizer5, 1, wx.TOP|wx.RIGHT|wx.EXPAND, 5)
        rightbox.Add(sizer6, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 5)

        mainsizer.Add(leftbox, 0, wx.TOP|wx.BOTTOM|wx.LEFT|wx.EXPAND, 2)
        mainsizer.Add(rightbox, 1, wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, 2)
        self.panel.SetSizerAndFit(mainsizer)

        self.Show()

    def createMenuBar(self):
        self.menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        moduleMenu = wx.Menu()
        for i, mod in enumerate(MODULES):
            moduleMenu.Append(MODULE_FIRST_ID+i, mod.name)
            moduleMenu.Bind(wx.EVT_MENU, self.loadModule, id=MODULE_FIRST_ID+i)
        fileMenu.AppendSubMenu(moduleMenu, "Modules")
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT, "Quitter\tCtrl+Q")
        fileMenu.Bind(wx.EVT_MENU, self.onQuit, id=wx.ID_EXIT)
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT,
                                   'À propos de %s %s' % (APP_NAME, APP_VERSION))
        self.Bind(wx.EVT_MENU, self.onHelpAbout, aboutItem)
        helpMenu.Append(SOURCE_DOC_ID, 
                        "Documentation de la Source Sonore\tShift+Ctrl+I")
        helpMenu.Bind(wx.EVT_MENU, self.onSourceDoc, id=SOURCE_DOC_ID)
        helpMenu.Append(MODULE_DOC_ID, "Documentation du Module\tCtrl+I")
        helpMenu.Bind(wx.EVT_MENU, self.onModuleDoc, id=MODULE_DOC_ID)
        self.menubar.Append(fileMenu, "Fichier")
        self.menubar.Append(helpMenu, "Aide")
        self.SetMenuBar(self.menubar)

    def createAudioServer(self):
        # Setup audio server.
        sr, outdev = audio_config()
        self.server = Server(sr, AUDIO_NCHNLS, AUDIO_BUFSIZE, AUDIO_DUPLEX)
        self.server.setOutputDevice(outdev)
        self.server.boot()

        # Audio vizualizers.
        self.fadein = Fader(1).play()
        self.outgain = SigTo(0.5, mul=self.fadein)
        self.outsig = Sig([0,0])
        self.outdisp = Sig([0]*3)
        self.outspec = Spectrum(self.outdisp, function=dump_func)
        self.outspec.function = None
        self.outscope = Scope(self.outdisp, function=dump_func)
        self.outscope.function = None
        if WITH_VIDEO_CAPTURE:
            self.voicerec = Input(0, mul=1).mix(2).out()
            self.fol = Follower(self.voicerec, freq=4)
            self.talk = self.fol > 0.02
            self.amp = Port(self.talk, risetime=0.25, falltime=0.5)
            self.ampscl = Scale(self.amp, outmin=1, outmax=0.3)
        else:
            self.ampscl = Sig(1)
        self.mixoutsig = Mix(self.outsig, 2, self.outgain*self.ampscl).out()

    def loadInitModule(self):
        self.module = InputOnlyModule(self.panel)
        self.module.SetBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.module.processing()
        wx.GetTopLevelParent(self).SetTitle("DSPDemo - " + InputOnlyModule.name)
        self.connectModuleToOutput()

    def loadModule(self, evt):
        index = evt.GetId() - MODULE_FIRST_ID
        oldmodule = self.module
        self.module = MODULES[index](self.panel)
        self.module.SetBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.module.processing()
        self.leftboxmid.Replace(oldmodule, self.module)
        oldmodule.Destroy()
        self.leftboxmid.Layout()
        wx.GetTopLevelParent(self).SetTitle("DSPDemo - " + MODULES[index].name)
        self.connectModuleToOutput()

    def connectModuleToOutput(self):
        self.outsig.value = self.module.output
        self.outdisp.value = [0] * 3
        num = len(self.module.display)
        for i in range(num):
            self.outdisp[i].setValue(self.module.display[i])
        
    def onQuit(self, evt):
        if self.server.getIsStarted():
            self.server.stop()
            time.sleep(0.25)
        self.Destroy()

    def onModuleDoc(self, evt):
        doc_frame = DocFrame(self, self.module.__doc__)

    def onSourceDoc(self, evt):
        src_frame = DocFrame(self, SOURCE_DOCUMENTATION)

    def onHelpAbout(self, evt):
        info = AboutDialogInfo()
        info.SetName(APP_NAME)
        info.SetVersion(APP_VERSION)
        if sys.platform != "darwin":
            info.SetIcon(DSPDemo_Icon_Small.GetIcon())
        info.SetCopyright("(C) 2018 Olivier Bélanger")
        info.SetDescription("\nDSPDemo est une application conçue pour analyser "
                            "et visualiser différents processus audio.\n")
        AboutBox(info, self)

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

    def createCaptureBox(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.webcam = ShowCapture(self.panel)
        sizer.Add(self.webcam, 0, wx.CENTER | wx.ALL, 5)
        return sizer

    def createOutputBox(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Sortie Audio")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        amplabel = wx.StaticText(self.panel, -1, "Volume (dB)")
        self.amp = PyoGuiControlSlider(self.panel, -60, 18, -6,
                                       orient=wx.HORIZONTAL)
        self.amp.setBackgroundColour(APP_BACKGROUND_COLOUR)
        self.amp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)

        self.meter = PyoGuiVuMeter(parent=self.panel, nchnls=AUDIO_NCHNLS,
                                   size=(5*AUDIO_NCHNLS, 200),
                                   orient=wx.HORIZONTAL)
        self.server.setMeter(self.meter)

        sizer.Add(amplabel, 0, wx.LEFT|wx.TOP|wx.EXPAND, 5)
        sizer.Add(self.amp, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        sizer.Add(self.meter, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        return sizer

    def createSpectrum(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self.panel, "Spectrogramme")
        sizer.Add(head, 0, wx.EXPAND|wx.BOTTOM, 2)

        toolbox = wx.BoxSizer(wx.HORIZONTAL)

        self.specFreq = wx.ToggleButton(self.panel, -1, label="Freq Log")
        self.specFreq.SetValue(0)
        self.specFreq.Bind(wx.EVT_TOGGLEBUTTON, self.specFreqScale)
        toolbox.Add(self.specFreq, 1, wx.TOP|wx.LEFT, 4)

        self.specMag = wx.ToggleButton(self.panel, -1, label="Mag Log")
        self.specMag.SetValue(1)
        self.specMag.Bind(wx.EVT_TOGGLEBUTTON, self.specMagScale)
        toolbox.Add(self.specMag, 1, wx.TOP|wx.LEFT, 4)

        self.specWin = wx.Choice(self.panel, -1, choices=WINCHOICES)
        self.specWin.SetSelection(2)
        self.specWin.Bind(wx.EVT_CHOICE, self.specWinType)
        toolbox.Add(self.specWin, 1, wx.TOP|wx.LEFT, 4)

        self.specSize = wx.Choice(self.panel, -1, choices=SIZECHOICES)
        self.specSize.SetSelection(4)
        self.specSize.Bind(wx.EVT_CHOICE, self.specSetSize)
        toolbox.Add(self.specSize, 1, wx.TOP|wx.LEFT, 4)

        self.specAmp = Knob(self.panel, outFunction=self.specSetAmp)
        self.specAmp.SetBackgroundColour(APP_BACKGROUND_COLOUR)
        toolbox.Add(self.specAmp, 0.1, wx.TOP|wx.LEFT|wx.RIGHT, 6)
        
        sizer.Add(toolbox, 0, wx.EXPAND)

        self.spectrum = PyoGuiSpectrum(parent=self.panel, mscaling=1)
        self.spectrum.setAnalyzer(self.outspec)
        self.spectrum.showChannelNames(False)
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

        label = wx.StaticText(self.panel, -1, "Taille de la fenêtre (ms):")
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
        self.scope.showChannelNames(False)

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
        if evt.GetInt():
            self.server.recstart()
        else:
            self.server.recstop()

    ### Spectrum methods ###
    def specFreqScale(self, evt):
        self.spectrum.setFscaling(evt.GetInt())

    def specMagScale(self, evt):
        self.spectrum.setMscaling(evt.GetInt())

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
