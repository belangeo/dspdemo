import wx
from pyo import *
from .constants import *
from .widgets import HeadTitle
from .bandlimited import DSPDemoBLOsc

class InputPanel(wx.Choicebook):
    def __init__(self, parent):
        wx.Choicebook.__init__(self, parent, -1, size=(300, -1))
        self.SetBackgroundColour(USR_PANEL_BACK_COLOUR)

        # Oscillateur auto-modulant, Pulse-Width-Modulation
        sources = [("Oscillateur anti-alias", self.createOscillatorPanel),
                   ("Fichier sonore", self.createSoundfilePanel),
                   ("Générateur de bruit", self.createNoisePanel)]
        for source in sources:
            panel = source[1]()
            self.AddPage(panel, source[0])
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)

        ### Audio processing ###
        # Band-limited oscillator 
        self.oscfreq = SigTo(250, 0.05)
        self.oscbright = SigTo(0.5, 0.05)
        self.oscshape = SigTo(0.25, 0.05)
        self.oscillator = DSPDemoBLOsc(freq=self.oscfreq, bright=self.oscbright,
                                       shape=self.oscshape)

        # Soundfile player
        self.soundtable = SndTable(initchnls=2)
        self.soundfile = TableRead(self.soundtable, freq=1, loop=0, interp=4)
        self.soundcall = TrigFunc(self.soundfile["trig"][0], self.onSoundfileEnd)

        # Noise generator
        self.whitenoise = Noise()
        self.pinknoise = PinkNoise()
        self.brownnoise = BrownNoise()
        self.noisegenerator = InputFader(self.whitenoise)

        # Audio output
        self.output = InputFader(self.oscillator)

    def OnPageChanged(self, evt):
        sel = evt.GetSelection()
        obj = [self.oscillator, self.soundfile, self.noisegenerator][sel]
        self.output.setInput(obj, 0.1)

    def createOscillatorPanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        pitbox = wx.BoxSizer(wx.VERTICAL)
        labelpit = wx.StaticText(panel, -1, "Fréquence")
        self.opit = PyoGuiControlSlider(panel, 20, 4000, 250, log=True)
        self.opit.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.opit.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onOscillatorFreq)
        sizer.Add(labelpit, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.opit, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        row2 = wx.BoxSizer(wx.HORIZONTAL)

        shpbox = wx.BoxSizer(wx.VERTICAL)
        labelshp = wx.StaticText(panel, -1, "Forme d'onde")
        self.oshp = PyoGuiControlSlider(panel, 0, 1, 0.25, size=(120, 16))
        self.oshp.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.oshp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onOscillatorShape)
        shpbox.Add(labelshp, 0, wx.LEFT|wx.TOP, 5)
        shpbox.Add(self.oshp, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        brtbox = wx.BoxSizer(wx.VERTICAL)
        labelbrt = wx.StaticText(panel, -1, "Brillance")
        self.obrt = PyoGuiControlSlider(panel, 0, 1, 0.5, size=(120, 16))
        self.obrt.setBackgroundColour(USR_PANEL_BACK_COLOUR)
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

        self.playbutton = wx.ToggleButton(panel, -1, "Jouer")
        self.playbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onPlaySoundfile)
        row1.Add(self.playbutton, 1, wx.ALL|wx.EXPAND, 5)

        loopbutton = wx.ToggleButton(panel, -1, "Loop")
        loopbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onLoopSoundfile)
        row1.Add(loopbutton, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(row1, 0, wx.EXPAND)

        labelpit = wx.StaticText(panel, -1, "Vitesse de lecture")
        self.spit = PyoGuiControlSlider(panel, 0.25, 4, 1, log=True)
        self.spit.setBackgroundColour(USR_PANEL_BACK_COLOUR)
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
                self.soundfile.freq = self.soundtable.getRate()

        dlg.Destroy()

    def onPlaySoundfile(self, evt):
        if evt.GetInt():
            self.soundfile.play()
        else:
            self.soundfile.stop()

    def onSoundfileEnd(self):
        if not self.soundfile.loop:
            self.playbutton.SetValue(False)

    def onLoopSoundfile(self, evt):
        self.soundfile.loop = evt.GetInt()

    def onSoundfileSpeed(self, evt):
        self.soundfile.freq = self.soundtable.getRate() * evt.value

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

    Ce module illustre l'effet de l'opération d'échantillonnage sur 
    le spectre de fréquence d'un signal. Il est composé d'un choix 
    de fréquences d'échantillonnage (en division de la fréquence 
    d'échantillonnage courante), d'un filtre anti-repliement 
    (appliqué avant le ré-échantillonnage afin de contrôler le
    repliement de spectre) et d'un filtre de reconstruction 
    (appliqué avant la reconstruction du signal afin d'éliminer
    les copies du spectre d'origine apparues lors de la numérisation
    du signal).

    Contrôles:
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

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

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

        sizer.Add(downlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.down, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(filt1label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.filt1, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(filt2label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.filt2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        self.SetSizer(sizer)

    def resample(self, evt):
        self.factor = [-1, -2, -4, -8][evt.GetInt()]
        mode1 = self.downsig.mode
        mode2 = self.output.mode
        self.processing()
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
        self.blocked = DCBlock(self.inputpanel.output)
        server = self.blocked.getServer()
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

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelbt = wx.StaticText(self, -1, "# de bits de quantification")
        self.bt = PyoGuiControlSlider(self, 2, 16, 16, log=False)
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

        sizer.Add(labelbt, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.bt, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(chooselabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.choose, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(ditherlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.dither, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        self.SetSizer(sizer)

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
        self.blocked = DCBlock(self.inputpanel.output)
        self.degrade = Degrade(self.blocked, bitdepth=16, add=self.ndither)
        self.qnoise = self.degrade - self.blocked
        self.output = InputFader(self.degrade)

class FiltersModule(wx.Panel):
    """
    Module: 01-Filtrage
    -------------------

    Ce module permet de comparer l'effet des principaux filtres sur 
    le signal audio. En plus du choix du filtre, des contrôles sont 
    offerts pour la fréquence de coupure (ou centrale), le facteur 
    de qualité (Q du filtre), le gain des filtres d'égalisation et
    l'ordre des filtres de base (passe-bas, passe-haut, passe-bande
    et réjecteur de bande).

    Contrôles:
        Type de filtre:
            Permet de sélectionner le type de filtre parmi le choix
            suivant: passe-bas, passe-haut, passe-bande, réjecteur de 
            bande, crête/creux, dégradé passe-bas et dégradé passe-haut.
        Fréquence de coupure/centrale:
            Fréquence de coupure (ou centrale) du filtre en Hertz.
        Facteur de qualité:
            Facteur de qualité (Q) du filtre, définit comme étant
            le rapport de la fréquence centrale sur la largeur de
            bande (Q = f / bw).
        Augmentation/réduction (dB):
            Le contrôle de gain, en dB, pour les filtres d'égalisation
            (crête/creux et dégradé).
        Ordre du filtre:
            L'ordre des filtres passe-bas, passe-haut, passe-bande et 
            réjecteur de bande. L'ordre correspond au plus grand nombre 
            d'échantillons passés utilisés par le filtre. Plus l'ordre 
            est grand, plus le filtre peut de produire des bandes de 
            transition abruptes.

    """
    name = "02-Filtrage"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.factor = 1

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        chooselabel = wx.StaticText(self, -1, "Type de filtre")
        choices = ["Passe-bas", "Passe-haut", "Passe-bande", 
                   "Réjecteur de bande", "Crête/Creux (peak/notch)",
                   "Dégradé passe-bas", "Dégradé passe-haut"]
        self.choose = wx.Choice(self, -1, choices=choices)
        self.choose.SetSelection(0)
        self.choose.Bind(wx.EVT_CHOICE, self.changeFilter)

        labelfr = wx.StaticText(self, -1, "Fréquence de coupure/centrale")
        self.fr = PyoGuiControlSlider(self, 50, 15000, 1000, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelq = wx.StaticText(self, -1, "Facteur de qualité")
        self.q = PyoGuiControlSlider(self, 0.5, 10, 1, log=True)
        self.q.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.q.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeQ)

        labelbo = wx.StaticText(self, -1, "Augmentation/réduction (dB)")
        self.bo = PyoGuiControlSlider(self, -48, 12, -6)
        self.bo.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.bo.disable()
        self.bo.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeBoost)

        orderlabel = wx.StaticText(self, -1, "Ordre du filtre")
        choices = ["2", "4", "6", "8"]
        self.order = wx.Choice(self, -1, choices=choices)
        self.order.SetSelection(0)
        self.order.Bind(wx.EVT_CHOICE, self.changeOrder)

        sizer.Add(chooselabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.choose, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelq, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.q, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelbo, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.bo, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(orderlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.order, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.filter1.freq = evt.value
        self.filter2.freq = evt.value

    def changeQ(self, evt):
        self.filter1.q = evt.value / self.factor
        self.filter2.q = evt.value

    def changeBoost(self, evt):
        self.filter2.boost = evt.value

    def changeOrder(self, evt):
        stages = evt.GetInt() + 1
        self.factor = rescale(stages, 1, 4, 1, 3)
        self.filter1.stages = stages
        self.filter1.q = self.q.getValue() / self.factor

    def changeFilter(self, evt):
        which = evt.GetInt()
        if which <= 3:
            self.filter1.type = which
            self.output.interp = 0
            self.bo.disable()
            self.order.Enable(True)
        else:
            self.filter2.type = which - 4
            self.output.interp = 1
            self.bo.enable()
            self.order.Enable(False)

    def processing(self):
        self.filter1 = Biquadx(self.inputpanel.output, freq=1000, q=1, stages=1)
        self.filter2 = EQ(self.inputpanel.output, freq=1000, q=1, boost=-3.00)
        self.output = Interp(self.filter1, self.filter2, 0)

MODULES = [ResamplingModule, QuantizeModule, FiltersModule]
