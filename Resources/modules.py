import os
import wx
from pyo import *
from .constants import *
from .widgets import HeadTitle
from .bandlimited import DSPDemoBLOsc, SchroederVerb1, SchroederVerb2

class InputPanel(wx.Choicebook):
    def __init__(self, parent):
        wx.Choicebook.__init__(self, parent, -1, size=(300, -1))
        self.SetBackgroundColour(USR_PANEL_BACK_COLOUR)

        # Pulse-Width-Modulation
        sources = [("Oscillateur multiforme", self.createLFOPanel),
                   ("Oscillateur anti-alias", self.createOscillatorPanel),
                   ("Fichier sonore", self.createSoundfilePanel),
                   ("Générateur de bruit", self.createNoisePanel)]
        for source in sources:
            panel = source[1]()
            self.AddPage(panel, source[0])
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)

        ### Audio processing ###
        # Multi-waveforms oscillator
        self.lfofreq = SigTo(250, 0.05)
        self.lfooscil = LFO(freq=self.lfofreq, sharp=0.0, type=7)

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
        self.soundfilemono = self.soundfile.mix()

        # Noise generator
        self.whitenoise = Noise()
        self.pinknoise = PinkNoise()
        self.brownnoise = BrownNoise()
        self.noisegenerator = InputFader(self.whitenoise)

        # Audio output
        self.output = InputFader(self.lfooscil)

    def OnPageChanged(self, evt):
        sel = evt.GetSelection()
        obj = [self.lfooscil, self.oscillator, self.soundfilemono, 
               self.noisegenerator][sel]
        self.output.setInput(obj, 0.1)

    def createLFOPanel(self):
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        choices = ["Sinusoïde", "Rampe", "Dent de scie", "Carrée", 
                   "Triangle", "Impulsion unipolaire", "Impulsion bipolaire"]
        wtyp = wx.Choice(panel, -1, choices=choices)
        wtyp.SetSelection(0)
        wtyp.Bind(wx.EVT_CHOICE, self.onLFOWaveType)
        sizer.Add(wtyp, 0, wx.ALL|wx.EXPAND, 5)

        pitbox = wx.BoxSizer(wx.VERTICAL)
        labelpit = wx.StaticText(panel, -1, "Fréquence")
        self.opit = PyoGuiControlSlider(panel, 20, 4000, 250, log=True)
        self.opit.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.opit.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onLFOFreq)
        sizer.Add(labelpit, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.opit, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, size=(300, 2)))
        sizer.AddSpacer(5)

        panel.SetSizerAndFit(sizer)
        return panel

    def onLFOWaveType(self, evt):
        realtype = [7, 0, 1, 2, 3, 4, 5][evt.GetInt()]
        self.lfooscil.type = realtype
        if realtype == 7:
            self.lfooscil.sharp = 0
        else:
            self.lfooscil.sharp = 1

    def onLFOFreq(self, evt):
        self.lfofreq.value = evt.value

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

class InputOnlyModule(wx.Panel):
    """
    Module: 00-Sources
    ------------------

    Ce module permet d'explorer les différentes sources sonores
    disponibles, sans traitement.

    """
    name = "00-Sources"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        self.SetSizer(sizer)

    def processing(self):
        self.output = self.inputpanel.output
        self.display = self.output

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
        self.display = self.output

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
        self.display = self.output

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
        self.filtfreq.value = evt.value

    def changeQ(self, evt):
        self.filt1Q.value = evt.value / self.factor
        self.filt2Q.value = evt.value

    def changeBoost(self, evt):
        self.filter2.boost = evt.value

    def changeOrder(self, evt):
        stages = evt.GetInt() + 1
        self.factor = rescale(stages, 1, 4, 1, 3)
        self.filter1.stages = stages
        self.filt1Q.value = self.q.getValue() / self.factor

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
        self.filtfreq = SigTo(1000, 0.05)
        self.filt1Q = SigTo(1, 0.05)
        self.filt2Q = SigTo(1, 0.05)
        self.filter1 = Biquadx(self.inputpanel.output, freq=self.filtfreq, 
                               q=self.filt1Q, stages=1)
        self.filter2 = EQ(self.inputpanel.output, freq=self.filtfreq, 
                          q=self.filt2Q, boost=-3.00)
        self.output = Interp(self.filter1, self.filter2, 0)
        self.display = self.output

class FixedDelayModule(wx.Panel):
    """
    Module: 03-Délais-fixes
    -----------------------

    Ce module permet de visualiser l'effet du temps de délai lorsqu'un
    signal original est additionné à une version délayé de lui-même. Les
    effets obtenus sont le filtre passe-bas pour de très courts délais, 
    toute la gamme de filtres en peigne pour des délais se situant entre
    0.1 et 50 ms, et finalement les effets d'échos pour les temps de
    délai plus grand que 50 ms.

    Tois ondes sont affichées dans les fenêtres de visualisation:

    - rouge: signal original
    - vert: signal délayé
    - bleu: addition du signal original et du signal délayé

    Contrôles:
        Temps de délais (ms):
            Permet d'ajuster le temps de délai en millisecondes. La
            valeur correspondante en échantillon est affichée en
            dessous.
        Réinjection en %:
            Permet d'ajuster la proportion du signal de sortie qui
            est réinjecté en entrée du délai (délai récursif). Plus
            la réinjection est grande, plus les pics de résonance 
            sont prononcés.

    """
    name = "03-Délais-fixes"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.sr = Sig(0).getSamplingRate()
        self.one = 1 / self.sr

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labeltm = wx.StaticText(self, -1, "Temps de délai (ms)")
        self.tm = PyoGuiControlSlider(self, self.one*1000, 100, self.one, log=True)
        self.tm.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.tm.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeTime)

        label = "Délai en échantillons: %.2f" % (self.one * self.sr)
        self.tmsample = wx.StaticText(self, -1, label)

        labelfb = wx.StaticText(self, -1, "Réinjection en %")
        self.fb = PyoGuiControlSlider(self, 0, 99, 0, log=False)
        self.fb.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fb.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFeed)

        sizer.Add(labeltm, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.tm, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(self.tmsample, 0, wx.LEFT|wx.TOP|wx.BOTTOM, 5)
        sizer.Add(labelfb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeTime(self, evt):
        self.dtime.value = evt.value * 0.001
        label = "Délai en échantillons: %.2f" % (self.dtime.value * self.sr)
        self.tmsample.SetLabel(label)

    def changeFeed(self, evt):
        self.dfeed.value = evt.value * 0.01

    def processing(self):
        self.dtime = SigTo(self.one, 0.05)
        self.dfeed = SigTo(0, 0.05)
        self.delay = Delay(self.inputpanel.output, self.dtime, self.dfeed)
        self.output = (self.inputpanel.output + self.delay) * 0.5
        self.display = Mix([self.inputpanel.output, self.delay, self.output], voices=3)

class VariableDelayModule(wx.Panel):
    """
    Module: 03-Délais-variables
    ---------------------------

    Ce module met en place une ligne de délai modulée à l'aide d'un
    oscillateur sinusoïdal. Les paramètres de fréquence du LFO, 
    de délai moyen et de profondeur de la modulation peuvent être
    ajustés de façon à créer soit un effet de flanger ou un effet 
    de chorus.

    Valeurs typiques pour un flanger:

    Fréquence du LFO: 0.1 Hz
    Temps de délai moyen: 5 ms
    Profondeur de la modulation: 99%

    Valeurs typiques pour un chorus (varient en fonction de la source):

    Fréquence du LFO: 3 Hz
    Temps de délai moyen: 12 ms
    Profondeur de la modulation: 5%

    Contrôles:
        Fréquence du LFO:
            Fréquence, en Hz, de l'oscillateur modulant le temps de délai.
        Temps de délai moyen (ms):
            Valeur centrale du temps de délai, en ms. Le LFO fait osciller
            le temps de délai autour de cette valeur.
        Profondeur de la modulation (%):
            Profondeur de la modulation autour du temps de délai moyen. À
            0 %, le délai est fixe, à 100 %, le temps délai oscille de 0 ms 
            à la valeur du délai moyen multiplié par 2.
        Réinjection en %:
            Permet d'ajuster la proportion du signal de sortie qui
            est réinjecté en entrée du délai (délai récursif). Plus
            la réinjection est grande, plus les pics de résonance 
            sont prononcés.

    """
    name = "03-Délais-variables"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelpit = wx.StaticText(self, -1, "Fréquence du LFO")
        self.opit = PyoGuiControlSlider(self, 0.01, 20, 0.1, log=True)
        self.opit.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.opit.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.onLFOFreq)

        labeltm = wx.StaticText(self, -1, "Temps de délai moyen (ms)")
        self.tm = PyoGuiControlSlider(self, 2, 100, 5, log=True)
        self.tm.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.tm.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeTime)

        labeldp = wx.StaticText(self, -1, "Profondeur de la modulation (%)")
        self.dp = PyoGuiControlSlider(self, 0, 99.5, 99.5)
        self.dp.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.dp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeDepth)

        labelfb = wx.StaticText(self, -1, "Réinjection en %")
        self.fb = PyoGuiControlSlider(self, 0, 99, 0, log=False)
        self.fb.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fb.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFeed)

        sizer.Add(labelpit, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.opit, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labeltm, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.tm, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labeldp, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.dp, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def onLFOFreq(self, evt):
        self.lfofreq.value = evt.value

    def changeTime(self, evt):
        self.dtime.value = evt.value * 0.001

    def changeDepth(self, evt):
        self.ddepth.value = evt.value * 0.01

    def changeFeed(self, evt):
        self.dfeed.value = evt.value * 0.01

    def processing(self):
        self.lfofreq = SigTo(0.1, 0.05)
        self.lfooscil = Sine(freq=self.lfofreq)
        self.dtime = SigTo(0.005, 0.05)
        self.ddepth = SigTo(0.995, 0.05)
        self.dfeed = SigTo(0, 0.05)
        self.vtime = self.lfooscil * self.dtime * self.ddepth + self.dtime
        self.delay = Delay(self.inputpanel.output, self.vtime, self.dfeed)
        self.output = (self.inputpanel.output + self.delay) * 0.5
        self.display = self.output.mix()

class PhasingModule(wx.Panel):
    """
    Module: 03-Phasing
    ------------------

    Ce module permet d'explorer avec un effet de phasing construit à
    l'aide de 12 filtres passe-tout d'ordre second. La différence
    principale entre le flanger et le phaser est que dans le flanger
    les pics d'amplitude couvre tout le spectre et sont équidistants.
    Dans un phaser, le nombre de pics dans le spectre dépend du nombre
    de filtres utilisés (12 dans ce cas-ci) et la répartition des
    pics dépend de la fréquence centrale de chacun des filtres. 
    L'algorithme utilisé dans ce module consiste en une fréquence de 
    base (celle du premier filtre) et en un facteur d'expansion, à
    partir duquel sont calculées les fréquences centrales de autres
    filtres.

    Contrôles:
        Fréquence de base en Hz:
            Fréquence centrale, en Hz, du premier filtre passe-tout.
        Espacement des filtres:
            Facteur d'expansion des filtres suivants. Les filtres
            successifs ont une fréquence valant la fréquence du filtre
            précédent, multipliée par ce facteur.
        Réinjection en %:
            Permet d'ajuster la proportion du signal de sortie qui
            est réinjecté en entrée du délai (délai récursif). Plus
            la réinjection est grande, plus les pics de résonance 
            sont prononcés.

    """
    name = "03-Phasing"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelfr = wx.StaticText(self, -1, "Fréquence de base en Hz")
        self.fr = PyoGuiControlSlider(self, 40, 1000, 100, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelsp = wx.StaticText(self, -1, "Espacement des filtres")
        self.sp = PyoGuiControlSlider(self, 1.1, 4, 1.3, log=True)
        self.sp.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.sp.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSpread)

        labelfb = wx.StaticText(self, -1, "Réinjection en %")
        self.fb = PyoGuiControlSlider(self, 0, 99, 50, log=False)
        self.fb.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fb.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFeed)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelsp, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.sp, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.freq.value = evt.value

    def changeSpread(self, evt):
        self.spread.value = evt.value

    def changeFeed(self, evt):
        self.dfeed.value = evt.value * 0.01

    def processing(self):
        self.amp = Fader(fadein=1, mul=0.3).play()
        self.freq = SigTo(100, 0.05)
        self.spread = SigTo(1.3, 0.05)
        self.dfeed = SigTo(0.5, 0.05)
        self.output = Phaser(self.inputpanel.output, freq=self.freq, 
                             spread=self.spread, q=1, 
                             feedback=self.dfeed, num=12, mul=self.amp)
        self.display = self.output.mix()

class TransposeModule(wx.Panel):
    """
    Module: 03-Transposition
    ------------------------

    Ce module illustre le transposition dans le domaine temporel
    à l'aide de deux lignes de délai supperposées dont les temps 
    de délai varient linéairement afin de produire une transposition 
    constante. La vitesse de déplacement du pointeur de lecture est
    calculée en fonction de la transposition désirée, en demi-tons.

    Contrôles:
        Transposition en demi-tons:
            Permet d'ajuster le degré de transposition appliqué à
            la source.
        Réinjection en %:
            Permet d'ajuster la proportion du signal de sortie qui
            est réinjecté en entrée du délai (délai récursif). Cela
            a pour effet de transposer le signal transposer, en boucle.
        Balance original/transposé:
            Balance entre le signal original et le signal transposé.
            0 = signal original, 1 = signal transposé, 0.5 = mélange
            des deux.

    """
    name = "03-Transposition"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labeltr = wx.StaticText(self, -1, "Transposition en demi-tons")
        self.tr = PyoGuiControlSlider(self, -24, 12, -7, log=False)
        self.tr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.tr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeTranspo)

        labelfb = wx.StaticText(self, -1, "Réinjection en %")
        self.fb = PyoGuiControlSlider(self, 0, 99, 0, log=False)
        self.fb.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fb.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFeed)

        labelbl = wx.StaticText(self, -1, "Balance original/transposé")
        self.bl = PyoGuiControlSlider(self, 0, 1, 0.5, log=False)
        self.bl.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.bl.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeBalance)

        sizer.Add(labeltr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.tr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelbl, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.bl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeTranspo(self, evt):
        self.transpo.value = evt.value

    def changeFeed(self, evt):
        self.feed.value = evt.value * 0.01

    def changeBalance(self, evt):
        self.bal.value = evt.value

    def processing(self):
        self.amp = Fader(fadein=1).play()
        self.transpo = SigTo(-7, 0.05)
        self.feed = SigTo(0, 0.05)
        self.bal = SigTo(0.5, 0.05)
        self.harmon = Harmonizer(self.inputpanel.output, self.transpo, self.feed)
        self.output = Interp(self.inputpanel.output, self.harmon, self.bal,
                             mul=self.amp)
        self.display = self.output

class ReverbModule(wx.Panel):
    """
    Module: 03-Réverbération
    ------------------------

    Ce module présente, à des fins de comparaison, divers algorithmes
    de réverbération numérique. Les choix sont:

    Réverbérateur de Schroeder, modèle 1:
        Algorithme utilsant quatre filtres en peigne en parallèle dont
        la somme est passée dans deux filtres passe-tout en série.
    Réverbérateur de Schroeder, modèle 2:
        Algorithme utilsant quatre filtres passe-tout en série. Le signal
        de chacun des filtres est ensuite passé dans un filtre passe-bas 
        et la somme des signaux de sortie des filtres passe-bas constitue 
        le signal réverbéré.
    Freeverb:
        Cet algorithme est une extension du modèle numéro 1 de Schroeder,
        dévelopé par Jezar à "dreampoint" (http://www.dreampoint.co.uk).
        Comme cet algorithme est du domaine public et très économe en
        temps de calcul, on le retrouve très fréquemment dans le domaine
        du logiciel libre.
    Réseau de délais récursifs (FDN - Feedback Delai Network):
        Ce réverbérateur numérique est constituté d'une matrice de huit
        filtres en peigne, en couplage croisé afin d'atténuer l'effet de
        coloration du filtre en peigne. Cet algorithme est un des plus
        efficace pour mettre en place des temps de réverbération très longs.
    Réverbe par convolution:
        Le choix par excellence pour obtenir une réverbération naturelle.
        Le signal est ici convolué avec la réponse impulsionnelle d'un lieu
        réel. Le hic, ça coûte très cher en CPU!

    Contrôles:
        Type de réverbération:
            Menu déroulant permettant de choisir un algorithme de 
            réverbération.
        Taille de la pièce:
            Grandeur de la pièce virtuelle. En quelque sorte, ce 
            paramètre permet de contrôler la profondeur de la 
            réverbération. 0 = petit espace, 1 = grand espace.
        Atténuation hautes fréquences:
            Vitesse à laquelle les hautes fréquences sont absorbées
            par les murs, matériaux, obstacles, etc.
            0 = peu d'atténuation, 1 = beaucoup d'atténuation.
        Balance original/transposé:
            Balance entre le signal original et le signal transposé.
            0 = signal original, 1 = signal transposé, 0.5 = mélange
            des deux.

    """
    name = "03-Réverbération"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        typelabel = wx.StaticText(self, -1, "Type de réverbération")
        choices = ["Schroeder modèle 1", "Schroeder modèle 2", 
              "Freeverb", "Réseau de délais récursifs",
              "Réverbe par convolution"]
        type = wx.Choice(self, -1, choices=choices)
        type.SetSelection(0)
        type.Bind(wx.EVT_CHOICE, self.changeReverbType)

        labelrz = wx.StaticText(self, -1, "Taille de la pièce")
        self.rz = PyoGuiControlSlider(self, 0, 1, 0.5, log=False)
        self.rz.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.rz.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeRoomSize)

        labelfb = wx.StaticText(self, -1, "Atténuation hautes fréquences")
        self.fb = PyoGuiControlSlider(self, 0, 1, 0.5, log=False)
        self.fb.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fb.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeDamping)

        labelbl = wx.StaticText(self, -1, "Balance original/réverbéré")
        self.bl = PyoGuiControlSlider(self, 0, 1, 0.25, log=False)
        self.bl.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.bl.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeBalance)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelrz, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.rz, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelbl, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.bl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeReverbType(self, evt):
        if evt.GetInt() == 4:
            self.rev5.play()
            self.rz.disable()
            self.fb.disable()
        else:
            self.rev5.stop()
            self.rz.enable()
            self.fb.enable()
        choices = [self.rev1.output, self.rev2.output,
                   self.rev3, self.rev4, self.rev5]
        self.reverb.setInput(choices[evt.GetInt()])

    def changeRoomSize(self, evt):
        self.size.value = evt.value

    def changeDamping(self, evt):
        self.damp.value = evt.value

    def changeBalance(self, evt):
        self.bal.value = evt.value

    def processing(self):
        self.size = SigTo(0.5, 0.05)
        self.damp = SigTo(0.5, 0.05)
        self.bal = SigTo(0.25, 0.05)
        self.rev1 = SchroederVerb1(self.inputpanel.output, self.size, self.damp)
        self.rev2 = SchroederVerb2(self.inputpanel.output, self.size, self.damp)
        self.rev3 = Freeverb(self.inputpanel.output, [self.size, self.size*0.99], 
                             [self.damp*0.99, self.damp], 1)
        self.r4damp = Scale(self.damp, outmin=10000, outmax=500)
        self.rev4 = WGVerb(self.inputpanel.output, [self.size, self.size*0.99], 
                           [self.r4damp*0.99, self.r4damp], 1)
        self.rev5 = CvlVerb(self.inputpanel.output, bal=1).stop()
        self.reverb = InputFader(self.rev1.output)
        self.output = Interp(self.inputpanel.output, self.reverb, self.bal)
        self.display = self.output

class PanningModule(wx.Panel):
    """
    Module: 04-Panoramisation
    -------------------------

    Ce module permet de comparer trois différents algorithmes de
    panoramisation. 

    - Linéaire:
        Le moins coûteux en temps de calcul, l'intensité totale
        est réduite de 6 dB au centre par rapport aux extrémités.
    - Sinus/cosinus:
        Le gain pour chaque haut-parleur est calculé à partir de
        fonction cosinus (pour le canal de gauche) et sinus (pour
        le canal de droite). L'intensité totale est toujours de
        1, peu importe la position de la source. Cet algorithme
        est plus coûteux en temps de calcul.
    - Racine carrée:
        Cet algorithme est un compromis entre les deux précédents
        en ce qui a trait au temps de calcul (plus coûteux que
        la panoramisation linéaire mais moins que sinus/cosinus)
        tout en conservant une intensité totale de 1 sur tout 
        l'arc de panoramisation. Par contre, la courbe est un peu
        abrupte aux extrémités (proche de 0 ou de 1).

    Contrôles:
        Algorithme de panoramisation:
            Permet de choisir l'algorithme de panoramisation.
        Pan gauche - droite:
            Position du signal sur l'axe gauche - droite.
            0 = complètement à gauche, 1 = complètement à droite.

    """
    name = "04-Panoramisation"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        typelabel = wx.StaticText(self, -1, "Algorithme de panoramisation")
        choices = ["Linéaire", "Sinus/cosinus", "Racine carrée"]
        type = wx.Choice(self, -1, choices=choices)
        type.SetSelection(0)
        type.Bind(wx.EVT_CHOICE, self.changePanType)

        labelpn = wx.StaticText(self, -1, "Pan gauche - droite")
        self.pn = PyoGuiControlSlider(self, 0, 1, 0.5, log=False)
        self.pn.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.pn.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changePan)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelpn, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.pn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changePanType(self, evt):
        choices = [self.pan1, self.pan2, self.pan3]
        self.output.setInput(choices[evt.GetInt()])

    def changePan(self, evt):
        self.pan.value = evt.value

    def processing(self):
        self.pan = SigTo(0.5, 0.05)
        self.pan1 = Sig(self.inputpanel.output, mul=[1 - self.pan, self.pan])
        self.pan2 = Pan(self.inputpanel.output, pan=self.pan)
        self.pan3 = Sig(self.inputpanel.output, 
                        mul=[Sqrt(1 - self.pan), Sqrt(self.pan)])
        self.output = InputFader(self.pan1)
        self.display = self.output

class HRTFModule(wx.Panel):
    """
    Module: 04-HRTF Spatialisation 3D
    ---------------------------------

    Ce module permet d'expérimenter avec la panoramisation 3D en
    stéréo avec l'algorithme HRTF (Head-Related Transfert Function).
    Les réponses impulsionnelles proviennent de Gardner et Martin
    du MIT Media Lab:

    http://alumni.media.mit.edu/~kdm/hrtfdoc/hrtfdoc.html

    On contrôle la position de la source est spécifiant ses 
    coordonnées en azimuth et en élévation.

    Cet algorithme utilise une banque de filtres pré-enregistrés
    pour simuler les effets spectraux de la tête, des oreilles et
    des épaules sur la perception du son. Observez, avec un bruit
    blanc par exemple, comme le spectre de la source change lorsque
    la position change. Pour entendre l'effet HRTF, il est préférable
    d'en faire l'écoute aux écouteurs!

    Contrôles:
        Position en azimuth:
            Contrôle la position de la source en azimuth (plan 
            horizontal). La position est donnée en degrés, entre
            -180 et 180 degrés. -90 signifie que le son est 
            complètement à gauche et à 90 degrés, le son est
            complètement à droite.
        Position en élévation:
            Contrôle la position de la source en élévation (plan 
            vertical). La position est donnée en degrés, entre
            -40 et 90 degrés. 0 degrés signifie que le son est
            au niveau des oreilles et à 90 degrés, le son est
            au dessus de la tête.

    """
    name = "04-HRTF Spatialisation 3D"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelaz = wx.StaticText(self, -1, "Position en azimuth")
        self.az = PyoGuiControlSlider(self, -180, 180, 0.0, log=False)
        self.az.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.az.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeAzimuth)

        labelel = wx.StaticText(self, -1, "Position en élévation")
        self.el = PyoGuiControlSlider(self, -40, 90, 0.0, log=False)
        self.el.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.el.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeElevation)

        sizer.Add(labelaz, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.az, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.el, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeAzimuth(self, evt):
        self.azimuth.value = evt.value

    def changeElevation(self, evt):
        self.elevation.value = evt.value

    def processing(self):
        self.hrtfdata = HRTFData(os.path.join(RESOURCES_PATH, "hrtf_compact"))
        self.azimuth = SigTo(0.0, 0.05)
        self.elevation = SigTo(0.0, 0.05)
        self.output = HRTF(self.inputpanel.output, self.azimuth, self.elevation,
                           self.hrtfdata)
        self.display = self.output

MODULES = [InputOnlyModule, ResamplingModule, QuantizeModule, FiltersModule,
           FixedDelayModule, VariableDelayModule, PhasingModule, TransposeModule,
           ReverbModule, PanningModule, HRTFModule]
