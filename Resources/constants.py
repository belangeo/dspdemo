APP_NAME = 'DSPDemo'
APP_VERSION = '0.0.4'
APP_COPYRIGHT = 'Olivier Bélanger, 2018'

WITH_VIDEO_CAPTURE = False

SOURCE_DOC_ID = 98
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

SOURCE_DOCUMENTATION = """
    Source Sonore - Sélection du son source.

    Le menu déroulant permet de sélectionner le son source parmi
    un choix de sons de synthèse ou une lecture de fichier audio.

    # Oscillateur multiforme #

    Oscillateur permettant de sélectionner la forme d'onde parmi
    un choix de formes d'onde classiques.

    Contrôles:
        Menu déroulant:
            Choix de la forme d'onde. Les choix suivants sont
            offerts: Sinusoïde, Rampe, Dent de scie, Carrée,
            Triangle, Impulsion unipolaire, Impulsion bipolaire.
        Fréquence:
            Fréquence fondamentale du signal en Hertz.

    # Oscillateur anti-alias #

    Oscillateur dont la quantité d'harmoniques est contrôlée
    automatiquement afin qu'il n'y ait jamais de composantes
    au-dessus de la fréquence de Nyquist (peu importe la
    fréquence fondamentale).

    Contrôles:
        Fréquence:
            Fréquence fondamentale du signal en Hertz.
        Forme d'onde:
            Interpolation entre 4 types de formes d'onde.
            0.0 = train d'impulsions
            0.25 = onde en dent de scie
            0.7 = onde carrée
            1.0 = onde triangulaire
        Brillance:
            Richesse spectrale du son. À 0, le signal est
            une onde sinusoïdale tandis qu'à 1, le signal
            contient des harmoniques jusqu'à concurences
            de la fréquence de Nyquist.

    # Fichier sonore #

    Lecture d'un fichier audio mono ou stéréo (WAV ou AIFF).

    Contrôles:
        Ouvrir:
            Bouton permettant de sélectionner le fichier son à
            lire.
        Jouer:
            Démarre / arrête la lecture du son.
        Loop:
            Active le mode de lecture en boucle.
        Vitesse de lecture:
            Transposition directe (par variation de la vitesse
            de lecture) du son lu. Plus le son est lu lentement,
            plus le son est grave.

    # Générateur de bruit #

    Différents générateurs de bruit (signaux aléatoires).

    Contrôles:
        Bruit blanc: toutes les fréquences sont présentes en
                     proportion statistiquement égale.
        Bruit rose: bruit blanc atténué par une pente de -3 dB
                    par octave.
        Bruit brun: bruit blanc atténué par une pente de -6 dB
                    par octave.

    """
