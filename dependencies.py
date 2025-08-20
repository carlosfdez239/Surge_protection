import subprocess
import sys

# Lista de módulos necesarios para la aplicación
REQUIRED_MODULES = [
    "mysql-connector-python",
    "pyserial",
    "Pillow"
]

def install_dependencies():
    """
    Verifica si los módulos necesarios están instalados.
    Si un módulo no está presente, intenta instalarlo usando pip.
    """
    print("Verificando dependencias del proyecto...")
    
    # Comprueba si pip está disponible
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
    except FileNotFoundError:
        print("Error: pip no está instalado. Por favor, instala pip para continuar.")
        return False
    except subprocess.CalledProcessError:
        print("Error al ejecutar pip. Asegúrate de que está en tu PATH.")
        return False

    for module in REQUIRED_MODULES:
        try:
            # Importa el módulo para verificar su existencia
            __import__(module.replace('-', '_'))
            print(f"✅ {module} ya está instalado.")
        except ImportError:
            print(f"❌ {module} no encontrado. Intentando instalar...")
            try:
                # Intenta instalar el módulo
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"✅ {module} instalado con éxito.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error al instalar {module}: {e}")
                print("Por favor, instala la dependencia manualmente.")
                return False

    print("Todas las dependencias están satisfechas.")
    return True

if __name__ == "__main__":
    if install_dependencies():
        print("\nPuedes continuar con la ejecución de la aplicación.")
    else:
        print("\nLa instalación de dependencias ha fallado. Revisa los errores anteriores.")