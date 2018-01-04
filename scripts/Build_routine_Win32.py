import os

flags = "--clean -F -c"
hidden = "--hidden-import wx.adv --hidden-import wx.html --hidden-import wx.xml"
icon = "--icon=Resources\DSPDemo_Icon.ico"
os.system('pyinstaller %s %s %s "DSPDemo.py"' % (flags, hidden, icon))

os.system("git checkout-index -a -f --prefix=DSPDemo_Win/")
os.system("copy dist\DSPDemo.exe DSPDemo_Win /Y")
os.system("rmdir /Q /S DSPDemo_Win\scripts")
os.remove("DSPDemo_Win/DSPDemo.py")
os.remove("DSPDemo_Win/.gitignore")
os.remove("DSPDemo_Win/setup.py")
os.remove("DSPDemo_Win/Resources/DSPDemo_Icon.icns")
os.remove("DSPDemo.spec")
os.system("rmdir /Q /S build")
os.system("rmdir /Q /S dist")
for f in os.listdir(os.getcwd()):
    if f.startswith("warn") or f.startswith("logdict"):
        os.remove(f)

