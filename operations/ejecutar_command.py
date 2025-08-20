'''
EjecutarCommand: Clase para ejecutar comandos en un dispositivo serial.
Esta clase permite enviar un comando a un dispositivo conectado por puerto serie,
esperar una respuesta y procesarla. 

Editado por: C. Fdez
fecha: 2025-08-11
revisión: 1.0   

to do:

revision history:
- 1.0: Creación de la clase EjecutarCommand con métodos para ejecutar comandos
        y procesar respuestas.

'''
class EjecutarCommand:
    def __init__(self, command, expected_response, device_serial):
        self.command = command
        self.expected_response = expected_response
        self.device_serial = device_serial

    def execute(self):
        print(f"Iniciando operación: Ejecutar comando '{self.command}'...")
        # Lógica para usar self.device_serial para enviar el comando y leer la respuesta
        
        
        self.device_serial.send_command(self.command)
        response = self.device_serial.receive_response()
        print(f"Respuesta recibida: {response}")

        self.unit_response = response.strip().split('\n')
        print(f"Respuesta procesada: {self.unit_response}")
        return self.unit_response