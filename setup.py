from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "Ayudante de mediciones automaticas"
LONG_DESCRIPTION = "API wrapper de py-visa que te hace la vida mas facil a la hora de programar rutinas de medicion especificamente para el generador de funciones Hantek PPS2320A y similar y los osciloscopios Tektronix de la serie TBS1000B-EDU."

setup(
    name="labo_helper",
    version=VERSION,
    author="Marcos Sidoruk",
    author_email="<marcsid2003@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["pyvisa", "numpy", "matplotlib", "colorama", "datetime"],
    keywords=["pyvisa", "osciloscope", "Tektronix"],
    classifiers=[]
)
