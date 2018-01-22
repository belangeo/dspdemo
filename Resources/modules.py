import wx
from pyo import *
from .constants import *
from .bandlimited import DSPDemoBLOsc

class InputPanel(wx.Choicebook):
    def __init__(self, parent):
        wx.Choicebook.__init__(self, parent, -1, size=(300, -1))
        # Oscillateur auto-modulant, Pulse-Width-Modulation
        sources = [("Fichier sonore", self.createSoundfilePanel), 
                   ("Oscillateur anti-alias", self.createOscillatorPanel),
                   ("Générateur de bruit", self.createNoisePanel)]
        for source in sources:
            panel = source[1]()
            self.AddPage(panel, source[0])
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)

        ### Audio processing ###
        # Soundfile player
        self.soundtable = SndTable(initchnls=2)
        self.soundfile = Looper(self.soundtable, pitch=1, mode=0).stop()
        # Band-limited oscillator 
        self.oscfreq = SigTo(250, 0.05)
        self.oscbright = SigTo(0.5, 0.05)
        self.oscshape = SigTo(0, 0.05)
        self.oscillator = DSPDemoBLOsc(freq=self.oscfreq, bright=self.oscbright,
                                       shape=self.oscshape)
        # Noise generator
        self.whitenoise = Noise()
        self.pinknoise = PinkNoise()
        self.brownnoise = BrownNoise()
        self.noisegenerator = InputFader(self.whitenoise)

        # Audio output
        self.output = InputFader(self.soundfile)

    def OnPageChanged(self, evt):
        sel = evt.GetSelection()
        obj = [self.soundfile, self.oscillator, self.noisegenerator][sel]
        self.output.setInput(obj, 0.1)

    def createSoundfilePanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        row1 = wx.BoxSizer(wx.HORIZONTAL)

        loadbutton = wx.Button(panel, -1, "Choisir")
        loadbutton.Bind(wx.EVT_BUTTON, self.onLoadSoundfile)
        row1.Add(loadbutton, 1, wx.ALL|wx.EXPAND, 5)

        playbutton = wx.ToggleButton(panel, -1, "Jouer")
        playbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onPlaySoundfile)
        row1.Add(playbutton, 1, wx.ALL|wx.EXPAND, 5)

        loopbutton = wx.ToggleButton(panel, -1, "Loop")
        loopbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onLoopSoundfile)
        row1.Add(loopbutton, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(row1, 0, wx.EXPAND)

        labelpit = wx.StaticText(panel, -1, "Transposition")
        self.spit = PyoGuiControlSlider(panel, 0.25, 4, 1, log=True, size=(140, 16))
        self.spit.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onSoundfileSpeed)
        sizer.Add(labelpit, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.spit, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        panel.SetSizerAndFit(sizer)
        return panel

    def onLoadSoundfile(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir un fichier son",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_PREVIEW)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if sndinfo(path) is not None:
                self.soundtable.setSound(path)
                self.soundfile.dur = self.soundtable.getDur()

        dlg.Destroy()

    def onPlaySoundfile(self, evt):
        if evt.GetInt():
            self.soundfile.play()
        else:
            self.soundfile.stop()

    def onLoopSoundfile(self, evt):
        self.soundfile.mode = evt.GetInt()

    def onSoundfileSpeed(self, evt):
        self.soundfile.pitch = evt.value

    def createOscillatorPanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        pitbox = wx.BoxSizer(wx.VERTICAL)
        labelpit = wx.StaticText(panel, -1, "Fréquence")
        self.opit = PyoGuiControlSlider(panel, 20, 4000, 250, log=True)
        self.opit.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onOscillatorFreq)
        sizer.Add(labelpit, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.opit, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        row2 = wx.BoxSizer(wx.HORIZONTAL)

        shpbox = wx.BoxSizer(wx.VERTICAL)
        labelshp = wx.StaticText(panel, -1, "Forme d'onde")
        self.oshp = PyoGuiControlSlider(panel, 0, 1, 0, log=False, size=(120, 16))
        self.oshp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onOscillatorShape)
        shpbox.Add(labelshp, 0, wx.LEFT|wx.TOP, 5)
        shpbox.Add(self.oshp, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        brtbox = wx.BoxSizer(wx.VERTICAL)
        labelbrt = wx.StaticText(panel, -1, "Brillance")
        self.obrt = PyoGuiControlSlider(panel, 0, 1, 0.5, log=False, size=(120, 16))
        self.obrt.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onOscillatorBright)
        brtbox.Add(labelbrt, 0, wx.LEFT|wx.TOP, 5)
        brtbox.Add(self.obrt, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        row2.Add(shpbox, 1)
        row2.Add(brtbox, 1)

        sizer.Add(row2, 0, wx.EXPAND)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        panel.SetSizerAndFit(sizer)
        return panel

    def onOscillatorFreq(self, evt):
        self.oscfreq.value = evt.value

    def onOscillatorBright(self, evt):
        self.oscbright.value = evt.value

    def onOscillatorShape(self, evt):
        self.oscshape.value = evt.value

    def createNoisePanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))

        choices = ["Bruit blanc", "Bruit rose", "Bruit brun"]
        ntyp = wx.RadioBox(panel, -1, "", wx.DefaultPosition, wx.DefaultSize,
                           choices, 3, wx.RA_SPECIFY_ROWS | wx.NO_BORDER)
        ntyp.Bind(wx.EVT_RADIOBOX, self.onNoiseType)
        sizer.Add(ntyp, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        panel.SetSizerAndFit(sizer)
        return panel

    def onNoiseType(self, evt):
        sel = evt.GetInt()
        obj = [self.whitenoise, self.pinknoise, self.brownnoise][sel]
        self.noisegenerator.setInput(obj, 0.1)

class ResamplingModule(wx.Panel):
    """
    Module: 01-Échantillonnage
    --------------------------

    Ce module illustre l'effet de l'opération d'échantillonnage sur le
    spectre de fréquence d'un signal. Il est composé d'un signal source
    dont on peut contrôler la fréquence fondamentale et la quantité 
    d'harmoniques, d'un choix de fréquence d'échantillonnage (en division
    de la fréquence d'échantillonnage courante), d'un filtre anti-repliement
    et d'un filtre de reconstruction.

    Contrôles:
        Fréquence fondamentale en Hertz: 
            Fréquence fondamentale du signal original.
        Quantité d'harmoniques: 
            Contrôle la quantité d'harmonique dans le signal original.
        Ré-échantillonnage:
            Choix de la nouvelle fréquence d'échantillonnage.
            "sr" : aucun ré-échantillonnage
            "sr/2" : Moitié de la fréquence d'échantillonnage courante
            "sr/4" : Quart de la fréquence d'échantillonnage courante
            "sr/8" : Huitième de la fréquence d'échantillonnage courante
        Filtre anti-repliement:
            Le filtre utilisé avant échantillonnage pour assurer que le
            signal à échantillonner ne contient pas de composantes au-dessus
            de la fréquence de Nyquist.
            "Aucun" : Auncun filtre n'est appliqué
            "FIR-8" : Fonction pieuvre à 8 points
            "FIR-32" : Fonction pieuvre à 32 points
            "FIR-128" : Fonction pieuvre à 128 points
        Filtre de reconstruction:
            Le filtre utilisé pour reconstruire le signal en éliminant les
            copies (autour des multiples de la fréquence d'échantillonnage)
            provoquées par la multiplication du signal par un train 
            d'impulsions.
            "Aucun" : Auncun filtre n'est appliqué
            "FIR-8" : Fonction pieuvre à 8 points
            "FIR-32" : Fonction pieuvre à 32 points
            "FIR-128" : Fonction pieuvre à 128 points

    """
    name = "01-Échantillonnage"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.factor = -1

        labelfr = wx.StaticText(self, -1, "Fréquence fondamentale en Hz")
        self.fr = PyoGuiControlSlider(self, 20, 5000, 686, log=True,
                                      orient=wx.HORIZONTAL)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelsh = wx.StaticText(self, -1, "Quantité d'harmoniques")
        self.sh = PyoGuiControlSlider(self, 0, 1, 0, log=False,
                                      orient=wx.HORIZONTAL)
        self.sh.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.sh.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSharp)

        downlabel = wx.StaticText(self, -1, "Ré-échantillonnage")
        self.down = wx.Choice(self, -1, choices=["sr", "sr/2", "sr/4", "sr/8"])
        self.down.SetSelection(0)
        self.down.Bind(wx.EVT_CHOICE, self.resample)

        filt1label = wx.StaticText(self, -1, "Filtre anti-repliement")
        f1 = ["Aucun", "FIR-8", "FIR-32", "FIR-128"]
        self.filt1 = wx.Choice(self, -1, choices=f1)
        self.filt1.SetSelection(0)
        self.filt1.Bind(wx.EVT_CHOICE, self.changeFilter1)

        filt2label = wx.StaticText(self, -1, "Filtre de reconstruction")
        f2 = ["Aucun", "FIR-8", "FIR-32", "FIR-128"]
        self.filt2 = wx.Choice(self, -1, choices=f2)
        self.filt2.SetSelection(0)
        self.filt2.Bind(wx.EVT_CHOICE, self.changeFilter2)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelsh, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.sh, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(downlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.down, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(filt1label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.filt1, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(filt2label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.filt2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def changeFreq(self, evt):
        print(self.GetSize())
        self.source.freq = evt.value

    def changeSharp(self, evt):
        self.source.feedback = evt.value * 0.175

    def resample(self, evt):
        self.factor = [-1, -2, -4, -8][evt.GetInt()]
        mode1 = self.downsig.mode
        mode2 = self.output.mode
        self.processing()
        self.source.freq = self.fr.getValue()
        self.source.feedback = self.sh.getValue() * 0.175
        self.downsig.mode = mode1
        self.output.mode = mode2
        wx.GetTopLevelParent(self).connectModuleToOutput()

    def changeFilter1(self, evt):
        order = [1, 8, 32, 128][evt.GetInt()]
        self.downsig.mode = order

    def changeFilter2(self, evt):
        order = [0, 8, 32, 128][evt.GetInt()]
        self.output.mode = order

    def processing(self):
        self.source = SineLoop(freq=686, mul=0.707)
        self.blocked = DCBlock(self.source)
        server = self.source.getServer()
        server.beginResamplingBlock(self.factor)
        self.downsig = Resample(self.blocked, mode=0)
        server.endResamplingBlock()
        self.output = Resample(self.downsig, mode=0)

class QuantizeModule(wx.Panel):
    """
    Module: 01-Quantification
    -------------------------

    Ce module illustre l'impact du nombre de bits de quantification
    utilisés lors de la numérisation d'un signal. En dessous de 8 
    bits, on perçoit clairement l'ajout du bruit de quantification
    au signal original. Le module permet aussi d'ajouter un bruit
    de dispersion (dither) afin de masquer le bruit de quantification
    (autant que possible!) à l'aide d'un bruit moins aggressant à
    l'écoute.

    Contrôles:
        Fréquence fondamentale en Hertz: 
            Fréquence fondamentale du signal original.
        Quantité d'harmoniques: 
            Contrôle la quantité d'harmonique dans le signal original.
        # de bits de quantification:
            Définit le pas de quantification, entre 2 et 16 bits.
        Choisir le signal:
            On peut visualiser (et écouter) le signal dégradé ou le
            bruit de quantification seul.
        Bruit de dispersion:
            Ajout d'un bruit de dispersion. Diverses variantes de bruit 
            sont offertes.

    """
    name = "01-Quantification"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.nbits = 16

        labelfr = wx.StaticText(self, -1, "Fréquence fondamentale en Hz")
        self.fr = PyoGuiControlSlider(self, 20, 5000, 187.5, log=True,
                                      orient=wx.HORIZONTAL)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelsh = wx.StaticText(self, -1, "Quantité d'harmoniques")
        self.sh = PyoGuiControlSlider(self, 0, 1, 0, log=False,
                                      orient=wx.HORIZONTAL)
        self.sh.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.sh.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSharp)

        labelbt = wx.StaticText(self, -1, "# de bits de quantification")
        self.bt = PyoGuiControlSlider(self, 2, 16, 16, log=False, integer=False,
                                      orient=wx.HORIZONTAL)
        self.bt.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.bt.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeBits)

        chooselabel = wx.StaticText(self, -1, "Choisir le signal")
        choices = ["Signal dégradé", "Bruit de quantification"]
        self.choose = wx.Choice(self, -1, choices=choices)
        self.choose.SetSelection(0)
        self.choose.Bind(wx.EVT_CHOICE, self.changeSignal)

        ditherlabel = wx.StaticText(self, -1, "Bruit de dispersion")
        choices = ["Aucun", "Rectangulaire", "Triangulaire", "Gaussien",
                   "Bruit hautes fréquences", "Bruit basses fréquences"]
        self.dither = wx.Choice(self, -1, choices=choices)
        self.dither.SetSelection(0)
        self.dither.Bind(wx.EVT_CHOICE, self.changeDither)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelsh, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.sh, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelbt, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.bt, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(chooselabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.choose, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(ditherlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.dither, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.source.freq = evt.value

    def changeSharp(self, evt):
        self.source.feedback = evt.value * 0.175

    def changeBits(self, evt):
        self.degrade.bitdepth = self.nbits = evt.value
        self.ndither.mul = 1 / (pow(2, self.nbits) / 2) * 0.66

    def changeSignal(self, evt):
        if evt.GetInt() == 0:
            self.output.setInput(self.degrade, 0.1)
        else:
            self.output.setInput(self.qnoise, 0.1)

    def changeDither(self, evt):
        self.ndither.mul = 1 / (pow(2, self.nbits) / 2) * 0.66
        self.ndither.value = self.nsignals[evt.GetInt()]

    def processing(self):
        self.nsignals = [Sig(0), Noise(), ((Noise()+Noise())/2), 
                         ((Noise()+Noise()+Noise()+Noise()+Noise()+Noise())/2),
                         Atone(Noise(), 2500), Tone(Noise(), 2500)]
        self.ndither = Sig(self.nsignals[0], mul=0)
        self.source = SineLoop(freq=187.5)
        self.blocked = DCBlock(self.source)
        self.degrade = Degrade(self.blocked, bitdepth=16, add=self.ndither)
        self.qnoise = self.degrade - self.blocked
        self.output = InputFader(self.degrade)

class FiltersModule(wx.Panel):
    """
    Module: 01-Échantillonnage
    --------------------------


    """
    name = "02-Filtres"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        self.SetSizer(sizer)

    def processing(self):
        self.output = self.inputpanel.output

MODULES = [ResamplingModule, QuantizeModule, FiltersModule]
