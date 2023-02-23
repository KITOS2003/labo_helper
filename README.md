Labo-helper
-----------

API wrapper de py-visa que te hace la vida mas facil a la hora de programar rutinas de medicion especificamente para el generador de funciones Hantek PPS2320A, los osciloscopios Tektronix de la serie TBS1000B-EDU y similar.

Actualmente es un trabajo en progreso y varias cosas pueden no funcionar.

Dependencias:
-------------

pyvisa

numpy

matplotlib

colorama

datetime

Uso:
----

Es recomendable que una vez conectados los instrumentos primero abras un interprete de python y corras el siguiente codigo

```python
import pyvisa
pyvisa.ResourceManager().list_resources() # NOTA: si usas un backend distinto tenelo en cuenta
```

El output de eso deberia darte una lista de los nombres que pyvisa le da a los instrumentos conectados, identifica que nombres corresponden a los instrumentos conectados. Para establecer la conexion podes usar el nombre completo de los instrumentos pero tambien podes usar un pedazo que los identifique de manera inequivoca, por ejemplo si se tiene [ INST::LINDO::4629, INST::FEO::7621 ], "LINDO" y "FEO" basta para identificar a los instrumentos

Luego en el script en el que quieras escribir tu rutina de medicion empeza por escribir:

```python
import pyvisa as pv # necesario para que puedas elejir el backend de pyvisa a utilizar
from labo_helper import FunctionGenerator
from labo_helper import Osciloscope

rm = pv.ResourceManager() # Aca podes elejir el backend

# NOTA: si en vez de usar una palabra clave queres usar si o si el nombre exacto del instrumento,
# a las lineas de abajo les podes poner como argumento extra exact_match = True
fg = FunctionGenerator(rm, "FEO") 
osc = Osciloscope(rm, "LINDO")
```
Si la comunicacion con los instrumentos se da con exito y el codigo de arriba corre sin excepciones ya podes empezar a escribir tus rutinas utilizando los metodos de ambas clases.
Ej. Barrido de frecuencias sencillo:

```python
fg.set_shape(1, "SIN") # Que el canal 1 del generador emita sinusoidales
fg.set_voltaje(1, 5.0) # Que el canal 1 del generador emita 5Vpp
fg.set_output_state(1, True) # Encender el canal 1

import numpy as np
frecuencias = np.linspace(0, 1000, 100)
for frec in frecuencias:
    fg.set_frequency(1, frec) # fijar la frecuencia del canal 1
    osc.autoset() # Autoset del osciloscopio, hace todo mas lento pero bueno
    osc.aquire_data("/home/mi_usuario/labo/mediciones") # que el osciloscopio mida y guarde todo en esa carpeta
```
