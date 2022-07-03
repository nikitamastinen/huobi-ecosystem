from pysinewave import SineWave
from time import sleep

sinewave = SineWave(pitch=12)
sinewave.play()
sleep(1)
sinewave.stop()
