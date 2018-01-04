import wx
from Resources.constants import *
from Resources.mainframe import MainFrame
from Resources.splash import DSPDemoSplashScreen

def onStart():
    mainFrame = MainFrame(None, title='DSP Demo')
    app.SetTopWindow(mainFrame)

if __name__ == "__main__":
    app = wx.App(False)
    sp = DSPDemoSplashScreen(None, callback=onStart)
    app.MainLoop()
