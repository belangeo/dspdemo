import sys
import wx
from .constants import *
from .images import DSPDemo_Icon

def GetRoundBitmap(w, h, r):
    maskColour = wx.Colour(0, 0, 0)
    shownColour = wx.Colour(5, 5, 5)
    b = wx.EmptyBitmap(w, h)
    dc = wx.MemoryDC(b)
    dc.SetBrush(wx.Brush(maskColour))
    dc.DrawRectangle(0, 0, w, h)
    dc.SetBrush(wx.Brush(shownColour))
    dc.SetPen(wx.Pen(shownColour))
    dc.DrawRoundedRectangle(0, 0, w, h, r)
    dc.SelectObject(wx.NullBitmap)
    b.SetMaskColour(maskColour)
    return b

def GetRoundShape(w, h, r):
    return wx.Region(GetRoundBitmap(w, h, r))

class DSPDemoSplashScreen(wx.Frame):
    def __init__(self, parent, callback):
        display = wx.Display(0)
        size = display.GetGeometry()[2:]
        st = wx.FRAME_SHAPED|wx.BORDER_SIMPLE|wx.FRAME_NO_TASKBAR|wx.STAY_ON_TOP
        wx.Frame.__init__(self, parent, -1, "", pos=(-1, size[1]//6), style=st)

        self.callback = callback

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.bmp = DSPDemo_Icon.GetBitmap()
        self.w, self.h = self.bmp.GetWidth(), self.bmp.GetHeight()
        self.SetClientSize((self.w, self.h))

        if wx.Platform == "__WXGTK__":
            self.Bind(wx.EVT_WINDOW_CREATE, self.SetWindowShape)
        else:
            self.SetWindowShape()

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)

        wx.CallLater(2000, self.OnClose)

        self.Center(wx.HORIZONTAL)
        if sys.platform == 'win32':
            self.Center(wx.VERTICAL)

        wx.CallAfter(self.Show)

    def SetWindowShape(self, *evt):
        r = GetRoundShape(self.w, self.h, 256)
        self.SetShape(r)

    def OnPaint(self, evt):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen("#000000"))
        dc.SetBrush(wx.Brush("#000000"))
        dc.DrawRectangle(0, 0, w, h)
        dc.DrawBitmap(self.bmp, 0, 0, True)
        dc.SetTextForeground("#333333")
        dc.DrawLabel("%s v%s" % (APP_NAME, APP_VERSION), wx.Rect(70,380,200,15))
        dc.DrawLabel(APP_COPYRIGHT, wx.Rect(70, 400, 200, 15))

    def OnClose(self):
        self.callback()
        self.Destroy()
