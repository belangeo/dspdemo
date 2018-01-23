APP_NAME = 'DSPDemo'
APP_VERSION = '0.0.3'
APP_COPYRIGHT = 'Olivier Bélanger, 2018'

WITH_VIDEO_CAPTURE = False

MODULE_DOC_ID = 99
MODULE_FIRST_ID = 100

APP_BACKGROUND_COLOUR = "#CCCCD0"
USR_PANEL_BACK_COLOUR = "#DDDDE0"
HEADTITLE_BACK_COLOUR = "#9999A0"

WINCHOICES = ["Rectangular", "Hamming", "Hanning", "Bartlett", 
              "Blackman 3-term", "Blackman-Harris 4", 
              "Blackman-Harris 7", "Tuckey", "Half-sine"]
SIZECHOICES = ["64", "128", "256", "512", "1024", "2048", "4096", "8192"]

AUDIO_NCHNLS = 2
AUDIO_BUFSIZE = 512
if WITH_VIDEO_CAPTURE:
    AUDIO_DUPLEX = 1
else:
    AUDIO_DUPLEX = 0
