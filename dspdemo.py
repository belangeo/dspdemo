import wx
from Resources.constants import *
from Resources.mainframe import MainFrame
from Resources.splash import DSPDemoSplashScreen

if __name__ == "__main__":
    app = wx.App(False)
    mainFrame = MainFrame(None, title='DSP Demo')
    mainFrame.Show()
    sp = DSPDemoSplashScreen(None)
    app.MainLoop()
