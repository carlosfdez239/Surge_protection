import os

class Printer:
    def __init__(self, printer_ip: str):
        self.printer_ip = printer_ip
        # En una implementación real, podrías verificar la conectividad aquí.

    def print_file(self, file_path: str):
        """
        Envía un archivo a la impresora.
        Este método es una simplificación; la implementación real dependerá
        del sistema operativo y el protocolo de impresión (ej. CUPS).
        """
        if not os.path.exists(file_path):
            print(f"Error: El archivo {file_path} no existe.")
            return False

        print(f"Imprimiendo archivo {file_path} en la impresora con IP {self.printer_ip}...")
        # Ejemplo con un comando del sistema, adaptalo a tu entorno
        # os.system(f"lpr -H {self.printer_ip} {file_path}")
        print("Impresión enviada con éxito.")
        return True