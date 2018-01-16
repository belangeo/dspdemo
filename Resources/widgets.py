import math
import wx
from .constants import *

class DocFrame(wx.Frame):
    def __init__(self, parent, text, size=(750, 750)):
        wx.Frame.__init__(self, parent, -1, "Documentation du module", size=size)
        panel = wx.Panel(self)
        panel.SetBackgroundColour(APP_BACKGROUND_COLOUR)
        sizer = wx.BoxSizer(wx.VERTICAL)
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP
        textctrl = wx.TextCtrl(panel, -1, text, style=style)
        sizer.Add(textctrl, 1, wx.EXPAND|wx.ALL, 5)
        panel.SetSizerAndFit(sizer)
        self.CenterOnScreen()
        self.Show()

class HeadTitle(wx.Panel):
    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent, -1)
        self.SetBackgroundColour(HEADTITLE_BACK_COLOUR)
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self, -1, title)
        label.SetForegroundColour("white")
        sizer.Add(label, 0, wx.CENTER|wx.ALL, 2)
        self.SetSizerAndFit(sizer)

class Knob(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=(26, 26), style=wx.TAB_TRAVERSAL, outFunction=None):
        wx.Panel.__init__(self, parent, id, pos, size, style)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.outFunction = outFunction
        self.twopi = math.pi * 2
        self.anchor1 = math.pi * (4.5 / 6)
        self.anchor2 = math.pi * (1.5 / 6)
        self.ancrange = self.twopi - self.anchor1 + self.anchor2
        self.startpos = None
        self.value = 0.5
        self.tempval = 0.5
        self.diff = 0
        self.inc = 0.005

    def OnLeftDown(self, evt):
        self.startpos = evt.GetPosition()
        if evt.ShiftDown():
            self.inc = 0.0001
        else:
            self.inc = 0.005
        self.CaptureMouse()

    def OnLeftUp(self, evt):
        if self.HasCapture():
            self.value = self.tempval
            self.ReleaseMouse()

    def OnMotion(self, evt):
        pos = evt.GetPosition()
        if self.HasCapture():
            vert = (pos[1] - self.startpos[1]) * -self.inc
            self.diff = (pos[0] - self.startpos[0]) * self.inc + vert
            wx.CallAfter(self.Refresh)

    def OnPaint(self, evt):
        w,h = self.GetSize()
        dc = wx.BufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        dc.SetBrush(wx.Brush("#FFFFFF", style=wx.TRANSPARENT))
        dc.SetPen(wx.Pen("#FFFFFF", width=1, style=wx.TRANSPARENT))
        dc.Clear()

        self.tempval = self.value + self.diff
        if self.tempval < 0:
            self.tempval = 0
        elif self.tempval > 1:
            self.tempval = 1
        anchor2 = self.tempval * self.ancrange + self.anchor1
        if anchor2 > (self.twopi):
            anchor2 -= self.twopi
        gc.SetBrush(wx.Brush("#FFFFFF", style=wx.TRANSPARENT))

        font = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_NORMAL)
        gc.SetFont(font, "#222222")

        path = gc.CreatePath()
        gc.SetPen(wx.Pen("#AAAAAA", 2))
        path.AddArc(w/2, h/2+2, 12, self.anchor2, self.anchor1, False)
        gc.DrawPath(path)

        path = gc.CreatePath()
        gc.SetPen(wx.Pen("#000000", 2))
        path.AddArc(w/2, h/2+2, 12, anchor2, self.anchor1, False)
        gc.DrawPath(path)

        if self.outFunction is not None:
            self.outFunction(self.tempval)
