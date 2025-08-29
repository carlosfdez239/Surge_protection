'''
Uso:  
from usb_scanner import USBDeviceScanner

scanner = USBDeviceScanner()
devices = scanner.scan()

for d in devices:
    print(d["ttyUSB"], d["idVendor"], d["serial"])

Creado: C. Fdez
Fecha: 29/08/2025

Rev: 0
Fecha: 29/08/2025

Bugs:
[]

Revision history:


To do:



'''
import glob
import subprocess
import re

class USBDeviceScanner:
    """
    Escanea los dispositivos ttyUSB conectados y devuelve información
    relevante (idVendor, idProduct, serial short).
    """

    def __init__(self):
        self.dispositivos = []

    def scan(self):
        """Escanea /dev/ttyUSB* y guarda la info en self.dispositivos"""
        self.dispositivos.clear()
        for path in glob.glob("/dev/ttyUSB*"):
            nombre_dispositivo = path.split("/")[-1]
            info = self._get_device_info(nombre_dispositivo)
            if info:
                self.dispositivos.append(info)
        return self.dispositivos

    def _get_device_info(self, ttyusb):
        """
        Obtiene la info de un dispositivo mediante `udevadm info`.
        """
        try:
            resultado = subprocess.run(
                ["udevadm", "info", f"/dev/{ttyusb}"],
                stdout=subprocess.PIPE,
                text=True,
                stderr=subprocess.DEVNULL
            )
            if resultado.returncode != 0:
                return None

            info = resultado.stdout
            id_vendor = re.search(r'ID_VENDOR_ID=(\w+)', info)
            id_product = re.search(r'ID_MODEL_ID=(\w+)', info)
            serial = re.search(r'ID_SERIAL_SHORT=([^\n]+)', info)

            return {
                'ttyUSB': ttyusb,
                'idVendor': id_vendor.group(1) if id_vendor else None,
                'idProduct': id_product.group(1) if id_product else None,
                'serial': serial.group(1) if serial else None
            }
        except Exception as e:
            print(f"Error procesando {ttyusb}: {e}")
            return None

    def print_devices(self):
        """Muestra en pantalla los dispositivos encontrados"""
        if not self.dispositivos:
            print("No se encontraron dispositivos ttyUSB.")
            return
        print("Dispositivos ttyUSB encontrados:")
        for disp in self.dispositivos:
            print(f"  - {disp['ttyUSB']}")
            print(f"    - idVendor:  {disp['idVendor']}")
            print(f"    - idProduct: {disp['idProduct']}")
            print(f"    - Serial:    {disp['serial']}")


if __name__ == "__main__":
    scanner = USBDeviceScanner()
    scanner.scan()
    scanner.print_devices()
