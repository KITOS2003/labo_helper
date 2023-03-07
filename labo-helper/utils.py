import numpy as np


class InstrumentException(Exception):
    def __init__(self, msg):
        pass


def assert_ch(channel):
    assert channel in (1, 2), "No existe el canal {}".format(channel)


def find_closest(array: np.ndarray, value):
    return array[np.abs(array - value).argmin()]


def unpack_8bit(bitfield_8):
    result = []
    for i in range(8):
        if bitfield_8 & 2**i != 0:
            result.append(True)
        else:
            result.append(False)
    return result
