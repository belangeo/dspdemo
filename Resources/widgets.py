import math
import wx
from .constants import *
try:
    import cv2
    FOUND_CV2 = True
except:
    FOUND_CV2 = False

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
        self.SetBackgroundColour(USR_PANEL_BACK_COLOUR)
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

    def setValue(self, val):
        self.value = self.tempval = val

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

def interpFloat(t, v1, v2):
    "interpolator for a single value; interprets t in [0-1] between v1 and v2"
    return (v2 - v1) * t + v1

def tFromValue(value, v1, v2):
    "returns a t (in range 0-1) given a value in the range v1 to v2"
    if (v2 - v1) == 0:
        return 1.0
    else:
        return float(value - v1) / (v2 - v1)

def clamp(v, minv, maxv):
    "clamps a value within a range"
    if v < minv: v = minv
    if v > maxv: v = maxv
    return v

def toLog(t, v1, v2):
    return math.log10(t / v1) / math.log10(v2 / v1)

def toExp(t, v1, v2):
    return math.pow(10, t * (math.log10(v2) - math.log10(v1)) + math.log10(v1))

class LabelKnob(wx.Panel):
    def __init__(self, parent, label="", size=(60, 60), mini=0, maxi=1, init=0, 
                 log=False, integer=False, outFunction=None):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, size=size)
        self.mini = mini
        self.maxi = maxi
        self.init = init
        self.log = log
        self.integer = integer
        self.outFunction = outFunction
        sizer = wx.BoxSizer(wx.VERTICAL)
        font, pts = self.GetFont(), self.GetFont().GetPointSize()
        font.SetPointSize(pts-2)
        label = wx.StaticText(self, -1, label)
        label.SetFont(font)
        sizer.Add(label, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT, 5)
        self.knob = Knob(self, outFunction=self.knobOutput)
        if self.log:
            self.knob.setValue(toLog(self.init, self.mini, self.maxi))
        else:
            self.knob.setValue(tFromValue(self.init, self.mini, self.maxi))
        sizer.Add(self.knob, 1, wx.LEFT|wx.RIGHT, 10)
        self.display = wx.StaticText(self, -1, "0.000")
        self.display.SetFont(font)
        sizer.Add(self.display, 0, wx.EXPAND|wx.CENTER|wx.LEFT|wx.RIGHT, 5)
        self.SetSizerAndFit(sizer)

    def knobOutput(self, value):
        if self.log:
            val = toExp(value, self.mini, self.maxi)
        else:
            val = interpFloat(value, self.mini, self.maxi)
        realvalue = val

        if self.integer:
            if abs(val) >= 10000:
                val = '%d' % val
            elif abs(val) >= 100:
                if val < 0:
                    val = '%d' % val
                else:
                    val = '% 1d' % val
            elif abs(val) >= 10:
                if val < 0:
                    val = '% 1d' % val
                else:
                    val = '% 2d' % val
            elif abs(val) < 10:
                if val < 0:
                    val = '% 2d' % val
                else:
                    val = '% 3d' % val

        else:
            if abs(val) >= 1000:
                val = '%.0f' % val
            elif abs(val) >= 100:
                if val < 0:
                    val = '%.0f' % val
                else:
                    val = '%.1f' % val
            elif abs(val) >= 10:
                if val < 0:
                    val = '%.1f' % val
                else:
                    val = '%.2f' % val
            elif abs(val) < 10:
                if val < 0:
                    val = '%.2f' % val
                else:
                    val = '%.3f' % val

        self.display.SetLabel(val)
        if self.outFunction is not None:
            if self.integer:
                realvalue = int(realvalue)
            self.outFunction(realvalue)

if FOUND_CV2:
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 240)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 180)
    class ShowCapture(wx.Panel):
        def __init__(self, parent, fps=30):
            wx.Panel.__init__(self, parent)
            self.SetBackgroundColour(APP_BACKGROUND_COLOUR)

            self.capture = capture
            ret, frame = self.capture.read()

            height, width = frame.shape[:2]
            self.SetMinSize((width, height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            self.bmp = wx.Bitmap.FromBuffer(width, height, frame)

            self.timer = wx.Timer(self)
            self.timer.Start(1000./fps)

            self.Bind(wx.EVT_PAINT, self.OnPaint)
            self.Bind(wx.EVT_TIMER, self.NextFrame)


        def OnPaint(self, evt):
            dc = wx.BufferedPaintDC(self)
            dc.DrawBitmap(self.bmp, 0, 0)

        def NextFrame(self, event):
            ret, frame = self.capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.bmp.CopyFromBuffer(frame)
                self.Refresh()
else:
    class ShowCapture(wx.Panel):
        def __init__(self, parent, fps=30):
            wx.Panel.__init__(self, parent)
            self.SetBackgroundColour(APP_BACKGROUND_COLOUR)
