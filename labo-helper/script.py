import pyvisa as pv
from osciloscope import Osciloscope
from function_generator import FunctionGenerator
import numpy as np
import time

rm = pv.ResourceManager("@py")
osc = Osciloscope(rm, "C017159")
fg = FunctionGenerator(rm, "")

tensiones = np.linspace(-1, 1, 20)

fg.set_shape(1, "SQU")
fg.set_voltaje(1, 0)
fg.toggle_channel(1, True)

for t in tensiones:
    fg.set_offset(1, t)
    time.sleep(1)
