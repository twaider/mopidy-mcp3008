import os
import pykka
import time
import traceback
import RPi.GPIO as GPIO
import logging

from threading import Thread
from mopidy import core, exceptions

logger = logging.getLogger(__name__)

# Adapted from https://gist.github.com/ladyada/3151375
class Mcp3008(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(Mcp3008, self).__init__()
        self.core = core
        self.running = False
        self.adc_chan_vol = config['mcp3008']['adc_chan_vol']
        self.deadzone_vol_lo = config['mcp3008']['deadzone_vol_lo']
        self.deadzone_vol_hi = config['mcp3008']['deadzone_vol_hi']
        self.gpio_spics = config['mcp3008']['gpio_spics']
        self.gpio_spiclk = config['mcp3008']['gpio_spiclk']
        self.gpio_spimiso = config['mcp3008']['gpio_spimiso']
        self.gpio_spimosi = config['mcp3008']['gpio_spimosi']

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_spiclk, GPIO.OUT)
        GPIO.setup(self.gpio_spics, GPIO.OUT)
        GPIO.setup(self.gpio_spimiso, GPIO.IN)
        GPIO.setup(self.gpio_spimosi, GPIO.OUT)

    def read_adc(self, channel):
        GPIO.setmode(GPIO.BCM)
        if ((channel > 7) or (channel < 0)):
           return -1
        GPIO.output(self.gpio_spics, True)
        GPIO.output(self.gpio_spiclk, False)
        GPIO.output(self.gpio_spics, False)

        dout = channel
        dout |= 0x18
        dout <<= 3
        for i in range(5):
            if (dout & 0x80):
                GPIO.output(self.gpio_spimosi, True)
            else:
                GPIO.output(self.gpio_spimosi, False)
            dout <<= 1
            GPIO.output(self.gpio_spiclk, True)
            GPIO.output(self.gpio_spiclk, False)

        din = 0
        for i in range(12):
            GPIO.output(self.gpio_spiclk, True)
            GPIO.output(self.gpio_spiclk, False)
            din <<= 1
            if (GPIO.input(self.gpio_spimiso)):
                din |= 0x1

        GPIO.output(self.gpio_spics, True)
        din >>= 1
        return din

    # Fix this. Always returns new_max? Check calc for new_value.
    def remap(self, old_value, old_min, old_max, new_min, new_max):
        old_range = old_max - old_min
        new_range = new_max - new_min
        if (old_range == 0):
            new_value = new_min
        else:
            new_value = (((old_value - old_min) * new_range) / old_range) + new_min

        if (new_value > new_max):
            new_value = new_max
        elif (new_value < new_min):
            new_value = new_min
        new_value = int(round(new_value))

        return new_value

    def start_thread(self):
        volume_last = 0
        volume_new  = 0
        volume_jitter = 5
	
	try:
	    state_last = self.read_adc(1)
            state_normal = self.remap(state_last, 0, 1023, 0, 6)
	    #self.core.playlists.get_uri_schemes()
	    #logger.warning()
	    if (state_normal < 4):
	        state_normal = 0
	    elif (state_normal > 3):
	        state_normal = 1

	    state = state_normal
	    not_playing = 1
	except:
	    traceback.print_exc()

        while self.running:
            time.sleep(0.2)
            try:
                volume_raw = self.read_adc(self.adc_chan_vol)
                volume_new = self.remap(volume_raw, 0, 1023, 0 - self.deadzone_vol_lo, 100 + self.deadzone_vol_hi)

                if (volume_new < 0):
                    volume_new = 0
                elif (volume_new > 100):
                    volume_new = 100
                if (abs(volume_new - volume_last) > volume_jitter):
                    self.core.mixer.set_volume(volume_new)
                    volume_last = volume_new

		pin1_raw = self.read_adc(1)
		pin1 = self.remap(pin1_raw, 0, 1023, 0, 6)

		if (pin1 < 4):
		    pin1 = 0
		elif (pin1 > 3):
		    pin1 = 1		

		if (pin1 != state):
		    state = pin1
		
      	            if (state == 1):
		        self.core.playback.play()
		    elif (state == 0):
		        self.core.playback.stop()

		#logger.warning(state)
            except:
                traceback.print_exc()

    def on_start(self):
        try:
            self.running = True
            thread = Thread(target=self.start_thread)
            thread.start()
        except:
            traceback.print_exc()
            GPIO.cleanup()

    def on_stop(self):
        self.running = False
        GPIO.cleanup()
