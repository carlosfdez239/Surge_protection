'''
SerialDevice.py - Clase para manejar dispositivos conectados por puerto serie.
Esta clase permite establecer una conexión con un dispositivo a través de un puerto serie,
enviar comandos y recibir respuestas.

Editado por: C. Fdez
fecha: 2025-08-11
revisión: 1.0

To do:

Revision history:
- 1.0: Creación de la clase SerialDevice con métodos para conectar, enviar comandos,
        recibir respuestas y cerrar la conexión.

'''

import serial
import time

class SerialDevice:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        """Establece la conexión con el puerto serie."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Conectado al puerto {self.port} a {self.baudrate} baudios.")
            return True
        except serial.SerialException as e:
            print(f"Error de conexión: {e}")
            return False

    def send_command(self, command: str):
        """Envía un comando al dispositivo."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(command)
                print(f"Comando enviado: {command}")
                return True
            except serial.SerialException as e:
                print(f"Error al enviar comando: {e}")
                return False
        return False

    def receive_response(self, wait_for_bytes: int = 1024):
        """Lee la respuesta del dispositivo."""
        if self.ser and self.ser.is_open:
            try:
                # Esperar a que haya datos disponibles
                time.sleep(0.1)
                response = self.ser.read(self.ser.in_waiting or wait_for_bytes)
                response_str = response.decode('utf-8', errors='ignore').strip()
                print(f"Respuesta recibida: {response_str}")
                return response_str
            except serial.SerialException as e:
                print(f"Error al recibir respuesta: {e}")
                return None
        return None

    def close(self):
        """Cierra la conexión serial."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Conexión serial cerrada.")