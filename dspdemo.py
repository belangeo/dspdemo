import wx
from Resources.mainframe import MainFrame
from Resources.splash import DSPDemoSplashScreen

def onStart():
    mainFrame = MainFrame(None, title='DSP Demo')
    app.SetTopWindow(mainFrame)

if __name__ == "__main__":
    app = wx.App(False)
    sp = DSPDemoSplashScreen(None, callback=onStart)
    app.MainLoop()

# video compression:
# ffmpeg -i 01_echantillonnage.mkv -vcodec libx264 -crf 28 01_echantillonnage_crf28.mkv