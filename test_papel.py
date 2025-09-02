'''
Creado: C.Fdez
Fecha: 01/09/2025


Rev 0
Fecha: 01/09/2025


To do:
    [ ]



Historico revisiones:

    [ ]



Bugs:

    [ ]




'''

import subprocess 
from pysnmp.hlapi import *

def verifica_papel_impresora():
    print("Verificando el tamaño de papel de la impresora 'Brother_packaging'...\n")
    try:
        # Los argumentos del comando deben ser elementos separados en la lista
        #cmd = ["lpoptions", "-p", "Brother_packaging", "-l"]
        cmd = ["lpoptions", "-p", "QL-820NWB-2", "-l"]
        
        # Ejecuta el comando y captura la salida
        proceso = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # La salida del comando se encuentra en el atributo 'stdout'
        contenido_lpoption = proceso.stdout
        print("Salida del comando lpoptions:")
        print("------------------------------")
        print(contenido_lpoption)
        print("------------------------------\n")
        for linea in contenido_lpoption.splitlines():
            if linea.startswith("PageSize"):
                tipos = linea.split()

                for elemento in tipos :
                    if elemento.startswith("*"):
                        #return elemento.lstrip("*")
                        papel = elemento.lstrip("*")
                        papel = papel[:2]
                        
                        print(f"papel montado --> {papel}")
        

    except FileNotFoundError:
        print("Error: El comando 'lpoptions' no se encuentra en tu sistema.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando. Código de salida: {e.returncode}\n")
        print(f"Mensaje de error: {e.stderr}\n")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}\n")

    Etiqueta = 62
    if Etiqueta != int(papel):
        print(f"El papel montado es de {papel} y el definido en la etiquet es de {Etiqueta}. No corresponden, revisa el rollo montado")
        setea_papel(Etiqueta)
    else:
        print(f"el papel es correcto")

def setea_papel(PageSize):
    print(F"Cambiando el tamaño de papel de la impresora al {PageSize}...\n")

    cmd = ["lpoptions", "-p", "QL-820NWB-2", "-o", f"PageSize={PageSize}X1"]
    # Ejecuta el comando y captura la salida
    proceso = subprocess.run(cmd, capture_output=True, text=True, check=True)
    verifica_papel_impresora()

def Soporte_montado():
    
    cmd = ["snmpget", "-v1", "-c","public","192.168.1.200", "1.3.6.1.2.1.43.8.2.1.12.1.1"]
    proceso = subprocess.run(cmd, capture_output=True, text=True, check=True)

    salida = proceso.stdout.strip()
    if "STRING" in salida:
        soporte_papel = salida.split("STRING")[1].split('"')[1].strip().strip('"').strip('\\')
        print(f"el papel montado actualmente en la impresora es --> {soporte_papel}\n")
    else:
        print(f"No se ha encontrado identificación correcta del soporte\n")

if __name__ == "__main__":
    Soporte_montado()
    #verifica_papel_impresora()