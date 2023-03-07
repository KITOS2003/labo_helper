import pyvisa as pv

from logger import Logger
from utils import assert_ch


class FunctionGenerator:
    def __init__(
        self, rm: pv.ResourceManager, keystring, logger=None, exact_match=False
    ):
        ls = rm.list_resources()
        for s in ls:
            if s == keystring or (keystring in s and exact_match is False):
                resource_name = s
        self._name = resource_name
        self.attached_dc_bot = None
        if logger is None:
            self._logger = Logger()
        else:
            self._logger = logger
        try:
            self._inst = rm.open_resource(resource_name)
        except:
            self._logger.error(
                "Conexion con el generador de funciones fallida",
                "nombre del instrumento {}".format(resource_name),
            )
            return None
        else:
            self._logger.success(
                "Conexion con el generador de funciones establecida",
                "nombre del instrumento {}".format(resource_name),
            )
        self._idn = self._inst.query("*IDN?")
        self.current_shape = [None, "", ""]
        self.current_frequency = [None, 0, 0]
        self.current_voltaje = [None, 0, 0]
        self.current_output_state = [None, False, False]
        self.current_offset = [None, 0, 0]
        self.shapes = ["SIN", "SQU", "RAMP"]
        self.update_state()

    def set_shape(self, channel, shape):
        assert_ch(channel)
        self._inst.write("SOUR{}:FUNC:SHAP {}".format(channel, shape))
        self.current_shape[channel] = shape
        self._logger.message(
            "{} Forma emitida por el canal {} establecida en {}".format(
                self._name, channel, shape
            )
        )

    def set_frequency(self, channel, frequency):
        assert_ch(channel)
        self._inst.write("SOUR{}:FREQ {}".format(channel, frequency))
        self.current_frequency[channel] = frequency
        self._logger.message(
            "{} Frecuencia de emision del canal {} fijada a {}".format(
                self._name, channel, frequency
            )
        )

    def set_voltaje(self, channel, voltaje):
        assert_ch(channel)
        self._inst.write("SOUR{}:FUNC:VOLT {}".format(channel, voltaje))
        self.current_voltaje[channel] = voltaje
        self._logger.message(
            "{} Tension de emision del canal {} fijado a {}".format(
                self._name, channel, voltaje
            )
        )

    def set_offset(self, channel, offset):
        assert_ch(channel)
        self._inst.write("SOUR{}:FUNC:VOLT:OFFS {}".format(channel, offset))
        self.current_offset[channel] = offset
        self._logger.message(
            "{} Offset DC del canal {} fijado a {}".format(self._name, channel, offset)
        )

    def toggle_channel(self, channel, output_state):
        assert_ch(channel)
        if output_state:
            on_off = "ON"
        else:
            on_off = "OFF"
        self._inst.write("OUTP{}:STAT {}".format(channel, on_off))
        self.current_output_state[channel] = output_state
        self._logger.message(
            "{} Estado del canal {} fijado a {}".format(self._name, channel, on_off)
        )
