import os
import sys
from pyo import pa_get_devices_infos, pa_get_default_devices_from_host

def dump_func(arg):
    pass

def audio_config():
    host = None

    if "DSP_DEMO_AUDIO_HOST" in os.environ:
        host = os.environ["DSP_DEMO_AUDIO_HOST"]
        # validate host...
        if sys.platform.startswith("win"):
            if host not in ["mme", "directsound", "asio", "wasapi", "wdm-ks"]:
                host = None
        elif sys.platform.startswith("linux"):
            if host not in ["alsa", "oss", "pulse", "jack"]:
                host = None
        else:
            if host not in ["core audio", "jack", "soundflower"]:
                host = None

    if host is None:
        if sys.platform.startswith("win"):
            host = "wasapi"
        elif sys.platform.startswith("linux"):
            host = "alsa"
        else:
            host = "core audio"

    indev, outdev = pa_get_default_devices_from_host(host)

    inputs, outputs = pa_get_devices_infos()

    sr = outputs[outdev]["default sr"]

    return sr, outdev
