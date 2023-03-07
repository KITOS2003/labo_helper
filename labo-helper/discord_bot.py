import time
import multiprocessing as mp
import discord as dc
from dotenv import load_dotenv

from osciloscope import Osciloscope
from function_generator import FunctionGenerator


client = dc.Client()


@client.event
async def on_ready():
    pass


client.run()


def enqueue_log(function):
    def result(self, *args, **kwargs):
        return function()

    return result


# API
class DiscordBot:
    def __init__(self):
        self.manager = mp.Manager()
        self.attached_instruments = []
        self.discord_bot_process = None

    def attach(self, instrument):
        if type(instrument) == Osciloscope:
            self._attach_Osciloscope(instrument)
        elif type(instrument) == FunctionGenerator:
            self._attach_FunctionGenerator(instrument)
        else:
            raise Exception(
                "No se puede usar el bot de discord para trackear un {}, no es un instrumento".format(
                    instrument
                )
            )

    def run(self, token):
        load_dotenv()
        mp.Process(target=discord_bot_entry, args=(self, token))

    def _attach_Osciloscope(self, osciloscope):
        osciloscope.current_time_scale = self.manager.Value("d", 0.0)
        osciloscope.current_time_offset = self.manager.Value("d", 0.0)
        osciloscope.current_voltaje_scale = self.manager.list(None, 0.0, 0.0)
        osciloscope.current_voltaje_offset = self.manager.list(None, 0.0, 0.0)
        osciloscope.current_channel_enabled = self.manager.list(None, False, False)
        osciloscope.current_average_sample_number = self.manager.Value("i", 1)
        self.attached_instruments.append(osciloscope)

    def _attach_FunctionGenerator(self, function_generator):
        self.attached_instruments.append(function_generator)
        pass


# Interno:

client = dc.Client()


def discord_bot_entry(discord_bot_object, token):
    pass
