import numpy as np
import matplotlib.pyplot as plt
import pyvisa as pv
import os

from colorama import Fore, Back, Style

import time
import datetime

class InstrumentException(Exception):
    pass

def assert_ch(channel):
    assert channel in (1, 2), "No existe el canal {}".format(channel)

def find_closest(array : np.ndarray, value):
    return array[np.abs(array - value).argmin()]

def unpack_8bit(bitfield_8):
    result = []
    for i in range(8):
        if bitfield_8 & 2**i != 0:
            result.append(True)
        else: 
            result.append(False)
    return result

class Logger:
    def __init__(self, save_path = ""):
        self._initial_time = time.time()
        self._log = []
        self._save_path = save_path
        if save_path != "":
            self.file = open(self._save_path, "w")

    def get_time(self):
        time_str = str(datetime.timedelta(seconds=time.time()-self._initial_time))
        if time_str.find(".") != -1:
            time_str=time_str[:time_str.find(".")]
        return time_str

    def error(self, head, msg):
        head = "{} ERR: {}".format(self.get_time(), head)
        print(Fore.BLACK+Back.RED, end='')
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.RED, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head+"\n"+msg+"\n")

    def warning(self, head, msg):
        head = "{} WARN: {}".format(self.get_time(), head)
        print(Fore.BLACK+Back.YELLOW, end='')
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.YELLOW, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head+"\n"+msg+"\n")
     
    def success(self, head, msg):
        head = "{}: {}".format(self.get_time(), head)
        print(Fore.BLACK+Back.GREEN, end='')
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.GREEN, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head+"\n"+msg+"\n")

    def message(self, msg):
        msg = "{} MSG: {}".format(self.get_time(), msg)
        print(msg)
        self._log.append(msg+"\n")

    def __del__(self):
        if self._save_path != "":
            for msg in self._log:
                self.file.write(msg)

class Osciloscope:
    def __init__(self, rm : pv.ResourceManager, keystring, exact_match = False, logger = None):
        self.possible_voltaje_scales = np.array(('0.002','0.005','0.01','0.02','0.05','0.1',
                                                 '0.2',  '0.5',  '1.0', '2.0', '5.0'))
        self.possible_time_scales = np.array(('5e-09','1e-08', '2.5e-08','5e-08', '1e-07','2.5e-07',
                                              '5e-07','1e-06', '2.5e-06','5e-06', '1e-05','2.5e-05',
                                              '5e-05','0.0001','0.00025','0.0005','0.001','0.0025',
                                              '0.005','0.01',  '0.025',  '0.05',  '0.1',  '0.25',
                                              '0.5',  '1.0',   '2.5',    '5.0',   '10.0', '25.0','50.0'))
        if logger == None:
            self._logger = Logger()
        else:
            self._logger = logger
        ls = rm.list_resources()
        for s in ls:
            if s == keystring or (keystring in s and exact_match == False):
                resource_name = s
        self._name = resource_name
        try:
            self._inst = rm.open_resource(resource_name)
        except:
            self._logger.error("Conexion con el osciloscopio fallida", "Nombre del instrumento: {}".format(self._name))
            return None
        else:
            self._idn = self._inst.query("*IDN?")
            self.osc.write('DAT:ENC RPB')
            self.osc.write('DAT:WID 1')
            self.current_time_scale = 0
            self.current_time_offset = 0
            self.current_voltaje_scale = [ None, 0, 0 ]
            self.current_voltaje_offset = [ None, 0, 0 ]
            self.current_channel_enabled = [ None, False, False ]
            self.current_average_sample_number = 1
            for i in [1, 2]:
                self._inst.write("CH{}:PROB 1".format(i))
                self._inst.write("CH{}:INV OFF".format(i))
            self.update_state()
            self._logger.success("Conexion con el osciloscopio exitosa", "Conectado con el dispositivo {}\nIdentificacion: {}".format(self._name, self._idn))
    
    def __str__(self, error_msg):
        print(self._name + "\n" + self._idn)

    def error_check(self):
        error = int(self._inst.query("*ESR?"))
        error = unpack_8bit(error_list)[2:6]
        if any(error) == True:
            self._logger.error(self._name+" "+error_msg, "")
            error_msg = self._inst.query("ALLEV?")
            self._logger.error("LOG DEL OSCILOSCOPIO:", error_msg)
            raise InstrumentException()

    def update_state(self):
        """Obtener la configuracion actual del osciloscopio y actualizar las variables internas"""
        self.current_time_scale = float(self._inst.query("HOR:MAI:SCA?"))
        self.current_time_offset = float(self._inst.query("HOR:MAI:POS?"))
        for i in range(1, 3):
            self.current_voltaje_scale[i] = float(self._inst.query("CH{}:SCA?".format(i)))
            self.current_voltaje_offset[i] = float(self._inst.query("CH{}:POS?".format(i)))
            if self._inst.query("SELECT:CH{}?".format(i)) in [ "1", "ON" ]:
                self.current_channel_enabled[i] = True
            else:
                self.current_channel_enabled[i] = False
        mode = self._inst.query("ACQ:MODE?")
        if mode == "SAMPLE":
            self.current_average_sample_number = 1
        elif mode == "AVERAGE":
            self.current_average_sample_number = int(self._inst.query("ACQ:NUMAVG?"))
        else:
            raise InstrumentException("El osciloscopio se encuentra en modo raro")
        self.error_check("Error al leer el estado del osciloscopio")

    def toggle_channel(channel, on_off):
        if on_off == True or on_off == "on":
            cmd_str="ON"
            state = True
        elif on_off == False or on_off == "off":
            cmd_str="OFF"
            state = False
        self._inst.write("SELECT:CH{} {}".format(channel, cmd_str))
        try:
            self.error_check("Error al cambiar el estado del canal {} del osciloscopio a \"{}\"".format(channel, cmd_str))
        except:
            raise InstrumentException()
        else:
            self.current_channel_enabled[channel] = state
            self._logger.msg("{} Estado del canal {} del osciloscopio cambiado a \"{}\"".format(self._name, channel, cmd_str))

    def set_average(self, avg_number):
        possible_average_numbers = [ 1, 4, 16, 64, 128 ]
        assert avg_number in possible_average_numbers, "Numero de samples a promediar incorrecto, debe ser 1, 4, 16, 64 o 128"
        if avg_number == 1:
            self._inst.write("ACQ:MODE:SAMPLE")
        else:
            self._inst.write("ACQ:MODE:AVERAGE")
            self._inst.write("ACQ:NUMAVG {}".format(avg_number))
        try: 
            self.error_check("Error al cambiar el numero de samples a promediar")
        except:
            raise InstrumentException()
        else:
            self.current_average_sample_number = avg_number
            self._logger.msg("Numero de samples a promediar fijado en {}".format(avg_number))
    
    def set_trigger_source(self, channel):
        assert_ch(channel)
        self._inst.write("TRIG:MAI:EDGE:SOU CH{}".format(channel))

    def set_trigger_slope(self, raise_fall):
        if raise_fall in ("raise", True, 1):
            str = "raise"
        elif raise_fall in ("fall", False, 0):
            str = "fall"
        else:
            self._logger.error("{} Error al cambiar la pendiente del trigger".format(self._name), "\"{}\" no es un parametro valido, los parametros validos son \"raise\" y \"fall\"".format(raise_fall))
            return
        self._inst.write("TRIG:MAI:EDGE:SLO {}".format(str))
        self.error_check("Error al cambiar la pendiente del trigger")

    def set_time_scale(self, scale, index_input = False):
        if index_input:
            scale = self.possible_time_scales[scale]
        else:
            scale = find_closest(self.possible_time_scales, scale)
        self._inst.write("HOR:MAI:SCA {}".format(scale))
        try: 
            self.error_check("Error al cambiar la escala de tiempo del osciloscopio")
        except:
            raise InstrumentException()
        else:
            self.current_time_scale = scale
            self._logger.message("{} Escala temporal del osciloscopio fijada en {}".format(self._name, scale))

    def set_time_offset(self, offset):
        self._inst.write("HOR:MAI:SCA {}".format(offset))
        if self.error_check():
            self._logger.error("Error al cambiar el offset temporal del osciloscopio", "")
        else:
            self.current_time_offset = offset
            self._logger.message("Offset temporal del osciloscopio fijado en {}".format(scale))

    def set_voltaje_scale(self, channel, scale, index_input = False):
        assert_ch(channel)
        if index_input:
            scale = self.possible_voltaje_scales[scale]
        else:
            scale = find_closest(self.possible_voltaje_scales, scale)
        self._inst.write("CH{}:SCA {}".format(channel, scale))
        if self.error_check():
            self._logger.error("Error al cambiar la escala del canal {} del osciloscopio".format(channel), "")
        else:
            self.current_voltaje_scale[channel] = scale
            self._logger.message("Escala del canal {} del osciloscopio fijado en {}".format(channel, scale))

    def set_voltaje_offset(self, channel, offset):
        assert_ch(channel)
        self._inst.write("CH{}:POS {}".format(channel, offset))
        if self.error_check():
            self._logger.error("Error al cambiar el offset del canal {} del osciloscopio".format(channel), "")
        else:
            self.current_voltaje_offset[channel] = offset
            self._logger.message("Offset del canal {} del osciloscopio fijado en {}".format(channel, scale))

    def autoset(self):
        self._inst.write("AUTOSET EXECUTE")
        self._inst.query("*OPC?")
        if self.error_check():
            self._logger.error("Error al ejecutar el autoset", "")
        self.update_state()

    def aquire_data(self, root_dir_path):
        dir_index = 0
        while True:
            dir_path = root_dir_path+"osc_measurement_{}/".format(dir_index)
            if os.path.isdir(dir_path):
                continue
            else:
                break
        os.mkdir(dir_path)
        plt.figure(1)
        plt.grid("on")
        plt.xlabel("Tiempo [s]")
        plt.ylabel("Tension [V]")
        with open(dir_path+"config", "w") as file:
            try:
                self._logger.message("Leyendo datos del osciloscopio...")
                for i in [1, 2]:
                    file.write("----------------------------------\nCHANNEL {}:".fotmat(i))
                    if current_channel_enabled[i]:
                        # Indicamos de que canal queremos extraer los datos
                        self._inst.write("DAT:SOU CH{}".format(i))
                        # extraemos los datos
                        data = self.query_binary_values("CURV?", datatype="B", container=np.array)
                        time_increment  = float(self._inst.query("WFMP:XINCR"))
                        time_zero = float(self._inst.query("WFMP:XZERO"))
                        voltaje_scale = float(self._inst.query("WFMP:YMULT"))
                        voltaje_zero = float(self._inst.query("WFMP:YZERO"))
                        voltaje_offset = float(self._inst.query("WFMP:YOFF"))
                        if self.error_check() == True:
                            raise
                        # escribimos la configuracion del osciloscopio en el archivo de configuracion
                        file.write(" ENABLED\n")
                        file.write("time_increment {}\n".format(time_increment))
                        file.write("time_zero      {}\n".format(time_zero))
                        file.write("voltaje_scale  {}\n".format(voltaje_scale))
                        file.write("voltaje_offset {}\n".format(voltaje_offset))
                        file.write("voltaje_zero   {}\n".format(voltaje_zero))
                        # y despues los datos propiamente dichos en un archivo separado
                        with open(dir_path+"data_ch{}".format(i)) as data_file:
                            voltaje_medido = (data - voltaje_offset)*voltaje_scale + voltaje_zero
                            tiempo_medido  = np.arange(time_zero, time_zero + time_increment*len(voltaje_medido), time_increment)
                            for x in zip(tiempo_medido, voltaje_medido):
                                data_file.write("{}, {}".format(x[0], x[1]))
                        # Como bonus un plot
                        ch_colors = { 1: "orange", 2: "blue" }
                        plt.plot(tiempo_medido, voltaje_medido, color=ch_colors[i] )
                    else:
                        file.write(" DISABLED\n")
                plt.savefig(dir_path+"figure.pdf")
                plt.clf()
            except:
                self._logger.error("Medicion fallida", "")
            else:
                self._logger.success("Medicion exitosa", "Datos guardados en {}".format(dir_path))


class FunctionGenerator:
    def __init__(self, rm : pv.ResourceManager, keystring, logger=None, exact_match = False):
        ls = rm.list_resources()
        for s in ls:
            if s == keystring or (keystring in s and exact_match == False):
                resource_name = s
        self._name = resource_name
        if logger == None:
            self._logger = Logger()
        else:
            self._logger = logger
        try:
            self._inst = rm.open_resource(resource_name)
        except:
            self._logger.error("Conexion con el generador de funciones fallida", "nombre del instrumento {}".format(resource_name))
            return None
        else:
            self._logger.success("Conexion con el generador de funciones establecida", "nombre del instrumento {}".format(resource_name))
        self._idn = self._inst.query("*IDN?")
        self.current_shape = [ None, "", "" ]
        self.current_frequency = [ None, 0, 0 ]
        self.current_voltaje = [ None, 0, 0 ]
        self.current_output_state = [ None, False, False ]
        self.current_offset = [ None, 0 , 0 ]
        self.shapes = [ 'SIN', 'SQU', 'RAMP' ]
        self.update_state()
            
    def set_shape(self, channel, shape):
        assert_ch(channel)
        self._inst.write('SOUR{}:FUNC:SHAP {}'.format(channel, shape))   
        self.current_shape[channel] = shape
        self._logger.message("{} Forma emitida por el canal {} establecida en {}".format(self._name, channel, shape))

    def set_frequency(self, channel, frequency):
        assert_ch(channel)
        self._inst.write("SOUR{}:FREQ {}".format(channel, frequency))
        self.current_frequency[channel] = frequency
        self._logger.message("{} Frecuencia de emision del canal {} fijada a {}".format(self._name, channel, frequency))

    def set_voltaje(self, channel, voltaje):
        assert_ch(channel)
        self._inst.write("SOUR{}:FUNC:VOLT {}".format(channel, voltaje))
        self.current_voltaje[channel] = voltaje
        self._logger.message("{} Tension de emision del canal {} fijado a {}".format(self._name, channel, voltaje))
    
    def set_offset(self, channel, offset):
        assert_ch(channel)
        self._inst.write("SOUR{}:FUNC:VOLT:OFFS {}".format(channel, offset))
        self.current_offset[channel] = offset
        self._logger.message("{} Offset DC del canal {} fijado a {}".format(self._name, channel, offset))

    def set_output_state(self, channel, output_state):
        assert_ch(channel)
        if output_state:
            on_off = "ON"
        else:
            on_off = "OFF"
        self._inst.write("OUTP{}:STAT {}".format(channel, on_off))
        self.current_output_state[channel] = output_state
        self._logger.message("{} Estado del canal {} fijado a {}".format(self._name, channel, on_off))

rm = pv.ResourceManager()
osc = Osciloscope(rm, "ASRL3:")

