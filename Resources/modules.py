import os
import math
import wx
from pyo64 import *
from pyo.lib._wxwidgets import DataMultiSlider
from .constants import *
from .widgets import HeadTitle, LabelKnob
from .bandlimited import DSPDemoBLOsc, SchroederVerb1, SchroederVerb2, AdditiveSynthesis, TriTable, PWM, OscSync

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
        self.lfofreq = SigTo(172, 0.05)
        self.lfooscil = LFO(freq=self.lfofreq, sharp=0.0, type=7)

        # Band-limited oscillator
        self.oscfreq = SigTo(172, 0.05)
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
        self.opit = PyoGuiControlSlider(panel, 20, 4000, 172, log=True)
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
        self.opit = PyoGuiControlSlider(panel, 20, 4000, 172, log=True)
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
        impulse = os.path.join(RESOURCES_PATH, "IRMediumHallStereo.wav")
        self.rev5 = CvlVerb(self.inputpanel.output, impulse=impulse, bal=1).stop()
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

class BinauralModule(wx.Panel):
    """
    Module: 04-Binaural Spatialisation 3D
    -------------------------------------

    Ce module permet d'expérimenter avec la panoramisation 3D en
    stéréo à l'aide des algorithmes VBAP (Vector-Based Amplitude
    Panning), pour les déplacements de la source, et HRTF 
    (Head-Related Transfert Function), pour la simulation du 
    filtrage causé par les oreilles, la tête, les épaules, etc.
    Les réponses impulsionnelles proviennent de Gardner et Martin
    du MIT Media Lab:

    http://alumni.media.mit.edu/~kdm/hrtfdoc/hrtfdoc.html

    On contrôle la position de la source est spécifiant ses
    coordonnées en azimuth et en élévation.

    Pour bien entendre l'effet Binaural des filtres HRTF, il est
    préférable d'en faire l'écoute aux écouteurs!

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
            0 et 90 degrés. 0 degrés signifie que le son est
            au niveau des oreilles et à 90 degrés, le son est
            au dessus de la tête.

    """
    name = "04-Binaural Spatialisation 3D"
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
        self.el = PyoGuiControlSlider(self, 0, 90, 0.0, log=False)
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
        self.azimuth = SigTo(0.0, 0.05)
        self.elevation = SigTo(0.0, 0.05)
        self.output = Binaural(self.inputpanel.output, self.azimuth, self.elevation)
        self.display = self.output

class PeakRMSModule(wx.Panel):
    """
    Module: 05-Valeur crête vs RMS
    ------------------------------

    Ce module illustre la différence entre la valeur crête (peak)
    et la valeur efficace (RMS).

    L'oscilloscope affiche le signal en rouge ainsi que ses valeurs
    crête et RMS en vert et bleu respectivement.

    """
    name = "05-Valeur crête vs RMS"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        label1 = wx.StaticText(self, -1, "Signal source en rouge.")
        self.label2 = wx.StaticText(self, -1, "Valeur crête en vert. 0.000")
        self.label3 = wx.StaticText(self, -1, "Valeur RMS en bleu. 0.000")

        sizer.Add(label1, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.label2, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.label3, 0, wx.LEFT|wx.TOP, 5)

        self.SetSizer(sizer)

    def getPeakValues(self, *args):
        wx.CallAfter(self.label2.SetLabel, "Valeur crête en vert. %.3f" % args[0])

    def getRMSValues(self, *args):
        wx.CallAfter(self.label3.SetLabel, "Valeur RMS en bleu. %.3f" % args[0])

    def processing(self):
        server = Sig(0).getServer()
        dur = server.getBufferSize() / server.getSamplingRate()
        self.peak = PeakAmp(self.inputpanel.output, self.getPeakValues)
        self.rms = RMS(self.inputpanel.output, self.getRMSValues)
        self.output = self.inputpanel.output
        self.disp = [self.output, SigTo(self.peak, dur), SigTo(self.rms, dur)]
        self.display = Mix(self.disp, voices=3)

class EnvFollowerModule(wx.Panel):
    """
    Module: 05-Suivi d'enveloppe
    ----------------------------

    Ce module illustre le suivi d'enveloppe d'amplitude. La source
    est d'abord analysée puis son suivi d'amplitude est utilisé pour
    contrôler l'amplitude d'un bruit rose en accompagnement.

    Le suivi d'enveloppe est effectué à l'aide d'une rectification
    positive de l'onde puis d'un filtrage passe-bas. La fréquence
    du filtre passe-bas permet de contrôler la réactivité du suiveur.

    Contrôles:
        Fréq. du filtre passe-bas en Hz:
            Contrôle la fréquence du filtre appliqué au signal rectifié.
            Plus la fréquence est grave, plus le lissage est prononcé
            et moins les petites variations d'amplitude seront perceptibles.

    """
    name = "05-Suivi d'enveloppe"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelfr = wx.StaticText(self, -1, "Fréq. du filtre passe-bas en Hz")
        self.fr = PyoGuiControlSlider(self, 0.1, 100, 10.0, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.freq.value = evt.value

    def processing(self):
        self.freq = SigTo(10, 0.05)
        self.amp = Follower(self.inputpanel.output, self.freq)
        self.new = PinkNoise(self.amp)
        self.output = Mix([self.inputpanel.output, self.new], voices=2)
        self.display = self.output

class GateModule(wx.Panel):
    """
    Module: 05-Porte de bruit
    -------------------------

    Ce module permet d'expérimenter avec la porte de bruit.

    Lorsque le suivi d'amplitude du signal passe sous le seuil spécifé,
    l'amplitude descend à zéro à une vitesse donnée par le temps de
    relâche. Lorsqu'il remonte au-dessus du seuil, l'amplitude retourne
    à 1 à une vitesse donnée par le temps d'attaque.

    Contrôles:
        Seuil en dB:
            Seuil, en décibels, au-dessous duquel l'amplitude du signal
            est brsquement rammenée à 0.
        Temps d'attaque en seconde:
            Durée, en seconde, que prend l'amplitude pour retourner à
            1 lorsque le suivi d'amplitude passe au-dessus du seuil.
        Temps de relâche en seconde:
            Durée, en seconde, que prend l'amplitude pour descendre à
            0 lorsque le suivi d'amplitude passe en dessous du seuil.

    """
    name = "05-Porte de bruit"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelth = wx.StaticText(self, -1, "Seuil en dB")
        self.th = PyoGuiControlSlider(self, -70, 0, -50.0)
        self.th.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.th.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeThresh)

        labelri = wx.StaticText(self, -1, "Temps d'attaque en seconde")
        self.ri = PyoGuiControlSlider(self, 0.0001, 0.25, 0.01, log=True)
        self.ri.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ri.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeRise)

        labelfa = wx.StaticText(self, -1, "Temps de relâche en seconde")
        self.fa = PyoGuiControlSlider(self, 0.0001, 0.25, 0.05, log=True)
        self.fa.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fa.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFall)

        sizer.Add(labelth, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.th, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelri, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ri, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfa, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fa, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeThresh(self, evt):
        self.thresh.value = evt.value

    def changeRise(self, evt):
        self.rise.value = evt.value

    def changeFall(self, evt):
        self.fall.value = evt.value

    def processing(self):
        self.thresh = SigTo(-50, 0.05)
        self.rise = SigTo(0.01, 0.05)
        self.fall = SigTo(0.05, 0.05)
        self.output = Gate(self.inputpanel.output, self.thresh, self.rise,
                           self.fall)
        self.display = self.output

class CompressModule(wx.Panel):
    """
    Module: 05-Compresseur
    -----------------------

    Ce module permet d'expérimenter avec le compresseur.

    Lorsque le suivi d'amplitude du signal passe au-dessus du seuil spécifé,
    le signal est compressé en fonction du ratio de compression. Lorsque le
    suivi d'amplitude est sous le seuil, le signal passe sans modification.

    Avec un seuil près de 0 dB et un ratio très élevé (entre 50 et 100), le
    compresseur agit comme un limiteur.

    Contrôles:
        Seuil en dB:
            Seuil, en décibels, au-dessus duquel le signal est compressé.
        Ratio de compression:
            Rapport entre le gain du signal en entré et en sortie du
            compresseur. Un ratio de 2 signifie que pour 2 décibels
            au-dessus du seuil en entrée, l'amplitude du signal en sortie
            sera de seulement 1 décibel au-dessus du seuil.
        Temps d'attaque en seconde:
            Durée, en seconde, que prend le compresseur pour atteindre son
            plein niveau de compression lorsque le suivi d'amplitude passe
            au-dessus du seuil.
        Temps de relâche en seconde:
            Durée, en seconde, que prend le compresseur pour arrêter de
            compresser lorsque le suivi d'amplitude passe au-dessous du
            seuil.

    """
    name = "05-Compresseur"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelth = wx.StaticText(self, -1, "Seuil en dB")
        self.th = PyoGuiControlSlider(self, -70, 0, -50.0)
        self.th.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.th.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeThresh)

        labelrt = wx.StaticText(self, -1, "Ratio de compression")
        self.rt = PyoGuiControlSlider(self, 1, 100, 4, log=True)
        self.rt.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.rt.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeRatio)

        labelri = wx.StaticText(self, -1, "Temps d'attaque en seconde")
        self.ri = PyoGuiControlSlider(self, 0.0001, 0.25, 0.01, log=True)
        self.ri.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ri.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeRise)

        labelfa = wx.StaticText(self, -1, "Temps de relâche en seconde")
        self.fa = PyoGuiControlSlider(self, 0.0001, 0.25, 0.05, log=True)
        self.fa.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fa.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFall)

        labelga = wx.StaticText(self, -1, "Gain post-compresseur")
        self.ga = PyoGuiControlSlider(self, 0, 24, 0)
        self.ga.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ga.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)

        sizer.Add(labelth, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.th, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelrt, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.rt, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelri, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ri, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfa, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fa, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelga, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ga, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeThresh(self, evt):
        self.thresh.value = evt.value

    def changeRatio(self, evt):
        self.ratio.value = evt.value

    def changeRise(self, evt):
        self.rise.value = evt.value

    def changeFall(self, evt):
        self.fall.value = evt.value

    def changeGain(self, evt):
        self.gain.value = evt.value

    def processing(self):
        self.thresh = SigTo(-50, 0.05)
        self.ratio = SigTo(4, 0.05)
        self.rise = SigTo(0.01, 0.05)
        self.fall = SigTo(0.05, 0.05)
        self.gain = SigTo(0, 0.05)
        self.output = Compress(self.inputpanel.output, self.thresh, self.ratio,
                               self.rise, self.fall, mul=DBToA(self.gain))
        self.display = self.output

# Not used yet.
class MBCompressModule(wx.Panel):
    """
    Module: 05-Compresseur Multi-Bande
    ----------------------------------

    Ce module permet d'expérimenter avec la compression multi-bande.

    Pour chacune des quatre bandes de fréquence, lorsque le suivi d'amplitude
    du signal passe au-dessus du seuil spécifé, le signal est compressé en 
    fonction du ratio de compression. Lorsque le suivi d'amplitude est sous 
    le seuil, le signal passe sans modification.

    La plage de fréquence des quatre bandes est:

        basse: 0 - 150 Hz
        mid-basse: 150 - 600 Hz
        mid-haute: 600 - 3200 Hz
        haute: 3200 Hz et plus

    Avec un seuil près de 0 dB et un ratio très élevé (entre 50 et 100), un
    compresseur agit comme un limiteur.

    Contrôles:
        Seuil en dB:
            Seuil, en décibels, au-dessus duquel le signal est compressé.
        Ratio de compression:
            Rapport entre le gain du signal en entré et en sortie du
            compresseur. Un ratio de 2 signifie que pour 2 décibels
            au-dessus du seuil en entrée, l'amplitude du signal en sortie
            sera de seulement 1 décibel au-dessus du seuil.
        Temps d'attaque en seconde:
            Durée, en seconde, que prend le compresseur pour atteindre son
            plein niveau de compression lorsque le suivi d'amplitude passe
            au-dessus du seuil.
        Temps de relâche en seconde:
            Durée, en seconde, que prend le compresseur pour arrêter de
            compresser lorsque le suivi d'amplitude passe au-dessous du
            seuil.

    """
    name = "05-Compresseur Multi-Bande"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.th2 = LabelKnob(self, "seuil", mini=-40, maxi=0, init=-20)
        self.rt2 = LabelKnob(self, "ratio", mini=1, maxi=20, init=1)
        self.ri2 = LabelKnob(self, "rise", mini=0.001, maxi=0.2, init=0.01)
        self.fa2 = LabelKnob(self, "fall", mini=0.005, maxi=0.5, init=0.1)
        self.bo2 = LabelKnob(self, "gain", mini=-24, maxi=24, init=0)
        box2.AddMany([(self.th2, 1), (self.rt2, 1), (self.ri2, 1), (self.fa2, 1), (self.bo2, 1)])

        sizer.Add(box2, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def changeThresh1(self, evt):
        self.thresh1.value = evt.value

    def changeRatio1(self, evt):
        self.ratio1.value = evt.value

    def changeBoost1(self, evt):
        self.boost1.value = evt.value

    def processing(self):
        self.split = FourBand(self.inputpanel.output, freq1=150, freq2=600, freq3=3200)
        self.thresh1 = SigTo(-20, 0.05)
        self.ratio1 = SigTo(1, 0.05)
        self.boost1 = SigTo(0, 0.05)
        self.gain1 = DBToA(self.boost1)
        self.output = Compress(self.split, thresh=self.thresh1, ratio=self.ratio1, knee=0.5, mul=self.gain1).mix(1)
        self.display = self.output

class VocoderModule(wx.Panel):
    """
    Module: 06-Vocodeur
    -------------------

    Ce module illustre le vocodeur dans le domaine temporel.

    Un vocodeur comprend une partie « analyseur » et une partie « synthétiseur ».
    Un suivi d'amplitude est appliqué à différentes tranches de fréquence dans la
    « analyseur » et le résultat est utilisé pour moduler l'amplitude des tranches
    de fréquences respectives dans la partie « synthétiseur ».

    Contrôles:
        Freq:
            Fréquence de base pour la séparation en tranche de fréquence.
        Exp:
            Facteur d'expansion appliqué aux fréquences successives (en 
            commençant par la fréquence de base) pour déterminer la fréquence
            centrale des filtres passe-bande.
        Q:
            Facteur de qualité des filtres (largeur de bande = fréquence centrale
            divisée par le facteur de qualité).
        Pente:
            Réactivité des suivis d'amplitude. Plus cette valeur est élevé, plus les
            suivis sont précis dans le temps.
        Nbrs:
            Nombre de filtres passe-bande constituant le vocodeur.

    """
    name = "06-Vocodeur"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Sources Sonores")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        row1 = wx.BoxSizer(wx.HORIZONTAL)

        loadbutton = wx.Button(self, -1, "Enveloppe")
        loadbutton.Bind(wx.EVT_BUTTON, self.onLoadSoundfile)
        row1.Add(loadbutton, 1, wx.ALL|wx.EXPAND, 5)

        loadbutton2 = wx.Button(self, -1, "Excitation")
        loadbutton2.Bind(wx.EVT_BUTTON, self.onLoadSoundfile2)
        row1.Add(loadbutton2, 1, wx.ALL|wx.EXPAND, 5)

        sizer.Add(row1, 0, wx.EXPAND)

        self.playbutton = wx.ToggleButton(self, -1, "Jouer les sons")
        self.playbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onPlaySoundfile)
        sizer.Add(self.playbutton, 0, wx.ALL|wx.EXPAND, 5)

        sizer.AddSpacer(10)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        sizer.AddSpacer(10)

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        self.p1 = LabelKnob(self, " Freq", mini=40, maxi=250, init=100, outFunction=self.setFreq)
        self.p2 = LabelKnob(self, " Exp.", mini=0.5, maxi=2, init=1.2, outFunction=self.setExp)
        self.p3 = LabelKnob(self, "  Q ", mini=1, maxi=100, init=20, outFunction=self.setQ)
        self.p4 = LabelKnob(self, "Pente", mini=0, maxi=1, init=0.5, outFunction=self.setSlope)
        self.p5 = LabelKnob(self, " Nbrs", mini=2, maxi=64, init=24, integer=True, outFunction=self.setStages)
        box1.AddMany([(self.p1, 1), (self.p2, 1), (self.p3, 1), (self.p4, 1), (self.p5, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 0)

        labeldb = wx.StaticText(self, -1, "Volume (dB)")
        self.db = PyoGuiControlSlider(self, -60, 18, 0)
        self.db.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.db.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeVol)

        sizer.Add(labeldb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.db, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def onLoadSoundfile(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'enveloppe spectrale",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_PREVIEW)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if sndinfo(path) is not None:
                self.soundtable.setSound(path)
                self.soundfile.freq = self.soundtable.getRate()

        dlg.Destroy()

    def onLoadSoundfile2(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'excitation",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_PREVIEW)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if sndinfo(path) is not None:
                self.soundtable2.setSound(path)
                self.soundfile2.freq = self.soundtable2.getRate()

        dlg.Destroy()

    def onPlaySoundfile(self, evt):
        if evt.GetInt():
            self.soundfile.play()
            self.soundfile2.play()
        else:
            self.soundfile.stop()
            self.soundfile2.stop()

    def setFreq(self, value):
        self.freq.value = value

    def setExp(self, value):
        self.exp.value = value

    def setQ(self, value):
        self.q.value = value

    def setSlope(self, value):
        self.slope.value = value

    def setStages(self, value):
        self.output.stages = value

    def changeVol(self, evt):
        self.gain.value = pow(10, evt.value * 0.05)

    def processing(self):
        self.gain = SigTo(1, 0.05, mul=0.25)
        self.fade = Fader(fadein=1, mul=self.gain).play()
        self.freq = SigTo(100, 0.05)
        self.exp = SigTo(1.2, 0.05)
        self.q = SigTo(20, 0.05)
        self.slope = SigTo(0.5, 0.05)

        # Soundfile player 1
        self.soundtable = SndTable(initchnls=2)
        self.soundfile = TableRead(self.soundtable, freq=1, loop=1, interp=4)
        self.soundfilemono = self.soundfile.mix()
        # Soundfile player 2
        self.soundtable2 = SndTable(initchnls=2)
        self.soundfile2 = TableRead(self.soundtable2, freq=1, loop=1, interp=4)
        self.soundfilemono2 = self.soundfile2.mix()

        self.output = Vocoder(self.soundfilemono, self.soundfilemono2, freq=self.freq,
                              spread=self.exp, q=self.q, slope=self.slope, mul=self.fade)
        self.display = self.output

class SpectralFilterModule(wx.Panel):
    """
    Module: 06-Filtre Spectral
    --------------------------

    Ce module permet d'expérimenter avec le filtrage dans le 
    domaine spectral.

    Une analyse FFT est d'abord effectuée sur le signal et le 
    volume de chacune des tranches de fréquence peut ensuite
    être contrôlé indépendamment à l'aide d'un graphique à bande.

    Contrôles:
        Taille FFT:
            Nombre de points dans l'analyse FFT. Le spectre entre
            0 et la fréquence d'échantillonnage sera séparé en
            autant de tranches. Le nombre de tranches effectives
            est donc `taille FFT / 2`, c'est-à-dire les tranches
            entre 0 et la fréquence de Nyquist.
        Chevauchements:
            Le nombre d'analyses qui se chevauchent sur la durée
            correspondant à la taille FFT. Pour certain effets 
            (en particulier la transposition et l'expansion 
            temporelle), plus cette valeur est élevé, plus le rendu
            sonore est de qualité. 
        Fenêtre:
            Le type de fenêtre appliqué avant et après l'analyse, afin
            d'éliminer les artefacts dans le rendu sonore.
        Dessiner le filtre (256 points):
            Les volume individuels des 256 premières tranches de 
            fréquence (0 à Nyquist pour une taille de 512).

    """
    name = "06-Filtre Spectral"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        # FFT properties widgets #
        box1 = wx.BoxSizer(wx.HORIZONTAL)

        sizeBox = wx.BoxSizer(wx.VERTICAL)
        sizelabel = wx.StaticText(self, -1, "Taille FFT")
        sizeChoice = wx.Choice(self, -1, choices=SIZECHOICES)
        sizeChoice.SetSelection(4)
        sizeChoice.Bind(wx.EVT_CHOICE, self.changeSize)
        sizeBox.AddMany([(sizelabel, 0, wx.EXPAND), (sizeChoice, 0, wx.EXPAND)])

        overBox = wx.BoxSizer(wx.VERTICAL)
        overlabel = wx.StaticText(self, -1, "Chevauchements")
        overChoice = wx.Choice(self, -1, choices=OVERLAPS)
        overChoice.SetSelection(1)
        overChoice.Bind(wx.EVT_CHOICE, self.changeOver)
        overBox.AddMany([(overlabel, 0, wx.EXPAND), (overChoice, 0, wx.EXPAND)])

        typelabel = wx.StaticText(self, -1, "Fenêtre")
        type = wx.Choice(self, -1, choices=WINCHOICES)
        type.SetSelection(2)
        type.Bind(wx.EVT_CHOICE, self.changeType)

        box1.AddMany([(sizeBox, 1, wx.ALL, 1), (overBox, 1, wx.ALL, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        # FFT properties widgets #

        box2 = wx.BoxSizer(wx.VERTICAL)
        graphLabel = wx.StaticText(self, -1, label="Dessiner le filtre (256 points)")
        grapher = DataMultiSlider(self, [0.0 for i in range(256)], outFunction=self.changeFilter)
        box2.AddMany([(graphLabel, 0), (grapher, 0, wx.EXPAND)])

        sizer.Add(box2, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def changeSize(self, evt):
        newsize = int(evt.GetString())
        self.pva.size = newsize

    def changeOver(self, evt):
        newolaps = int(evt.GetString())
        self.pva.overlaps = newolaps

    def changeType(self, evt):
        newtype = evt.GetInt()
        self.pva.wintype = newtype
        self.output.wintype = newtype

    def changeFilter(self, values):
        if hasattr(self, "table"):
            self.table.replace(values)

    def processing(self):
        self.table = DataTable(256)
        self.pva = PVAnal(self.inputpanel.output)
        self.pvf = PVFilter(self.pva, self.table)
        self.output = PVSynth(self.pvf)
        self.display = self.output

class CrossSynthModule(wx.Panel):
    """
    Module: 06-Synthèse croisée
    ---------------------------

    Ce module permet d'expérimenter avec la synthèse croisée dans
    le domaine spectral.

    Une analyse FFT est d'abord effectuée sur deux signaux puis leurs
    spectres sont ensuite multipliés afin d'appliquer le profil spectral
    du premier son sur le contenu fréquentiel du second.

    Contrôles:
        Enveloppe:
            Permet de choisir la première source sonore (enveloppe spectrale).
            Ce signal doit généralement être dynamique, tant au niveau
            des fréquences que de l'amplitude.
        Excitation:
            Permet de choisir la seconde source sonore.
            Ce signal doit généralement être riche en contenu fréquentiel
            et stable au niveau des amplitudes.
        Jouer les sons:
            Lance la lecture des sons.
        Taille FFT:
            Nombre de points dans l'analyse FFT. Le spectre entre
            0 et la fréquence d'échantillonnage sera séparé en
            autant de tranches. Le nombre de tranches effectives
            est donc `taille FFT / 2`, c'est-à-dire les tranches
            entre 0 et la fréquence de Nyquist.
        Chevauchements:
            Le nombre d'analyses qui se chevauchent sur la durée
            correspondant à la taille FFT. Pour certain effets 
            (en particulier la transposition et l'expansion 
            temporelle), plus cette valeur est élevé, plus le rendu
            sonore est de qualité. 
        Fenêtre:
            Le type de fenêtre appliqué avant et après l'analyse, afin
            d'éliminer les artefacts dans le rendu sonore.
        Volume (dB):
            Permet d'ajuster le volume après la synthèse croisée.

    """
    name = "06-Synthèse croisée"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Sources Sonores")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        row1 = wx.BoxSizer(wx.HORIZONTAL)

        loadbutton = wx.Button(self, -1, "Enveloppe")
        loadbutton.Bind(wx.EVT_BUTTON, self.onLoadSoundfile)
        row1.Add(loadbutton, 1, wx.ALL|wx.EXPAND, 5)

        loadbutton2 = wx.Button(self, -1, "Excitation")
        loadbutton2.Bind(wx.EVT_BUTTON, self.onLoadSoundfile2)
        row1.Add(loadbutton2, 1, wx.ALL|wx.EXPAND, 5)

        sizer.Add(row1, 0, wx.EXPAND)

        self.playbutton = wx.ToggleButton(self, -1, "Jouer les sons")
        self.playbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onPlaySoundfile)
        sizer.Add(self.playbutton, 0, wx.ALL|wx.EXPAND, 5)

        sizer.AddSpacer(10)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        # FFT properties widgets #
        box1 = wx.BoxSizer(wx.HORIZONTAL)

        sizeBox = wx.BoxSizer(wx.VERTICAL)
        sizelabel = wx.StaticText(self, -1, "Taille FFT")
        sizeChoice = wx.Choice(self, -1, choices=SIZECHOICES)
        sizeChoice.SetSelection(4)
        sizeChoice.Bind(wx.EVT_CHOICE, self.changeSize)
        sizeBox.AddMany([(sizelabel, 0, wx.EXPAND), (sizeChoice, 0, wx.EXPAND)])

        overBox = wx.BoxSizer(wx.VERTICAL)
        overlabel = wx.StaticText(self, -1, "Chevauchements")
        overChoice = wx.Choice(self, -1, choices=OVERLAPS)
        overChoice.SetSelection(1)
        overChoice.Bind(wx.EVT_CHOICE, self.changeOver)
        overBox.AddMany([(overlabel, 0, wx.EXPAND), (overChoice, 0, wx.EXPAND)])

        typelabel = wx.StaticText(self, -1, "Fenêtre")
        type = wx.Choice(self, -1, choices=WINCHOICES)
        type.SetSelection(2)
        type.Bind(wx.EVT_CHOICE, self.changeType)

        box1.AddMany([(sizeBox, 1, wx.ALL, 1), (overBox, 1, wx.ALL, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        # FFT properties widgets #

        labeldb = wx.StaticText(self, -1, "Volume (dB)")
        self.db = PyoGuiControlSlider(self, -60, 18, 0)
        self.db.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.db.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeVol)

        sizer.Add(labeldb, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.db, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def onLoadSoundfile(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'enveloppe spectrale",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_PREVIEW)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if sndinfo(path) is not None:
                self.soundtable2.setSound(path)
                self.soundfile2.freq = self.soundtable2.getRate()

        dlg.Destroy()

    def onLoadSoundfile2(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'excitation",
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
            self.soundfile2.play()
        else:
            self.soundfile.stop()
            self.soundfile2.stop()

    def changeSize(self, evt):
        newsize = int(evt.GetString())
        self.pva.size = newsize
        self.pva2.size = newsize

    def changeOver(self, evt):
        newolaps = int(evt.GetString())
        self.pva.overlaps = newolaps
        self.pva2.overlaps = newolaps

    def changeType(self, evt):
        newtype = evt.GetInt()
        self.pva.wintype = newtype
        self.pva2.wintype = newtype
        self.output.wintype = newtype

    def changeVol(self, evt):
        self.gain.value = pow(10, evt.value * 0.05)

    def processing(self):
        self.gain = SigTo(1)
        self.fade = Fader(fadein=1, mul=self.gain).play()
        # Soundfile player 1
        self.soundtable = SndTable(initchnls=2)
        self.soundfile = TableRead(self.soundtable, freq=1, loop=1, interp=4)
        self.soundfilemono = self.soundfile.mix()
        # Soundfile player 2
        self.soundtable2 = SndTable(initchnls=2)
        self.soundfile2 = TableRead(self.soundtable2, freq=1, loop=1, interp=4)
        self.soundfilemono2 = self.soundfile2.mix()

        self.pva = PVAnal(self.soundfilemono)
        self.pva2 = PVAnal(self.soundfilemono2)
        self.pvmult = PVMult(self.pva, self.pva2)
        self.output = PVSynth(self.pvmult, mul=self.fade)
        self.display = self.output

class SpectralPlaybackModule(wx.Panel):
    """
    Module: 06-Vitesse et Hauteur Indépendantes
    -------------------------------------------

    Ce module permet d'expérimenter avec la resynthèse dans le 
    domaine spectral.

    Une analyse FFT (Vocodeur de phase) est d'abord effectuée sur
    le signal et le résultat de chacune des analyses successives
    est sauvegardé dans un tableau. La lecture du tableau permet
    un contrôle indépendant de la vitesse de lecture et de la 
    hauteur (transposition) du son.

    Contrôles:
        Fichier sonore:
            permet de sélectionner le fichier son à resynthétiser.
        Taille FFT:
            Nombre de points dans l'analyse FFT. Le spectre entre
            0 et la fréquence d'échantillonnage sera séparé en
            autant de tranches. Le nombre de tranches effectives
            est donc `taille FFT / 2`, c'est-à-dire les tranches
            entre 0 et la fréquence de Nyquist.
        Chevauchements:
            Le nombre d'analyses qui se chevauchent sur la durée
            correspondant à la taille FFT. Pour certain effets 
            (en particulier la transposition et l'expansion 
            temporelle), plus cette valeur est élevé, plus le rendu
            sonore est de qualité. 
        Fenêtre:
            Le type de fenêtre appliqué avant et après l'analyse, afin
            d'éliminer les artefacts dans le rendu sonore.
        Enregistrer et jouer...:
            Lance l'analyse du son et la lecture du tableau contenant
            les analyses successives.
        Vitesse de lecture:
            Contrôle la vitesse de lecture, c'est-à-dire la vitesse
            à laquelle les analyses successives sont lues.
        Transposition:
            Contrôle la transposition du spectre à la lecture.

    """
    name = "06-Vitesse et Hauteur Indépendantes"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        loadbutton = wx.Button(self, -1, "Fichier sonore")
        loadbutton.Bind(wx.EVT_BUTTON, self.onLoadSoundfile)
        sizer.Add(loadbutton, 0, wx.ALL|wx.EXPAND, 5)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        # FFT properties widgets #
        box1 = wx.BoxSizer(wx.HORIZONTAL)

        sizeBox = wx.BoxSizer(wx.VERTICAL)
        sizelabel = wx.StaticText(self, -1, "Taille FFT")
        sizeChoice = wx.Choice(self, -1, choices=SIZECHOICES)
        sizeChoice.SetSelection(4)
        sizeChoice.Bind(wx.EVT_CHOICE, self.changeSize)
        sizeBox.AddMany([(sizelabel, 0, wx.EXPAND), (sizeChoice, 0, wx.EXPAND)])

        overBox = wx.BoxSizer(wx.VERTICAL)
        overlabel = wx.StaticText(self, -1, "Chevauchements")
        overChoice = wx.Choice(self, -1, choices=OVERLAPS)
        overChoice.SetSelection(1)
        overChoice.Bind(wx.EVT_CHOICE, self.changeOver)
        overBox.AddMany([(overlabel, 0, wx.EXPAND), (overChoice, 0, wx.EXPAND)])

        typelabel = wx.StaticText(self, -1, "Fenêtre")
        type = wx.Choice(self, -1, choices=WINCHOICES)
        type.SetSelection(2)
        type.Bind(wx.EVT_CHOICE, self.changeType)

        box1.AddMany([(sizeBox, 1, wx.ALL, 1), (overBox, 1, wx.ALL, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        # FFT properties widgets #

        sizer.AddSpacer(10)

        self.buttonrec = wx.ToggleButton(self, -1, "Enregistrer et jouer...")
        self.buttonrec.Bind(wx.EVT_TOGGLEBUTTON, self.record)
        sizer.Add(self.buttonrec, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        labelspeed = wx.StaticText(self, -1, "Vitesse de lecture")
        self.speed = PyoGuiControlSlider(self, -2, 2, 0.5)
        self.speed.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.speed.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSpeed)

        sizer.Add(labelspeed, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.speed, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        labelpitch = wx.StaticText(self, -1, "Transposition")
        self.pitch = PyoGuiControlSlider(self, 0.1, 2, 1)
        self.pitch.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.pitch.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changePitch)

        sizer.Add(labelpitch, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.pitch, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        sizer.AddSpacer(10)

        self.waitinglabel = wx.StaticText(self, -1, "")
        sizer.Add(self.waitinglabel, 0, wx.EXPAND|wx.LEFT|wx.TOP, 5)

        self.SetSizer(sizer)

    def onLoadSoundfile(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'enveloppe spectrale",
            defaultDir=os.getcwd(),
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_PREVIEW)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if sndinfo(path) is not None:
                self.soundtable.setSound(path)
                self.soundfile.freq = self.soundtable.getRate()

        dlg.Destroy()

    def changeSize(self, evt):
        newsize = int(evt.GetString())
        self.pva.size = newsize
        self.recording()

    def changeOver(self, evt):
        newolaps = int(evt.GetString())
        self.pva.overlaps = newolaps
        self.recording()

    def changeType(self, evt):
        newtype = evt.GetInt()
        self.pva.wintype = newtype
        self.output.wintype = newtype

    def record(self, evt):
        if evt.GetInt():
            self.recording()
        else:
            self.pvb.stop()
            self.gain.stop()

    def recording(self):
        dur = self.soundtable.getDur()
        self.pvb.length = dur
        self.soundfile.play()
        self.gain.play()
        self.pvb.play()
        self.waitinglabel.SetLabel("Mise en mémoire...")
        wx.CallLater(dur*1000, self.waitinglabel.SetLabel, "")

    def changeSpeed(self, evt):
        self.rate.value = evt.value

    def changePitch(self, evt):
        self.pit.value = evt.value

    def processing(self):
        self.gain = Fader(0.05, 0.05, 0)

        self.soundtable = SndTable(initchnls=2)
        self.soundfile = TableRead(self.soundtable, freq=1, loop=1, interp=4)

        self.rate = SigTo(0.5)
        self.index = Phasor(freq=1/5*self.rate)
        self.pit = SigTo(1)

        self.pva = PVAnal(self.soundfile)
        self.pvb = PVBuffer(self.pva, self.index, self.pit, length=5).stop()
        self.output = PVSynth(self.pvb, mul=self.gain)
        self.display = self.output

class SpectralDelayModule(wx.Panel):
    """
    Module: 06-Délai Spectral
    --------------------------

    Ce module permet d'expérimenter avec le délai par tranche de
    fréquence dans le domaine spectral.

    Une analyse FFT (Vocodeur de phase) est d'abord effectuée sur 
    le signal puis chacune des tranches de fréquence peut être
    délayée (avec facteur de récursion) indépendamment les unes
    des autres.

    Contrôles:
        Choisir un son:
            Permet de sélectionner un fichier sonore.
        Jouer:
            Lance la lecture du fichier son en boucle.
        Taille FFT:
            Nombre de points dans l'analyse FFT. Le spectre entre
            0 et la fréquence d'échantillonnage sera séparé en
            autant de tranches. Le nombre de tranches effectives
            est donc `taille FFT / 2`, c'est-à-dire les tranches
            entre 0 et la fréquence de Nyquist.
        Chevauchements:
            Le nombre d'analyses qui se chevauchent sur la durée
            correspondant à la taille FFT. Pour certain effets 
            (en particulier la transposition et l'expansion 
            temporelle), plus cette valeur est élevé, plus le rendu
            sonore est de qualité. 
        Fenêtre:
            Le type de fenêtre appliqué avant et après l'analyse, afin
            d'éliminer les artefacts dans le rendu sonore.
        Délai par tranche de fréquence:
            Ce graphique à bande permet de contrôler le temps de délai
            (en multiple de la taille FFT divisée par le nombre de 
            chevauchements) indépendamment pour chacune des tranches de
            fréquence.
        Récursion par tranche de fréq.:
            Ce graphique à bande permet de contrôler le facteur de récursion
            indépendamment pour chacune des tranches de fréquence.

    """
    name = "06-Délai Spectral"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.maxDelay = 2.0
        self.fftsize = 1024
        self.overlaps = 4
        self.frames = int(self.maxDelay * self.GetParent().GetParent().server.getSamplingRate() / (self.fftsize / self.overlaps))

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        row1 = wx.BoxSizer(wx.HORIZONTAL)

        loadbutton = wx.Button(self, -1, "Choisir un son")
        loadbutton.Bind(wx.EVT_BUTTON, self.onLoadSoundfile)
        row1.Add(loadbutton, 1, wx.RIGHT, 5)

        self.playbutton = wx.ToggleButton(self, -1, "Jouer")
        self.playbutton.Bind(wx.EVT_TOGGLEBUTTON, self.onPlaySoundfile)
        row1.Add(self.playbutton, 0)

        sizer.Add(row1, 0, wx.ALL|wx.EXPAND, 5)

        sizer.AddSpacer(10)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        # FFT properties widgets #
        box1 = wx.BoxSizer(wx.HORIZONTAL)

        sizeBox = wx.BoxSizer(wx.VERTICAL)
        sizelabel = wx.StaticText(self, -1, "Taille FFT")
        sizeChoice = wx.Choice(self, -1, choices=SIZECHOICES)
        sizeChoice.SetSelection(4)
        sizeChoice.Bind(wx.EVT_CHOICE, self.changeSize)
        sizeBox.AddMany([(sizelabel, 0, wx.EXPAND), (sizeChoice, 0, wx.EXPAND)])

        overBox = wx.BoxSizer(wx.VERTICAL)
        overlabel = wx.StaticText(self, -1, "Chevauchements")
        overChoice = wx.Choice(self, -1, choices=OVERLAPS)
        overChoice.SetSelection(1)
        overChoice.Bind(wx.EVT_CHOICE, self.changeOver)
        overBox.AddMany([(overlabel, 0, wx.EXPAND), (overChoice, 0, wx.EXPAND)])

        typelabel = wx.StaticText(self, -1, "Fenêtre")
        type = wx.Choice(self, -1, choices=WINCHOICES)
        type.SetSelection(2)
        type.Bind(wx.EVT_CHOICE, self.changeType)

        box1.AddMany([(sizeBox, 1, wx.ALL, 1), (overBox, 1, wx.ALL, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 4)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        # FFT properties widgets #

        box2 = wx.BoxSizer(wx.VERTICAL)
        delayLabel = wx.StaticText(self, -1, label="Délai par tranche de fréquence")
        self.delay = DataMultiSlider(self, [0.0 for i in range(256)], yrange=(0, self.frames), size=(-1, 100), outFunction=self.changeDelay)
        box2.AddMany([(delayLabel, 0), (self.delay, 0, wx.EXPAND)])

        sizer.Add(box2, 0, wx.EXPAND | wx.ALL, 5)

        box3 = wx.BoxSizer(wx.VERTICAL)
        feedLabel = wx.StaticText(self, -1, label="Récursion par tranche de fréq.")
        feed = DataMultiSlider(self, [0.0 for i in range(256)], size=(-1, 100), outFunction=self.changeFeed)
        box3.AddMany([(feedLabel, 0), (feed, 0, wx.EXPAND)])

        sizer.Add(box3, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def onLoadSoundfile(self, evt):
        dlg = wx.FileDialog(
            self, message="Choisir le fichier d'enveloppe spectrale",
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

    def changeSize(self, evt):
        self.fftsize = int(evt.GetString())
        self.pva.size = self.fftsize
        self.frames = int(self.maxDelay * self.GetParent().GetParent().server.getSamplingRate() / (self.fftsize / self.overlaps))
        self.delay.yrange = (0, self.frames)

    def changeOver(self, evt):
        self.overlaps = int(evt.GetString())
        self.pva.overlaps = self.overlaps
        self.frames = int(self.maxDelay * self.GetParent().GetParent().server.getSamplingRate() / (self.fftsize / self.overlaps))
        self.delay.yrange = (0, self.frames)

    def changeType(self, evt):
        newtype = evt.GetInt()
        self.pva.wintype = newtype
        self.output.wintype = newtype

    def changeDelay(self, values):
        if hasattr(self, "deltable"):
            self.deltable.replace(values)

    def changeFeed(self, values):
        if hasattr(self, "feedtable"):
            self.feedtable.replace(values)

    def processing(self):
        self.soundtable = SndTable(initchnls=2)
        self.soundfile = TableRead(self.soundtable, freq=1, loop=1, interp=4)

        self.deltable = DataTable(256)
        self.feedtable = DataTable(256)
        self.pva = PVAnal(self.soundfile)
        self.pvd = PVDelay(self.pva, self.deltable, self.feedtable, maxdelay=self.maxDelay, mode=1)
        self.output = PVSynth(self.pvd)
        self.display = self.output

class AddSynthFixModule(wx.Panel):
    """
    Module: 08-Sommation de sinusoïdes
    ----------------------------------

    Ce module permet de construire graduellement des formes d'onde
    en dent de scie, carrée et triangulaire par sommation d'ondes
    sinusoïdales.

    Dent de scie:
        Constituée de toutes les harmoniques. L'amplitude de chacune
        des harmoniques est l'inverse de son rang, A(n) = 1 / n.
    Onde carrée:
        Constituée uniquement des harmoniques impaires. L'amplitude
        de chacune des harmoniques est l'inverse de son rang, A(n) = 1 / n.
    Onde triangulaire:
        Constituée uniquement des harmoniques impaires. L'amplitude
        de chacune des harmoniques est l'inverse de son rang au carrée,
        A(n) = 1 / (n*n). Dans le cas de l'onde triangulaire, chaque
        deuxième harmonique est inversée en phase.

    Contrôles:
        Forme d'onde:
            Choix de la forme d'onde à construire. Les choix sont:
            Dent de scie, Onde carrée et Onde triangulaire.
        Fréquence fondamentale:
            Fréquence, en Hertz, de l'oscillateur qui lit la forme d'onde.
        Nombre d'harmoniques:
            Détermine de combien de composantes est constituée la forme
            d'onde. Plus le nombre est élevé, plus la forme est précise.
    """
    name = "08-Sommation de sinusoïdes"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.which = 0
        self.order = 10

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        typelabel = wx.StaticText(self, -1, "Forme d'onde")
        choices = ["Dent de scie", "Onde carrée", "Onde triangulaire"]
        type = wx.Choice(self, -1, choices=choices)
        type.SetSelection(0)
        type.Bind(wx.EVT_CHOICE, self.changeWaveType)

        labelfr = wx.StaticText(self, -1, "Fréquence fondamentale")
        self.fr = PyoGuiControlSlider(self, 40, 4000, 172, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelhr = wx.StaticText(self, -1, "Nombre d'harmoniques")
        self.hr = PyoGuiControlSlider(self, 1, 50, 10, integer=True)
        self.hr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.hr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeHarms)

        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelhr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.hr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeWaveType(self, evt):
        self.which = evt.GetInt()
        if self.which == 0:
            self.output.table = self.sawtable
        elif self.which == 1:
            self.output.table = self.sqrtable
        elif self.which == 2:
            self.output.table = self.tritable
        self.output.table.order = self.order
        self.output.table.normalize()

    def changeHarms(self, evt):
        self.order = int(evt.value)
        self.output.table.order = self.order
        self.output.table.normalize()

    def changeFreq(self, evt):
        self.freq.value = evt.value

    def processing(self):
        self.freq = SigTo(172, 0.05)
        self.sawtable = SawTable(10)
        self.sqrtable = SquareTable(10)
        self.tritable = TriTable(10)
        self.output = Osc(self.sawtable, self.freq, mul=0.707)
        self.display = self.output

class AddSynthVarModule(wx.Panel):
    """
    Module: 08-Synthèse Additive
    ----------------------------

    Ce module permet d'expérimenter avec certains algorithmes de réduction
    de données dans un contexte de synthèse additive à forme d'onde variable.
    Ce module permet de générer un palette très large de timbres, explorez
    différentes combinaisons de paramètres.

    Contrôles:
        Nombre de partiels:
            Détermine le nombre d'oscillateurs composant le signal sonore.
        Env. att - dec - sus - rel:
            Enveloppe d'amplitude de type ADSR (Attack, Decay, Sustain, Release).
            att: Durée, en millisecondes, de la phase ascendante de l'enveloppe.
            dec: Durée, en millisecondes, de la phase d'atténuation suivant la
                 phase d'attaque.
            sus: Valeur d'amplitude de la tenue de l'enveloppe.
            rel: Durée, en milliseconde, de la relâche, c'est-à-dire le retour
                 à zéro de l'enveloppe.
        Réduction amp:
            Facteur de réduction d'une série de puissance permettant de
            générer l'amplitude de tous les partiels avec une seule valeur.
            L'amplitude de chacun des partiels est l'amplitude du partiel
            précédent multipliée par ce facteur. A(n) = A(n-1) * facteur.
        Réduction dur:
            Facteur de réduction d'une série de puissance permettant de
            contrôler la durée de l'enveloppe de tous les partiels avec
            une seule valeur. La durée des segments de l'enveloppe de
            chacun des partiels est la durée des segments de l'enveloppe
            du partiel précédent multipliée par ce facteur.
            att(n) = att(n-1) * facteur, dec(n) = dec(n-1) * facteur, etc.
        Fondamentale:
            Fréquence fondamentale du signal en Hertz. Pour des timbres
            inharmoniques, on dirait plutôt que c'est la fréquence du premier
            partiel.
        Expansion:
            Facteur de compression/expansion d'une série de puissance servant
            à générer la fréquence de chacun des partiels. L'expression est
            la suivante: f(n) = fond * n ^ facteur
            La fréquence fondamentale est multipliée au rang harmonique, élevé
            à une puisssance donnée par ce paramètre.
            - Pour un facteur de 1 la série harmonique (multiples entiers) de
            la fréquence fondamentale.
            - Pour un facteur prés de 0 de légères déviations (chorus) de la
            fréquence fondamentale.
            - Pour un facteur > 1 une expansion exponentielle des fréquences
            des harmoniques.
        Amp. Var. amp - freq - type
            Contrôle les balises des générateurs aléatoires associés à
            l'amplitude des différents partiels. Chaque partiel possède son
            générateur aléatoire indépendant.
            amp: Profondeur des variations.
            freq: Vitesse, en Hertz, des variations.
            type: Type de générateur, 0 = random avec interpolation,
                  1 = random avec tenue (sample-and-hold),
                  2 = random uniforme (bruit blanc).
        Freq Var. amp - freq - type
            Contrôle les balises des générateurs aléatoires associés à la
            fréquence des différents partiels. Chaque partiel possède son
            générateur aléatoire indépendant.
            amp: Profondeur des variations.
            freq: Vitesse, en Hertz, des variations.
            type: Type de générateur, 0 = random avec interpolation,
                  1 = random avec tenue (sample-and-hold),
                  2 = random uniforme (bruit blanc).
        Forme d'onde:
            Permet de changer la forme d'onde lue par chacun des partiels.
            Une forme d'onde complexe permet de décupler rapidement, et
            efficacement, la quantité de composantes dans le signal final.
        Jouer:
            Bouton permettant de jouer un son. Un premier clic déclenche la
            première section de l'enveloppe (att - dec - sus) qui maintient
            sa valeur de tenue. Un second clic active la phase de relâche
            de l'enveloppe.

    """
    name = "08-Synthèse Additive"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelpt = wx.StaticText(self, -1, "Nombre de partiels")
        self.pt = PyoGuiControlSlider(self, 1, 60, 30, integer=True)
        self.pt.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.pt.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.setPartials)

        sizer.Add(labelpt, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.pt, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        box1 = wx.BoxSizer(wx.HORIZONTAL)
        envel = wx.StaticText(self, -1, "Env. ")
        self.att = LabelKnob(self, " att", mini=1, maxi=2000, init=10, log=True, outFunction=self.setAttack)
        self.dec = LabelKnob(self, " dec", mini=1, maxi=2000, init=100, log=True, outFunction=self.setDecay)
        self.sus = LabelKnob(self, " sus", mini=0, maxi=1, init=0.7, outFunction=self.setSustain)
        self.rel = LabelKnob(self, " rel", mini=1, maxi=2000, init=500, log=True, outFunction=self.setRelease)
        box1.AddMany([(envel, 0, wx.ALIGN_CENTER_VERTICAL), (self.att, 1), (self.dec, 1), (self.sus, 1), (self.rel, 1)])

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 5)

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        ampbox = wx.BoxSizer(wx.VERTICAL)
        labadf = wx.StaticText(self, -1, "Réduction amp")
        self.adf = PyoGuiControlSlider(self, 0.5, 1, 0.9, size=(120,16))
        self.adf.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.adf.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.setAmpDamp)
        ampbox.Add(labadf, 0, wx.LEFT|wx.TOP, 5)
        ampbox.Add(self.adf, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box2.Add(ampbox, 1)
        timbox = wx.BoxSizer(wx.VERTICAL)
        labtim = wx.StaticText(self, -1, "Réduction dur")
        self.tim = PyoGuiControlSlider(self, 0.5, 1, 0.9, size=(120,16))
        self.tim.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.tim.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.setTimeDamp)
        timbox.Add(labtim, 0, wx.LEFT|wx.TOP, 5)
        timbox.Add(self.tim, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box2.Add(timbox, 1)

        sizer.Add(box2, 0, wx.EXPAND)

        box3 = wx.BoxSizer(wx.HORIZONTAL)
        funbox = wx.BoxSizer(wx.VERTICAL)
        labfun = wx.StaticText(self, -1, "Fondamentale")
        self.fun = PyoGuiControlSlider(self, 40, 4000, 172, log=True, size=(120,16))
        self.fun.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fun.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.setFreq)
        funbox.Add(labfun, 0, wx.LEFT|wx.TOP, 5)
        funbox.Add(self.fun, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box3.Add(funbox, 1)
        spdbox = wx.BoxSizer(wx.VERTICAL)
        labspd = wx.StaticText(self, -1, "Expansion")
        self.spd = PyoGuiControlSlider(self, 0.001, 2, 1, log=True, size=(120,16))
        self.spd.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.spd.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.setSpread)
        spdbox.Add(labspd, 0, wx.LEFT|wx.TOP, 5)
        spdbox.Add(self.spd, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box3.Add(spdbox, 1)

        sizer.Add(box3, 0, wx.EXPAND)

        box4 = wx.BoxSizer(wx.HORIZONTAL)
        ampvar = wx.StaticText(self, -1, "Amp. Var.  ")
        self.ard = LabelKnob(self, " amp", mini=0, maxi=1, init=0, outFunction=self.setAmpVarAmp)
        self.ars = LabelKnob(self, " freq", mini=0.01, maxi=20, init=1, log=True, outFunction=self.setAmpVarFreq)
        self.art = LabelKnob(self, " type", mini=0, maxi=2.66, init=0, integer=True, outFunction=self.setAmpVarType)
        box4.AddMany([(ampvar, 0, wx.ALIGN_CENTER_VERTICAL), (self.ard, 1), (self.ars, 1), (self.art, 1)])

        box5 = wx.BoxSizer(wx.HORIZONTAL)
        freqvar = wx.StaticText(self, -1, "Freq Var.  ")
        self.frd = LabelKnob(self, " amp", mini=0, maxi=0.5, init=0, outFunction=self.setFreqVarAmp)
        self.frs = LabelKnob(self, " freq", mini=0.01, maxi=20, init=1, log=True, outFunction=self.setFreqVarFreq)
        self.frt = LabelKnob(self, " type", mini=0, maxi=2.66, init=0, integer=True, outFunction=self.setFreqVarType)
        box5.AddMany([(freqvar, 0, wx.ALIGN_CENTER_VERTICAL), (self.frd, 1), (self.frs, 1), (self.frt, 1)])

        sizer.Add(box4, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(box5, 0, wx.EXPAND | wx.ALL, 5)

        box6 = wx.BoxSizer(wx.HORIZONTAL)
        wavbox = wx.BoxSizer(wx.VERTICAL)
        wavelabel = wx.StaticText(self, -1, "Forme d'onde")
        choices = ["Sinus", "Scie 5", "Scie 15",
                   "Scie 30", "Scie 60",
                   "Carrée 5", "Carrée 15",
                   "Carrée 30", "Carrée 60",
                   "Triangle 3", "Triangle 6",
                   "Triangle 12", "Triangle 24"]
        wave = wx.Choice(self, -1, choices=choices)
        wave.SetSelection(0)
        wave.Bind(wx.EVT_CHOICE, self.setWaveform)
        wavbox.Add(wavelabel, 0, wx.LEFT|wx.TOP, 5)
        wavbox.Add(wave, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box6.Add(wavbox)
        playbox = wx.BoxSizer(wx.VERTICAL)
        playbox.Add(wx.StaticText(self, -1, ""), 0, wx.LEFT|wx.TOP, 5)
        gobutton = wx.ToggleButton(self, label="Jouer")
        gobutton.Bind(wx.EVT_TOGGLEBUTTON, self.play)
        playbox.Add(gobutton, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        box6.Add(playbox, 1)

        sizer.Add(box6, 0, wx.EXPAND)

        self.SetSizer(sizer)

    def play(self, evt):
        if evt.GetInt():
            self.addsynth.play()
        else:
            self.addsynth.stop()

    def setPartials(self, evt):
        self.addsynth.setPartials(int(evt.value))

    def setAttack(self, x):
        self.addsynth.setAttack(x * 0.001)

    def setDecay(self, x):
        self.addsynth.setDecay(x * 0.001)

    def setSustain(self, x):
        self.addsynth.setSustain(x)

    def setRelease(self, x):
        self.addsynth.setRelease(x * 0.001)

    def setAmpDamp(self, evt):
        self.addsynth.setAmpDamp(evt.value)

    def setTimeDamp(self, evt):
        self.addsynth.setTimeDamp(evt.value)

    def setAmpVarAmp(self, x):
        self.addsynth.setAmpVarAmp(x)

    def setAmpVarFreq(self, x):
        self.addsynth.setAmpVarFreq(x)

    def setAmpVarType(self, x):
        self.addsynth.setAmpVarType(x)

    def setFreqVarAmp(self, x):
        self.addsynth.setFreqVarAmp(x)

    def setFreqVarFreq(self, x):
        self.addsynth.setFreqVarFreq(x)

    def setFreqVarType(self, x):
        self.addsynth.setFreqVarType(x)

    def setWaveform(self, evt):
        self.addsynth.setWaveform(evt.GetInt())

    def setFreq(self, evt):
        self.addsynth.setFreq(evt.value)

    def setSpread(self, evt):
        self.addsynth.setSpread(evt.value)

    def processing(self):
        self.addsynth = AdditiveSynthesis()
        self.output = Sig(self.addsynth.output)
        self.display = self.output

class PulseWidthModModule(wx.Panel):
    """
    Module: 08-Modulation de largeur d'impulsion
    --------------------------------------------

    Ce module génère un signal audio à l'aide de la technique dite
    de modulation à largeur d'impulsion.

    Un signal à modulation de largeur d'impulsion (Pulse Width
    Modulation ou PWM en anglais) est constitué de deux composantes
    principales qui définissent son comportement: un rapport cyclique
    et une fréquence. Le rapport cyclique décrit la durée pendant
    laquelle le signal est à l'état haut (ouverture) en pourcentage
    de la durée d'un cycle complet. La fréquence détermine combien de
    cycles complets le signal effectue à la seconde.

    Contrôles:
        Fréquence fondamentale en Hz:
            Contrôle le nombre de cycles (périodes) complets par seconde.
            C'est la fréquence fondamentale du signal en Hertz.
        Cycle d'ouverture en %:
            Contrôle la proportion de la phase d'ouverture par rapport
            à la durée complète du cycle. 50 % signifie que le signal
            passe autant de temps dans le positif que dans le négatif,
            générant ainsi une forme d'onde carrée.
        Filtre anti-alias:
            Qualité du filtre passe-bas servant à adoucir les transitions
            du signal entre 1 et -1. Une valeur de 0 signifie qu'il n'y a
            pas de filtre anti-alias et que le signal alterne entre les
            deux pôles de façon instantannée. Une valeur positive indique
            la taille de la réponse impulsionnelle du filtre passe-bas
            utilisé. La taille est équivalente à la valeur de ce paramètre
            multiplié par 2.

    """
    name = "08-Modulation de largeur d'impulsion"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelfr = wx.StaticText(self, -1, "Fréquence fondamentale en Hz")
        self.fr = PyoGuiControlSlider(self, 40, 2000, 172, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labeldc = wx.StaticText(self, -1, "Cycle d'ouverture en %")
        self.dc = PyoGuiControlSlider(self, 1, 99, 50, integer=True)
        self.dc.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.dc.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeDuty)

        labelfl = wx.StaticText(self, -1, "Filtre anti-alias")
        self.fl = PyoGuiControlSlider(self, 0, 32, 0, integer=True)
        self.fl.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fl.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFilter)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labeldc, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.dc, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfl, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changeFreq(self, evt):
        self.freq.value = evt.value

    def changeDuty(self, evt):
        self.duty.value = evt.value * 0.01

    def changeFilter(self, evt):
        self.output.damp = int(evt.value)

    def processing(self):
        self.freq = SigTo(172, 0.05)
        self.duty = SigTo(0.5, 0.05)
        self.output = PWM(self.freq, 0, self.duty, 0, mul=0.5)
        self.display = self.output

class OscSyncModule(wx.Panel):
    """
    Module: 08-Oscillateur synchronisé
    ----------------------------------

    Ce module permet d'explorer le potentiel de l'oscillateur
    synchronisé.

    Un oscillateur synchronisé, dans les synthétiseurs analogiques,
    était réalisé à l'aide de deux oscillateurs, un "maître" et un
    dit "esclave". L'oscillateur maître est celui qui correspond à
    la fréquence jouée au clavier et sert à remettre la phase de
    l'oscillateur esclave à zéro chaque fois que son cycle recommence.
    En désaccordant la fréquence de l'oscillateur esclave, on peut
    donc créer des formes d'ondes inédites puisque la phase de ce
    dernier sera forcée de revenir à zéro avant d'avoir terminée
    son cycle. Cette technique génère un signal riche en harmooniques.

    Contrôles:
        Forme d'onde:
            Permet de changer la forme d'onde lue par l'oscillateur
            esclave. Une forme d'onde complexe enrichira d'autant plus
            le spectre du signal final.
        Fréquence maître en Hz:
            Fréquence de l'oscillateur maître (que l'on entend pas).
            Cet oscillateur ne sert qu'à la re-synchronisation mais
            contrôle tout de même la fréquence fondamentale du signal.
        Fréquence esclave en Hz:
            Fréquence de l'oscillateur esclave. Selon que cette
            fréquence est plus ou moins déphasée par rapport à la
            fréquence de l'oscillateur maître, la forme d'onde de
            cet oscillateur ne terminera pas son cycle
            (f_slave < f_master) ou aura le temps d'en commencer
            un nouveau avant d'être re-synchronisé
            (f_slave > f_master).
        Fondu enchaîné en ms:
            Ce paramètre permet de passer du mode "hard sync" (lorsqu'à
            0) au mode "soft sync" (plus grande que 0) en utilisant
            deux oscillateurs synchronisés et en appliquant un fondu
            enchaîné entre les deux. la re-synchronisation est
            systématiquement appliquée à l'oscillateur qui est dans
            le silence afin d'adoucir l'impact (et la quantité
            d'harmoniques) du changement de phase instantanné.

    """
    name = "08-Oscillateur synchronisé"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        wavelabel = wx.StaticText(self, -1, "Forme d'onde")
        choices = ["Sinus", "Scie 5", "Scie 15",
                   "Scie 30", "Scie 60",
                   "Carrée 5", "Carrée 15",
                   "Carrée 30", "Carrée 60",
                   "Triangle 3", "Triangle 6",
                   "Triangle 12", "Triangle 24"]
        wave = wx.Choice(self, -1, choices=choices)
        wave.SetSelection(0)
        wave.Bind(wx.EVT_CHOICE, self.setWaveform)
        sizer.Add(wavelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(wave, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        labelfr = wx.StaticText(self, -1, "Fréquence maître en Hz")
        self.fr = PyoGuiControlSlider(self, 40, 2000, 172, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeFreq)

        labelfr2 = wx.StaticText(self, -1, "Fréquence esclave en Hz")
        self.fr2 = PyoGuiControlSlider(self, 40, 2000, 200, log=True)
        self.fr2.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr2.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeSlave)

        labelfl = wx.StaticText(self, -1, "Fondu enchaîné en ms")
        self.fl = PyoGuiControlSlider(self, 0, 2, 0)
        self.fl.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fl.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeCrossfade)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfr2, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfl, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fl, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def setWaveform(self, evt):
        self.output.table = self.tables[evt.GetInt()]

    def changeFreq(self, evt):
        self.freq.value = evt.value

    def changeSlave(self, evt):
        self.slave.value = evt.value

    def changeCrossfade(self, evt):
        self.xfade.value = evt.value

    def processing(self):
        self.tables = [HarmTable(), SawTable(5), SawTable(15), SawTable(30), SawTable(60),
                      SquareTable(5), SquareTable(15), SquareTable(30), SquareTable(60),
                      TriTable(3), TriTable(6), TriTable(12), TriTable(24)]
        self.freq = SigTo(172, 0.05)
        self.slave = SigTo(200, 0.05)
        self.xfade = SigTo(0, 0.05)
        self.output = OscSync(self.tables[0], self.freq, self.slave, self.xfade)
        self.display = self.output

class AmpModModule(wx.Panel):
    """
    Module: 09-Modulation de l'amplitude
    ------------------------------------

    Ce module permet de comparer la modulation en anneaux et la modulation
    d'amplitude.

    La différence, au niveau de l'implantation, entre ces des deux types
    de modulation se situe au niveau de l'oscillateur modulant. Pour la
    modulation en anneaux, il est bipolaire (oscille entre -1 et 1),
    tandis que pour la modulation d'amplitude, il est unipolaire (oscille
    entre 0 et 1).

    Le spectre d'une modulation en anneaux consiste en la somme et la
    différence entre chaque composante du signal porteur et chaque
    composante du signal modulant.

    Le spectre d'une modulation d'amplitude présente les même composantes
    que la modulation en anneaux, en plus du signal porteur inchangé.

    Contrôles:
        Type de modulation:
            Permet de sélectionner le type de modulation désiré.
        Fréquence porteuse:
            Fréquence, en Hertz, de l'oscillateur porteur. Cet oscillateur
            est toujours bipolaire.
        Fréquence modulante:
            Fréquence, en Hertz, de l'oscillateur modulant.
        Forme d'onde de la porteuse:
            Permet de changer la forme d'onde lue par l'oscillateur porteur.
            Une forme d'onde complexe enrichira d'autant plus le spectre du
            signal final.
        Forme d'onde de la modulante:
            Permet de changer la forme d'onde lue par l'oscillateur modulant.
            Une forme d'onde complexe enrichira d'autant plus le spectre du
            signal final.

    """
    name = "09-Modulation de l'amplitude"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        typelabel = wx.StaticText(self, -1, "Type de modulation")
        choices = ["Modulation en anneaux", "Modulation d'amplitude"]
        type = wx.Choice(self, -1, choices=choices)
        type.SetSelection(0)
        type.Bind(wx.EVT_CHOICE, self.setType)
        sizer.Add(typelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(type, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        labelfr = wx.StaticText(self, -1, "Fréquence porteuse")
        self.fr = PyoGuiControlSlider(self, 40, 2000, 344, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changePortFreq)

        labelfr2 = wx.StaticText(self, -1, "Fréquence modulante")
        self.fr2 = PyoGuiControlSlider(self, 1, 2000, 172, log=True)
        self.fr2.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr2.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeModFreq)

        choices = ["Sinus", "Scie 2", "Scie 5",
                   "Scie 10", "Scie 20",
                   "Carrée 2", "Carrée 5",
                   "Carrée 10", "Carrée 20",
                   "Triangle 2", "Triangle 5",
                   "Triangle 10", "Triangle 20"]

        wavelabel = wx.StaticText(self, -1, "Forme d'onde de la porteuse")
        wave = wx.Choice(self, -1, choices=choices)
        wave.SetSelection(0)
        wave.Bind(wx.EVT_CHOICE, self.setWaveform)

        wave2label = wx.StaticText(self, -1, "Forme d'onde de la modulante")
        wave2 = wx.Choice(self, -1, choices=choices)
        wave2.SetSelection(0)
        wave2.Bind(wx.EVT_CHOICE, self.setWaveform2)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelfr2, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(wavelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(wave, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(wave2label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(wave2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def setType(self, evt):
        self.scaling.value = evt.GetInt() * 0.5

    def changePortFreq(self, evt):
        self.freq.value = evt.value

    def changeModFreq(self, evt):
        self.freq2.value = evt.value

    def setWaveform(self, evt):
        self.port.table = self.tables[evt.GetInt()]

    def setWaveform2(self, evt):
        self.mod.table = self.tables[evt.GetInt()]

    def processing(self):
        self.scaling = SigTo(0, 0.05, 0)
        self.tables = [HarmTable(), SawTable(2), SawTable(5), SawTable(10), SawTable(20),
                      SquareTable(2), SquareTable(5), SquareTable(10), SquareTable(20),
                      TriTable(2), TriTable(5), TriTable(10), TriTable(20)]
        self.freq = SigTo(344, 0.05)
        self.freq2 = SigTo(172, 0.05)
        self.mod = Osc(self.tables[0], self.freq2, mul=1-self.scaling, add=self.scaling)
        self.port = Osc(self.tables[0], self.freq)
        self.output = self.port * self.mod * 0.707
        self.display = self.output

class FreqModModule(wx.Panel):
    """
    Module: 09-Modulation de fréquence
    ----------------------------------

    Ce module permet d'explorer le potentiel de la modulation de fréquence
    selon l'algorithme de John Chaowning.

    Le spectre d'une modulation de fréquence présente la fréquence porteuse
    et une série de bandes latérales (de chaque côté de la porteuse) aux
    multiples de la fréquence modulante (P-M, P+M, P-2M, P+2M, P-3M, P+3M ...).

    Contrôles:
        Fréquence porteuse:
            Fréquence porteuse en Hertz. À cette fréquence viendra
            s'additionner le signal de l'oscillateur modulant pour
            produire la fréquence modulée de l'oscillateur porteur.
        Ratio porteuse:modulante:
            Ce ratio détermine la fréquence de l'oscillateur modulant,
            en relation avec la fréquence porteuse. La fréquence modulante
            est la fréquence porteuse divisée par le ratio. Les rapports
            d'entier donnent toujours un spectre harmonique.
        Index de modulation:
            Indique l'amplitude de l'oscillateur modulant en multiples
            de la fréquence modulante (fréquence modulante multipliée
            par index de modulation égale amplitude de l'oscillateur
            modulant). Détermine le nombre de bandes latérales (I+1)
            de chaque côté de la fréquence porteuse.
        Forme d'onde de la porteuse:
            Permet de changer la forme d'onde lue par l'oscillateur porteur.
            Une forme d'onde complexe enrichira d'autant plus le spectre du
            signal final.
        Forme d'onde de la modulante:
            Permet de changer la forme d'onde lue par l'oscillateur modulant.
            Une forme d'onde complexe enrichira d'autant plus le spectre du
            signal final.

    """
    name = "09-Modulation de fréquence"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelfr = wx.StaticText(self, -1, "Fréquence porteuse")
        self.fr = PyoGuiControlSlider(self, 40, 5000, 344, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changePortFreq)

        labelra = wx.StaticText(self, -1, "Ratio porteuse:modulante")
        self.ra = PyoGuiControlSlider(self, 0.1, 10, 1)
        self.ra.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ra.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeRatio)

        labelind = wx.StaticText(self, -1, "Index de modulation")
        self.ind = PyoGuiControlSlider(self, 0, 40, 5)
        self.ind.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ind.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeIndex)

        choices = ["Sinus", "Scie 2", "Scie 5",
                   "Scie 10", "Scie 20",
                   "Carrée 2", "Carrée 5",
                   "Carrée 10", "Carrée 20",
                   "Triangle 2", "Triangle 5",
                   "Triangle 10", "Triangle 20"]

        wavelabel = wx.StaticText(self, -1, "Forme d'onde de la porteuse")
        wave = wx.Choice(self, -1, choices=choices)
        wave.SetSelection(0)
        wave.Bind(wx.EVT_CHOICE, self.setWaveform)

        wave2label = wx.StaticText(self, -1, "Forme d'onde de la modulante")
        wave2 = wx.Choice(self, -1, choices=choices)
        wave2.SetSelection(0)
        wave2.Bind(wx.EVT_CHOICE, self.setWaveform2)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelra, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ra, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelind, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ind, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(wavelabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(wave, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(wave2label, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(wave2, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changePortFreq(self, evt):
        self.freq.value = evt.value

    def changeRatio(self, evt):
        self.ratio.value = evt.value

    def changeIndex(self, evt):
        self.index.value = evt.value

    def setWaveform(self, evt):
        self.port.table = self.tables[evt.GetInt()]

    def setWaveform2(self, evt):
        self.mod.table = self.tables[evt.GetInt()]

    def processing(self):
        self.tables = [HarmTable(), SawTable(2), SawTable(5), SawTable(10), SawTable(20),
                      SquareTable(2), SquareTable(5), SquareTable(10), SquareTable(20),
                      TriTable(2), TriTable(5), TriTable(10), TriTable(20)]
        self.freq = SigTo(344, 0.05)
        self.ratio = SigTo(1, 0.05)
        self.index = SigTo(5, 0.05)
        self.modfreq = self.freq / self.ratio
        self.modamp = self.modfreq * self.index
        self.mod = Osc(self.tables[0], self.modfreq, mul=self.modamp)
        self.port = Osc(self.tables[0], self.freq+self.mod, mul=0.707)
        self.output = self.display = self.port

class AutoModModule(wx.Panel):
    """
    Module: 09-Auto-modulation
    --------------------------

    Ce module illustre l'auto-modulation.

    L'auto-modulation consiste à moduler le pointeur de lecture d'une
    forme d'onde avec la lecture (pondérée) de la forme d'onde elle-même.
    Le résultat est équivalent à une modulation de fréquence dont le ratio
    est fixé à 1.

    freq ---> + ---> OSC ------>
              |             |
              ---<--- x <---
                      |
                    index

    Contrôles:
        Fréquence porteuse:
            Fréquence porteuse en Hertz. À cette fréquence viendra
            s'additionner le signal de sortie de l'oscillateur pour
            produire la fréquence modulée de ce même oscillateur.
        Index de modulation:
            Indique le volume du signal de sortie de l'oscillateur qui
            est additionné à la fréquence porteuse afin de moduler la
            fréquence de l'oscillateur.

    """
    name = "09-Auto-modulation"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        labelfr = wx.StaticText(self, -1, "Fréquence porteuse")
        self.fr = PyoGuiControlSlider(self, 40, 2000, 172, log=True)
        self.fr.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.fr.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changePortFreq)

        labelind = wx.StaticText(self, -1, "Index de modulation")
        self.ind = PyoGuiControlSlider(self, 0, 1, 0.1)
        self.ind.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.ind.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeIndex)

        sizer.Add(labelfr, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.fr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelind, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.ind, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def changePortFreq(self, evt):
        self.freq.value = evt.value

    def changeIndex(self, evt):
        self.index.value = evt.value

    def processing(self):
        self.table = HarmTable(size=32768)
        self.freq = SigTo(172, 0.05)
        self.index = SigTo(0.1, 0.05, mul=0.17)
        self.port = OscLoop(self.table, self.freq, feedback=self.index, mul=0.707)
        self.output = self.display = self.port

class ChebyFuncModule(wx.Panel):
    """
    Module: 10-Fonctions de Chebychev
    ---------------------------------

    Ce module permet de manipuler une fonction de transfert créée à l'aide
    des 10 premiers polynômes de Chebychev.

    Une fenêtre flottante s'affiche avec ce module afin de visualiser la 
    fonction de transfert.

    La fonction de transfert est automatiquement normalisée afin de ne jamais
    dépasser l'ambitus -1 à 1.

    Contrôles:
        Amplitudes des polynômes (T1 à T10):
            Amplitudes, entre -1 et 1, des 10 premiers polynômes de Chebychev.
            La somme de ces 10 polynômes constituent la fonction de transfert.
        Volume d'entrée:
            Volume du signal en entrée de la fonction de transfert. Ce contrôle,
            lorsque la fonction de normalisation est activée, modifie uniquement
            le spectre du signal de sortie, sans modifier l'amplitude du son.
        Activer la normalisation:
            Active/désactive la fonction de normalisation.

    """
    name = "10-Fonctions de Chebychev"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.amplist = [1.0] + [0.0] * 9

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        sizer.Add(wx.StaticText(self, -1, "Amplitudes des polynômes"), 0, 
                                wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, 5)
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        self.p1 = LabelKnob(self, " T1 ", mini=-1, maxi=1, init=1, outFunction=self.setT1)
        self.p2 = LabelKnob(self, " T2 ", mini=-1, maxi=1, init=0, outFunction=self.setT2)
        self.p3 = LabelKnob(self, " T3 ", mini=-1, maxi=1, init=0, outFunction=self.setT3)
        self.p4 = LabelKnob(self, " T4 ", mini=-1, maxi=1, init=0, outFunction=self.setT4)
        self.p5 = LabelKnob(self, " T5 ", mini=-1, maxi=1, init=0, outFunction=self.setT5)
        box1.AddMany([(self.p1, 1), (self.p2, 1), (self.p3, 1), (self.p4, 1), (self.p5, 1)])

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        self.p6 = LabelKnob(self, " T6 ", mini=-1, maxi=1, init=0, outFunction=self.setT6)
        self.p7 = LabelKnob(self, " T7 ", mini=-1, maxi=1, init=0, outFunction=self.setT7)
        self.p8 = LabelKnob(self, " T8 ", mini=-1, maxi=1, init=0, outFunction=self.setT8)
        self.p9 = LabelKnob(self, " T9 ", mini=-1, maxi=1, init=0, outFunction=self.setT9)
        self.p10 = LabelKnob(self, " T10", mini=-1, maxi=1, init=0, outFunction=self.setT10)
        box2.AddMany([(self.p6, 1), (self.p7, 1), (self.p8, 1), (self.p9, 1), (self.p10, 1)])

        labelgn = wx.StaticText(self, -1, "Volume d'entrée")
        self.gn = PyoGuiControlSlider(self, 0.01, 1, 1)
        self.gn.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.gn.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeGain)

        self.tog = wx.CheckBox(self, -1, "Activer la normalisation")
        self.tog.Bind(wx.EVT_CHECKBOX, self.activateNorm)

        sizer.Add(box1, 0, wx.EXPAND | wx.ALL, 0)
        sizer.AddSpacer(10)
        sizer.Add(box2, 0, wx.EXPAND | wx.ALL, 0)
        sizer.Add(labelgn, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.gn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(self.tog, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def onStart(self):
        self.table.view(title="Fonction de transfert")

    def onEnd(self):
        if self.table.viewFrame is not None:
            self.table.viewFrame.Destroy()
            self.table._setViewFrame(None)

    def setT1(self, value):
        self.amplist[0] = value

    def setT2(self, value):
        self.amplist[1] = value
        self.table.replace(self.amplist)

    def setT3(self, value):
        self.amplist[2] = value
        self.table.replace(self.amplist)

    def setT4(self, value):
        self.amplist[3] = value
        self.table.replace(self.amplist)

    def setT5(self, value):
        self.amplist[4] = value
        self.table.replace(self.amplist)

    def setT6(self, value):
        self.amplist[5] = value
        self.table.replace(self.amplist)

    def setT7(self, value):
        self.amplist[6] = value
        self.table.replace(self.amplist)

    def setT8(self, value):
        self.amplist[7] = value
        self.table.replace(self.amplist)

    def setT9(self, value):
        self.amplist[8] = value
        self.table.replace(self.amplist)

    def setT10(self, value):
        self.amplist[9] = value
        self.table.replace(self.amplist)

    def changeGain(self, evt):
        self.gain.value = evt.value
            
    def activateNorm(self, evt):
        self.normalize.value = evt.GetInt()

    def processing(self):
        self.normalize = SigTo(0, 0.05)
        self.gain = SigTo(1, 0.05)
        self.table = ChebyTable(size=1024)
        self.table.autoNormalize(True)
        self.look = Lookup(self.table, self.inputpanel.output*self.gain)
        self.peak = Clip(Port(PeakAmp(self.look), 0.01, 0.01), 0.01, 1)
        self.norm = self.look * (1 / self.peak)
        self.output = Interp(self.look, self.norm, self.normalize, mul=0.707)
        self.display = self.output

class DistoFuncModule(wx.Panel):
    """
    Module: 10-Algorithmes de distorsion
    ------------------------------------

    Ce module permet de comparer quatre différents algorithmes de distorsion.

    Les algorithmes possibles sont:
        - Clipping: Une coupure abrupte du signal, positif et négatif, en
                    fonction d'un seuil donné. L'amplitude du signal de sortie
                    est réajusté en le multipliant par l'inverse du seuil.
        - Redresseur d'onde: La partie négative du signal est rabattue dans
                             le positif en fonction du paramètre "drive".
                             drive = 0   : Aucune distorsion
                             drive = 0.5 : Redresseur demi-onde
                             drive = 1   : Redresseur pleine onde
        - Arctangente: Distorsion à l'aide d'une fonction arctangente.
        - Waveshaper: Une distorsion économique en temps de calcul (elle ne
                      contient pas de fonction trigonométrique) et qui offre
                      une progression intéressante de la fonction de transfert.

    Contrôles:
        Choix de la distorsion:
            Permet de choisir l'algorithme de distorsion désiré. 
        Drive:
            Quantité de distorsion appliquée au signal, varie en fonction
            de l'algorithme choisi.
        Activer le filtre passe-bas:
            Active/désactive un filtre passe-bas appliqué après la distorsion.
        Fréquence de coupure du filtre:
            Fréquence de coupure, en Hertz, du filtre passe-bas.

    """
    name = "10-Algorithmes de distorsion"
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        head = HeadTitle(self, "Source Sonore")
        sizer.Add(head, 0, wx.BOTTOM|wx.EXPAND, 5)

        self.inputpanel = InputPanel(self)
        sizer.Add(self.inputpanel, 0, wx.EXPAND)

        head = HeadTitle(self, "Interface du Module")
        sizer.Add(head, 0, wx.EXPAND)

        choices = ["Clipping", "Redresseur d'onde", "Arctangente", "Waveshaper"]

        distlabel = wx.StaticText(self, -1, "Choix de la distorsion")
        dist = wx.Choice(self, -1, choices=choices)
        dist.SetSelection(0)
        dist.Bind(wx.EVT_CHOICE, self.setDistorsion)

        labeldrv = wx.StaticText(self, -1, "Drive")
        self.drv = PyoGuiControlSlider(self, 0, 1, 0.5)
        self.drv.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.drv.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeDrive)

        self.tog = wx.CheckBox(self, -1, "Activer le filtre passe-bas")
        self.tog.Bind(wx.EVT_CHECKBOX, self.activateLowpass)

        labelcut = wx.StaticText(self, -1, "Fréquence de coupure du filtre")
        self.cut = PyoGuiControlSlider(self, 100, 20000, 5000, log=True)
        self.cut.setBackgroundColour(USR_PANEL_BACK_COLOUR)
        self.cut.Bind(EVT_PYO_GUI_CONTROL_SLIDER, self.changeCutoff)

        sizer.Add(distlabel, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(dist, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labeldrv, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.drv, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.AddSpacer(10)
        sizer.Add(self.tog, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        sizer.Add(labelcut, 0, wx.LEFT|wx.TOP, 5)
        sizer.Add(self.cut, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.SetSizer(sizer)

    def setDistorsion(self, evt):
        if evt.GetInt() == 0:
            self.distord.value = self.disto1
        elif evt.GetInt() == 1:
            self.distord.value = self.disto2
        elif evt.GetInt() == 2:
            self.distord.value = self.disto3
        elif evt.GetInt() == 3:
            self.distord.value = self.disto4

    def changeDrive(self, evt):
        self.drive.value = evt.value

    def activateLowpass(self, evt):
        self.filtered.interp = evt.GetInt()

    def changeCutoff(self, evt):
        self.cutoff.value = evt.value

    def processing(self):
        piOn4 = math.pi / 4
        self.signal = self.inputpanel.output
        self.drive = SigTo(0.5, 0.05)
        self.cutoff = SigTo(5000, 0.05)
        self.thresh = Clip((1 - self.drive), 0.01, 1)
        self.disto1 = Max(Min(self.signal, self.thresh), -self.thresh, mul=0.707/self.thresh)
        self.disto2 = self.signal * (1 - self.drive) + Abs(self.signal) * self.drive
        self.comp = self.drive * piOn4 + piOn4
        self.disto3 = Atan2(self.signal, (1 - self.drive) * math.pi, mul=1/self.comp)
        self.clipped = Clip(self.drive, 0, 0.999)
        self.k = (2 * self.clipped) / (1.0 - self.clipped)
        self.disto4 = (1 + self.k) * self.signal / (1 + self.k * Abs(self.signal))
        self.distord = Sig(self.disto1)
        self.lowpass = ButLP(self.distord, freq=self.cutoff)
        self.filtered = Interp(self.distord, self.lowpass, 0)
        self.output = self.filtered
        self.display = self.output

MODULES = [InputOnlyModule, ResamplingModule, QuantizeModule, FiltersModule,
           FixedDelayModule, VariableDelayModule, PhasingModule, TransposeModule,
           ReverbModule, PanningModule, BinauralModule, PeakRMSModule,
           EnvFollowerModule, GateModule, CompressModule, VocoderModule,
           SpectralFilterModule, CrossSynthModule, SpectralPlaybackModule,
           SpectralDelayModule, AddSynthFixModule,
           AddSynthVarModule, PulseWidthModModule, OscSyncModule, AmpModModule,
           FreqModModule, AutoModModule, ChebyFuncModule, DistoFuncModule]
