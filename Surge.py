'''
Surge Protection Tester
================================
This code is a part of the Surge Protection Tester application, which is designed to test surge protection devices. 
It includes functionalities for scanning barcodes, executing commands, performing manual tasks, 
and printing labels and reports.

creation date: 2025-08-11
creator: C. Fdez

date: 2025-08-20
revision : 1.5.1


To Do
[X] Implementar la lógica de impresión de etiquetas y reportes.
[X] Importar el método para generar el template de impresión de etiquetas.
[ ] Definir qué tipo de informe queremos hacer y cómo se generará.
[ ] Limpiar el código de prints y comentarios innecesarios.
[ ] Comentar el código.
[ ] Implementar un método para re imprimir etiquetas en caso de error. Utilizar los datos de la tabla packaging_list.
    [ ] Implementar un botón para reimprimir etiquetas o desde el message box.


Bug history:
[ ] Revisar el método de validación de resultados para asegurar que maneja correctamente los casos
    donde NO se obtienen resultados válidos.
[ ] Asegurar que la lógica de impresión maneja correctamente los casos donde no hay unidades empaquetadas.
[X] Revisar la lógica de actualización de los boxes para asegurar que se actualizan correctamente
    los estados de las unidades después de cada prueba. 
[X] Modificar el serial de manera que sea un único número de serie formado por la concatenación de los actuales.


revision history:
1.0 - Initial version with basic functionalities for testing surge protection devices.
1.5 - Added functionalities for printing labels and Insert in packaging_list table.
1.5.1 - Modified the packaging_list table to include the serial number as a unique number joining the
        serials of the units in the packaging unit. Created a new variable Nb_serial to hold this value.
'''

import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import datetime
import os
from PIL import Image, ImageTk, ImageFont, ImageDraw
import sys
from pylibdmtx.pylibdmtx import encode
from lib.database_manager import DatabaseManager
from lib.serial_device import SerialDevice
from lib.printer import Printer
from lib.test_papel import Soporte_montado
from operations.ejecutar_command import EjecutarCommand
from operations.imprimir_report import ImprimirReport
from lib.busca_tty import USBDeviceScanner
from src.config import (
    COLOR_TESTING_INDICATOR,
    COLOR_OK,
    COLOR_NOK,
    COLOR_WHITE,
    COLOR_DARK_GRAY,
    COLOR_LIGHT_GRAY,
    COLOR_SUPER_LIGHT_GRAY,
    COLOR_HEADER_BG,
    COLOR_BUTTON_BLUE,
    COLOR_INIT_BUTTON,
    COLOR_BLACK,
)

class SurgeTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Surge Protection Tester")
        self.root.attributes('-fullscreen', True)
        self.root.config(bg=COLOR_DARK_GRAY)
        #self.root.bind('<Escape>', self.exit_fullscreen)
        self.root.bind('<Escape>', lambda event: self.root.destroy())  # Cierra la aplicación al presionar Escape

        self.db = DatabaseManager()
        
        self.status_boxes = {}
        self.erp_code_var = tk.StringVar()
        self.batch_entry_var = tk.StringVar()
        self.serial_entry_var = tk.StringVar()
        
        self.active_tests = {}
        self.packaging_units={}
        self.recipe_steps = []
        self.current_step_index = 0

        self.create_widgets()
        self.update_time()

        self.load_products_to_hmi()
        self.on_erp_selected(None)
        self.usb_connected =""
        # Dimensiones de la etiqueta
        self.mm_to_px = 11.81  # Factor de conversión de mm a px (300 DPI)
        self.label_width = int(50 * self.mm_to_px)  # 50 mm de ancho
        label_width_transformado = int(round(self.label_width/self.mm_to_px))
        self.label_height = int(35 * self.mm_to_px)  # 35 mm de alto

        self.BRAND = "LOADSENSING G7"
        self.RUBIK_FONT_PATH = "/home/ws-prod23/Surge_protection/src/fonts/Rubik-Light.ttf"  
        self.DIRECTORIO_LOGO = os.path.join(os.path.dirname(__file__), 'src', 'templates', 'W_Label_Devices_1.png')
        self.IMPRESORA = "Brother_packaging"
        self.FIXTURE = "c07f4c1c1a5bef11948d45405e7370b6"

        scanner = USBDeviceScanner()
        devices = scanner.scan()

        for d in devices:
            print(d["ttyUSB"], d["idVendor"], d["serial"])
            if d["serial"] == self.FIXTURE:
                self.usb_connected = d["ttyUSB"]
                print(f"👍 👍  La fixture está ahora conectada al puerto --> {self.usb_connected}\n")
            
        papel_montado = Soporte_montado()
        print (f"este es el valor de papel_montado cogiendo los dos primeros digitos --> {papel_montado[:2]}\n")
        print (f"este es el contenido de label_width_transformado --> {label_width_transformado}")
        if label_width_transformado == int(papel_montado[:2]):
            print(f"el ancho de papel es {label_width_transformado}")
            label_width_transformado = papel_montado
            print (f" ahora el valor de label_width_transformado es --> {label_width_transformado}")
        
        
        if papel_montado != label_width_transformado:
            aviso_papel = messagebox.showwarning(title="ATENCIÓN EN LA IMPRESORA", message=f"El papel montado es {papel_montado} pero el que se necesita es {label_width_transformado}, por favor cambia el rollo")

        print (f"\n El papel montado en la impresora es --> {papel_montado} y el formato de la etiqueta necesita {label_width_transformado}\n")

    def create_widgets(self):
        """Crea y organiza todos los widgets de la interfaz."""
        self.main_frame = tk.Frame(self.root, bg=COLOR_DARK_GRAY)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.header_frame = tk.Frame(self.main_frame, bg=COLOR_HEADER_BG, height=90)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)

        # Logo
        try:
            project_root = os.path.abspath(os.path.dirname(__file__))
            logo_path = os.path.join(project_root, 'src', 'templates', 'WS_logo.png')
            
            if os.path.exists(logo_path):
                self.logo_image = PhotoImage(file=logo_path)
                self.logo_label = tk.Label(self.header_frame, image=self.logo_image, bg=COLOR_HEADER_BG)
                self.logo_label.pack(side=tk.LEFT, padx=20, pady=10)
            else:
                logo_label = tk.Label(self.header_frame, 
                                      text="[LOGO]", 
                                      bg=COLOR_HEADER_BG, 
                                      fg=COLOR_WHITE, 
                                      font=("Arial", 16))
                logo_label.pack(side=tk.LEFT, padx=20, pady=10)
        except Exception as e:
            print(f"Error al cargar el logo: {e}")
            logo_label = tk.Label(self.header_frame, 
                                  text="[LOGO]", 
                                  bg=COLOR_HEADER_BG, 
                                  fg=COLOR_WHITE, font=("Arial", 16))
            logo_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        title_label = tk.Label(self.header_frame, 
                               text="Surge protect Testing", 
                               bg=COLOR_HEADER_BG, 
                               fg=COLOR_WHITE, 
                               font=("Arial", 24, "bold"))
        title_label.pack(side=tk.LEFT, expand=True, fill=tk.X, pady=10)

        self.time_label = tk.Label(self.header_frame, text="", bg=COLOR_HEADER_BG, fg=COLOR_WHITE, font=("Arial", 20))
        self.time_label.pack(side=tk.RIGHT, padx=20)

        self.content_frame = tk.Frame(self.main_frame, bg=COLOR_DARK_GRAY)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        self.lateral_frame = tk.Frame(self.content_frame, width=350, bg=COLOR_SUPER_LIGHT_GRAY)
        self.lateral_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.lateral_frame.pack_propagate(False)

        tk.Label(self.lateral_frame, text="Datos de la Unidad", 
                 bg=COLOR_SUPER_LIGHT_GRAY, 
                 font=("Arial", 18, "bold")).pack(pady=(20, 10))

        ttk.Label(self.lateral_frame, text="Código ERP:", 
                  background=COLOR_SUPER_LIGHT_GRAY, 
                  font=("Arial", 12)).pack(pady=(10, 5), padx=10, fill=tk.X)
        self.erp_combobox = ttk.Combobox(self.lateral_frame, 
                                         textvariable=self.erp_code_var, 
                                         state="readonly", 
                                         font=("Arial", 12))
        self.erp_combobox.pack(padx=10, fill=tk.X)
        self.erp_combobox.bind("<<ComboboxSelected>>", self.on_erp_selected)
        
        ttk.Label(self.lateral_frame, text="Número de Lote:", 
                  background=COLOR_SUPER_LIGHT_GRAY, 
                  font=("Arial", 12)).pack(pady=(10, 5), padx=10, fill=tk.X)
        ttk.Entry(self.lateral_frame, textvariable=self.batch_entry_var, font=("Arial", 12)).pack(padx=10, fill=tk.X)

        ttk.Label(self.lateral_frame, 
                  text="Número de Serie:", 
                  background=COLOR_SUPER_LIGHT_GRAY, 
                  font=("Arial", 12)).pack(pady=(10, 5), padx=10, fill=tk.X)
        self.serial_entry = ttk.Entry(self.lateral_frame, textvariable=self.serial_entry_var, font=("Arial", 12))
        self.serial_entry.pack(padx=10, fill=tk.X)
        
        self.serial_entry.bind("<Return>", lambda event: self.aceptar())

        self.start_button = ttk.Button(self.lateral_frame, text="Aceptar", command=self.aceptar)
        self.start_button.pack(pady=20, padx=10, fill=tk.X)
        
        self.center_frame = tk.Frame(self.content_frame, bg=COLOR_SUPER_LIGHT_GRAY)
        self.center_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.op_title_label = tk.Label(self.center_frame, text="Esperando Inicio...", bg=COLOR_SUPER_LIGHT_GRAY, fg=COLOR_DARK_GRAY, font=("Arial", 30, "bold"))
        self.op_title_label.pack(pady=(20, 10))
        
        self.op_subtitle_label = tk.Label(self.center_frame, 
                                          text="",
                                          anchor="w" ,
                                          bg=COLOR_SUPER_LIGHT_GRAY, 
                                          fg=COLOR_DARK_GRAY, 
                                          font=("Arial", 18))
        self.op_subtitle_label.pack(pady=5,
                                    padx=20,
                                    fill=tk.X,
                                    expand= True,)
        
        self.op_desc_label = tk.Label(self.center_frame, 
                                      text="",
                                      anchor="w", 
                                      bg=COLOR_SUPER_LIGHT_GRAY, 
                                      fg=COLOR_DARK_GRAY, 
                                      font=("Arial", 14), 
                                      wraplength=800)
        self.op_desc_label.pack(pady=10,
                                padx=20,
                                fill=tk.X,
                                expand= True,)
        
        self.op_image_label = tk.Label(self.center_frame, bg=COLOR_SUPER_LIGHT_GRAY)
        self.op_image_label.pack(pady=20)
        self.current_image = None
        
        self.boxes_frame = tk.Frame(self.center_frame, bg=COLOR_SUPER_LIGHT_GRAY)
        self.boxes_frame.pack(side=tk.BOTTOM,fill=tk.BOTH,  expand=True, padx=20, pady=5)
        
        self.footer_frame = tk.Frame(self.root, bg=COLOR_HEADER_BG, height=80)
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.footer_frame.pack_propagate(False)
        
        style_blue = ttk.Style()
        style_blue.configure("Blue.TButton", 
                             font=("Arial", 12), 
                             padding=10, 
                             background=COLOR_BUTTON_BLUE, 
                             foreground=COLOR_WHITE)
        style_blue.map("Custom.TButton",
                        background=[('active', COLOR_BUTTON_BLUE)],
                        foreground=[('active', COLOR_WHITE)])
                       
        
        style_red = ttk.Style()
        style_red.configure("Red.TButton", 
                            font=("Arial", 12), 
                            padding=10, 
                            )
        style_red.map("Custom.TButton",
                        background=[('active', COLOR_NOK)],
                        foreground=[('active', COLOR_WHITE)])

        self.continue_button = ttk.Button(self.footer_frame, 
                                          text="Continuar", 
                                          command=self.continue_test_logic, 
                                          style="Blue.TButton")
        self.continue_button.pack(side=tk.LEFT, padx=20, pady=5)
        self.continue_button.config(state=tk.DISABLED)
        
        self.abort_button = ttk.Button(self.footer_frame, 
                                       text="Abortar Test", 
                                       command=self.abort_test_process, 
                                       style="Red.TButton")
        self.abort_button.pack(side=tk.RIGHT, padx=20, pady=5)

    def update_time(self):
        """Actualiza la hora del sistema cada segundo."""
        now = datetime.datetime.now()
        self.time_str = now.strftime("%d/%m/%Y %H:%M:%S")
        self.time_label.config(text=self.time_str)
        self.root.after(1000, self.update_time)

    def update_test_info(self, title, subtitle, description, image_path=None):
        """Actualiza la información central de la operación de test."""
        
        self.op_title_label.config(text=title)
        
        # Actualiza el subtítulo y la descripción de la operación justificando a la izquierda
        self.op_subtitle_label.config(text=subtitle)
        self.op_desc_label.config(text=description)    

        # Actualiza la imagen de la operación si se proporciona una ruta
        if image_path and os.path.exists(image_path):
            try:
                original_image = Image.open(image_path)
                resized_image = original_image.resize((400, 300), Image.LANCZOS)
                self.current_image = ImageTk.PhotoImage(resized_image)
                self.op_image_label.config(image=self.current_image)
            except Exception as e:
                print(f"No se pudo cargar la imagen: {e}")
                self.op_image_label.config(image='', text="[IMAGEN NO ENCONTRADA]")
        else:
            self.op_image_label.config(image='', text="")
            self.current_image = None

    def create_status_boxes(self, num_boxes):
        """
        Crea los boxes para las unidades de prueba.
        Elimina los boxes existentes si los hubiera.
        """
        print(f" 👽👽👽 contenido de status_boxes a la entrada del create_status_boxes --> {self.status_boxes}\n")
        for widget in self.boxes_frame.winfo_children():
            widget.destroy()
        
        self.status_boxes = {}
        self.num_boxes = num_boxes
        print(f" 👽👽👽 contenido de status_boxes antes de empezar el test, debe estar vacío--> {self.status_boxes}\n")
        print (f"👉👉👉 Cantidad de boxes a crear: --> {self.num_boxes}\n")
        for i in range(self.num_boxes):
            box_text = f"UNIDAD_{i+1}"
            box_label= tk.Label(self.boxes_frame, 
                                text=f"UNIDAD_{i+1}", 
                                bg=COLOR_SUPER_LIGHT_GRAY, 
                                fg="#000000",
                                font=("Arial", 16), 
                                relief=tk.RAISED, 
                                bd=2, padx=10, 
                                pady=2)
            box_label.pack(padx=10,pady=2,side=tk.LEFT, fill=tk.X, expand=True,ipady= 100)
            self.status_boxes[i+1] = {'label': box_label, 'texto': box_text}
            print(f" {self.num_boxes} boxes creados, el último box creado es: {self.status_boxes[i+1]}\n")

    def update_box_status(self, box_number, status_color, serial=None):
        """Actualiza el color y el texto de un box."""
        if box_number in self.status_boxes:
            self.box = self.status_boxes[box_number]
            print(f"Actualizando box {box_number} con color {status_color} y serial {serial}\n")
            self.box_text = serial if serial else f""  #Ahora box_text contiene el serial
            print(f"Box text: {self.box_text}\n")
            self.box['label'].config(text=self.box_text, bg=status_color)
            self.box['texto'] = self.box_text
            print(f"Contenido de status_boxes después de actualizar el box {box_number}: {self.status_boxes}\n")

    def clear_all_boxes(self):
        """
        Recorre todos los boxes y los deja en su estado inicial (vacíos y con un color neutro).
        """
        for box_number in self.status_boxes.keys():
            self.update_box_status(
                box_number=box_number,
                status_color=COLOR_SUPER_LIGHT_GRAY,  # Color de fondo neutro
                serial=None                          # Pasa None para vaciar el texto
            )
            if hasattr(self, "num_boxes"):
                self.create_status_boxes(num_boxes=self.num_boxes)  # Vuelve a crear los boxes con el número actual
            else:
                print(f"❗❗❗ No se ha definido num_boxes, no se pueden recrear los boxes.\n")

    def update_box_color_status(self, box_number, status_color):
        """Actualiza el color y el texto de un box."""
        print(f"✈️ ✈️ ✈️ Datos que están entrando : box_number: {box_number}, status_color: {status_color}\n")
        if box_number in self.status_boxes:
            self.box = self.status_boxes[box_number]
            print(f"Actualizando box {box_number} con color {status_color} ")
            self.box['label'].config(bg=status_color)

    def exit_fullscreen(self, event=None):
        """Sale del modo de pantalla completa."""
        self.root.attributes('-fullscreen', False)

    def on_erp_selected(self, event):
        """Maneja la selección de un ERP para cargar la receta y la primera operación."""
        erp_code = self.erp_combobox.get()
        print(f"Desde on_erp_selected 👀👀👀 ERP Code seleccionado: {erp_code}\n")
        if erp_code:
            self.load_recipe()
            print(f"👀👀👀 Receta cargada para ERP Code {erp_code}: --> {self.recipe_steps}\n")
            if self.recipe_steps:
                self.current_step_index = 0
                self.update_hmi_with_step()
                self.create_status_boxes(num_boxes=self.recipe_steps[0][9])  # Asume que el número de boxes está en la receta
            else:
                self.update_test_info(
                    title="Error: Receta no encontrada",
                    subtitle="",
                    description=f"No hay pasos de prueba definidos para el producto con ERP_Code {self.erp_combobox.get()}."
                )
        else:
            self.update_test_info(
                title="Esperando Selección de Receta",
                subtitle="",
                description="Por favor, selecciona un producto del menú desplegable para ver los detalles de la receta."
            )

    def load_products_to_hmi(self):
        """Carga los códigos de producto desde la base de datos y los asigna al combobox de la HMI."""
        try:
            products = self.db.execute_query("SELECT erp_code FROM products")
            if products:
                product_list = [p[0] for p in products]
                self.erp_combobox['values'] = product_list
                if product_list:
                    self.erp_combobox.set(product_list[0])
        except Exception as e:
            print(f"Error al cargar los productos en la HMI: {e}")

    def load_recipe(self):
        """Carga la receta completa del producto seleccionado."""
        erp_code = self.erp_combobox.get()
        if erp_code:
            self.recipe_steps = self.db.execute_query(
                "SELECT operation, title, subtitle, description, image_path, command, expected_response, data_min, data_max, boxes "
                "FROM test_recipes WHERE erp_code = %s ORDER BY step_number", (erp_code,)
            )
            print(f"Dentro de load_recipe --> Receta cargada para ERP Code {erp_code}: {self.recipe_steps}\n")
            #self.create_status_boxes(num_boxes=self.recipe_steps[0][9])
            #print(f" desde load_recipe se pide crear los boxes --> Cantidad de boxes creados: {self.recipe_steps[0][9]}\n")

    def update_hmi_with_step(self):
        """Actualiza el frame central de la HMI con la información del paso actual."""
        if self.recipe_steps and self.current_step_index < len(self.recipe_steps):
            step_data = self.recipe_steps[self.current_step_index]
            title, subtitle, description, image_path = step_data[1], step_data[2], step_data[3], step_data[4]
            
            full_image_path = os.path.join(os.path.dirname(__file__), 'src/templates', image_path)
            
            self.update_test_info(
                title=title,
                subtitle=subtitle,
                description=description,
                image_path=full_image_path
            )

    def aceptar(self):
        # Limpiamos la entrada del serial para coger el nuero correcto de la etiqueta escaneada
        if ";" in self.serial_entry_var.get():
            self.serial_number = self.serial_entry_var.get().split(';')[1].strip()
        else:
            self.serial_number = self.serial_entry_var.get().strip()
        if not self.serial_number:
            print("Error: El Número de Serie es obligatorio.")
            return

        self.box_number = self.find_available_box()
        print(f"Box disponible: {self.box_number}\n")
        if not self.box_number:
            print("No hay boxes disponibles.")
            return

        print(f"Asignando Serial: {self.serial_number} al Box: {self.box_number}")
        
        self.load_recipe()
        print(f"Receta cargada: {self.recipe_steps}\n")

        self.update_box_status(box_number=self.box_number, 
                               status_color=COLOR_TESTING_INDICATOR, 
                               serial=self.serial_number)
        print(f"Actualizados el box con el serial {self.serial_number} y color {COLOR_TESTING_INDICATOR}\n")
        
        self.update_hmi_with_step()
        print(f"Actualizado hmi con receta para {self.serial_number} cargada con {len(self.recipe_steps)} pasos.")   
        

        self.active_tests[self.serial_number] = {
            "erp_code": self.erp_combobox.get(),
            "box_number": self.box_number,
            "status": "RUNNING",
            "current_step": 0
        }
        
        self.serial_entry_var.set("")
        self.continue_button.config(state=tk.NORMAL)

    def continue_test_logic(self):
        print(f"Botón 'Continuar' presionado.\n")
        #self.continue_button.config(state=tk.DISABLED)
        # Si estamos en el último paso, reiniciamos al primer paso
        if self.current_step_index == len(self.recipe_steps) - 1 :
            print("🈸🈸 Hemos llegado al final de la receta. Iniciando desde el primer paso de la receta.\n")
            self.current_step_index = 0
            
            # limpiar los status_boxes
            self.clear_all_boxes()
            #self.continue_button.config(state=tk.DISABLED)
            self.update_hmi_with_step()
            # borrado del active_tests ya que estamos en un nuevo ciclo de pruebas
            print(f"✅✅✅   Reiniciando active_tests para el nuevo ciclo de pruebas.\n")
            self.active_tests = {}
        

        else:
            print(f" No es el primer paso, avanzando al siguiente paso de la receta.\n")
            self.current_step_index += 1
        if "escanea_datamatrix.py" in self.recipe_steps[self.current_step_index][0]:
            print(f"Ponemos foco en entrada serial --> operación de escaneo de datamatrix en el paso {self.current_step_index}.\n")
            # Ponemos foco en la entrada de serial para que el usuario pueda escanear el datamatrix
            self.serial_entry.focus_set()
            
        self.run_next_step_logic()

    def run_next_step_logic(self):
        print(f"Ejecutando el siguiente paso de la receta... {self.current_step_index} \n")
        if not self.recipe_steps:
            return

        
        print(f"Índice del paso actual: {self.current_step_index}\n")
        print(f"Número total de pasos: {len(self.recipe_steps)}\n")
        print(f"Descripción de los Pasos de la receta: {self.recipe_steps}\n\n")
        
        if self.current_step_index < len(self.recipe_steps):
            step_data = self.recipe_steps[self.current_step_index]
            print(f"Descripcion del contenido del paso actual: {step_data}\n")
            self.update_hmi_with_step()
            operation_type = step_data[0]

            if operation_type in ["realizar_tarea_manual.py", "escanea_datamatrix.py"]:
                print(f"Ejecutando operación: {operation_type}\n")
                self.update_hmi_with_step()
                self.continue_button.config(state=tk.NORMAL)
            
            elif operation_type in ["Verificando unidad"]:
                print(f"💯💯💯 Ejecutando operación de verificar la unidad: {operation_type}\n")
                # Hacemos una query para obtener el estado de la unidad
                self.check_packaging_unit()
            elif operation_type in ["Imprimir"]:
                self.imprimir(packaging_units=self.packaging_units)
            else:
                self.run_automatic_tests()

    def check_packaging_unit(self):
        """
        Verifica si la unidad puede ser empaquetada.
        una query verfica los estados status = PASSED para los steps Verificando sensor VW y Verificando sensor TH
        """
        print("Estamos en check_unit, verificando si la unidad puede ser empaquetada.\n")
        sensor_VW = "Verificando sensor VW"
        sensor_TH = "Verificando sensor TH"
        # Cogemos el número de serie del box que se está verificando
        
        print(f"el Serial de la unidad verificada es : --> {self.serial_number}\n")
        estado_unidad = self.db.execute_query(
            "SELECT status FROM test_results WHERE serial_number = %s AND step_name IN (%s, %s)",
            (self.serial_number, sensor_VW, sensor_TH)
        )
        print(f"Resultado de la query en los steps Verificando sensor VW y Verificando sensor TH: {estado_unidad}\n")
        if estado_unidad:
            if all(status[0] == "PASSED" for status in estado_unidad):
                print("✅ ✅ ✅ La unidad puede ser empaquetada.\n")
                self.update_test_info(
                    title="Unidad Verificada",
                    subtitle="",
                    description="La unidad ha pasado todas las verificaciones y puede ser empaquetada.",
                    image_path=os.path.join(os.path.dirname(__file__), 'src/templates', 'unit_verified.png')
                )
                self.update_box_color_status(
                    box_number=self.box_number,
                    status_color=COLOR_OK
                )
                self.packaging_units[self.box_number] = {"serial":self.serial_number, "lote":self.batch_entry_var.get(),}
                print(f"Unidades que pueden ser empaquetadas: {self.packaging_units}\n")
                
            else:
                print("❌ ❌ ❌ La unidad no puede ser empaquetada, al menos un sensor falló.\n")
                self.update_test_info(
                    title="Unidad No Verificada",
                    subtitle="",
                    description="Al menos un sensor falló. La unidad no puede ser empaquetada. Cambia la unidad y vuelve a escanear.",
                    image_path=os.path.join(os.path.dirname(__file__), 'src/templates', 'unit_not_verified.png')
                )
                self.update_box_color_status(
                    box_number=self.box_number,
                    status_color=COLOR_NOK
                )
                print(f"Estamos en el else de la validación de  un serial. El numero del box actual es {self.box_number}\n")
                
    def run_automatic_tests(self):
        print("Todos los pasos manuales completados. Iniciando pruebas automáticas para todas las unidades.")
        # Query para obtener el commando del step actual
        # Aquí se asume que el comando y la respuesta esperada están en el paso actual
        if not self.recipe_steps:
            print("No hay pasos de receta definidos.\n")
            return
        print(f"🥈🥈🥈  Índice del paso actual: {self.current_step_index}\n")  

        step_data = self.recipe_steps[self.current_step_index]
        if not step_data:
            print("No hay datos de paso disponibles.\n")
            return 
         
        print(f"Datos del paso actual: {step_data}")
        # Aquí se asume que el comando y la respuesta esperada están en el paso actual
        command = step_data[5]
        print(f"Comando a ejecutar: {command}\n")
        command = command.encode()
        expected_response = step_data[6]
        print(f"Respuesta esperada: {expected_response}\n")
        Data_min = step_data[7]
        print(f"Data Min: {Data_min}\n")
        Data_max = step_data[8]
        print(f"Data Max: {Data_max}\n")

        puerto = "/dev/"+self.usb_connected
        print(f"el puerto actual para la fixture es --> {puerto}")

        res_command = EjecutarCommand(
            command=b'\n' + command + b'\n',
            expected_response=expected_response,
            device_serial=SerialDevice(port=puerto)
        )
        print(f"Ejecutando comando: {command} con respuesta esperada: {expected_response}")
        print(f'"respuesta recibida estoy en automatic_test:\n"+ {res_command}')
        channel_values = {}
                
        if not res_command.device_serial.connect():
            print("Error al conectar al dispositivo serial.")
            return  
        if res_command.execute():
            print("Comando ejecutado correctamente.")
            self.update_hmi_with_step()
            # Ejecutar la validación de los valores obtenidos
            self.validate_result(res_command.unit_response)
            
            self.continue_button.config(state=tk.NORMAL)
        else:
            print("Error al ejecutar el comando.")
            self.update_hmi_with_step()
            self.continue_button.config(state=tk.NORMAL)
  
    def validate_result(self, result):
        """
        Valida el resultado obtenido del comando ejecutado.
        Compara los valores obtenidos con los valores mínimos y máximos definidos en la receta.
        """
        self.Data_min = float(self.recipe_steps[self.current_step_index][7])
        self.Data_max = float(self.recipe_steps[self.current_step_index][8])
        print(f"🅰️ 🅰️ 🅰️   Contenido de status_boxes: {self.status_boxes}\n")
        print(f'👍 👍 Este es el contenido de result: --> {result}\n')

        if not result:
            print("No se obtuvo ningún resultado para validar.")
            return False
        
        # Creamos un diccionario temporal para guardar los resultados de cada canal
        processed_results = {}
        for elemento in result:
            if "=" in elemento:
                parts = elemento.split("=")
                try:
                    # Extraemos el número de canal de la cadena
                    channel_str = parts[0].split('channel')[1].strip()
                    channel_number = int(channel_str)
                    value = parts[1].strip()
                    processed_results[channel_number] = value
                except (IndexError, ValueError) as e:
                    print(f"❌ Error al parsear el elemento '{elemento}': {e}")
                    continue # Continuamos con el siguiente elemento
        
        # Si no se procesó ningún resultado, la validación falla
        if not processed_results:
            print(f"🔥 🔥 🔥  No se encontraron resultados de canal válidos en el output.\n")
            return False

        # Ahora iteramos sobre las cajas para validar cada resultado
        for box_key, box_value in self.status_boxes.items():
            channel_number = box_key - 1
            
            # Obtenemos el resultado para el canal correspondiente
            result_value_str = processed_results.get(channel_number)
            
            if result_value_str is None:
                print(f"❌ ❌ ❌ No se encontró un resultado para el canal {channel_number}.\n")
                self.update_box_color_status(
                    box_number=box_key,
                    status_color=COLOR_NOK
                )
                return False
                
            try:
                value = float(result_value_str)
                serial = box_value['texto']
                
                # Recuperamos los datos necesarios
                Erp_code = self.erp_combobox.get()
                batch_actual = self.batch_entry_var.get()
                actual_recipe_step = self.recipe_steps[self.current_step_index]
                actual_step_name = actual_recipe_step[2]
                time = datetime.datetime.now()

                if self.Data_min <= value <= self.Data_max:
                    print(f"✅ ✅ Valor para el canal {channel_number} dentro del rango esperado ({self.Data_min}, {value}, {self.Data_max}).\n")
                    status = "PASSED"
                    self.update_box_color_status(
                        box_number=box_key,
                        status_color=COLOR_OK
                    )
                else:
                    print(f"❌❌❌ Valor para el canal {channel_number} fuera del rango esperado ({self.Data_min}, {value}, {self.Data_max}).\n")
                    status = "FAILED"
                    self.update_box_color_status(
                        box_number=box_key,
                        status_color=COLOR_NOK
                    )
                    # Esto se ha de cambiar. El test continua aunque falle un canal
                    
                    #self.finalize_test(self, serial_number=serial, status="FAILED")
                    #return False

                # Consulta a la base de datos para la descripción
                info_producto = self.db.execute_query(
                    "SELECT ERP_Code, description FROM products WHERE ERP_Code = %s", (Erp_code,))
                
                # Inserción en la base de datos
                self.db.execute_query(
                    "INSERT INTO test_results (serial_number, product_code, status, batch_number, timestamp, description, step_name, data_min, data_value, data_max) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (serial, Erp_code, status, batch_actual, time, info_producto[0][1], actual_step_name, self.Data_min, value, self.Data_max),
                    fetch=False
                )
                print(f"✅✅✅  Datos insertados para el serial {serial} con valor {value}.\n")

            except ValueError as e:
                print(f"❌ Error al convertir el valor '{result_value_str}' a float: {e}")
                self.update_box_color_status(
                    box_number=box_key,
                    status_color=COLOR_NOK
                )
                return False
                
        # Si todos los bucles terminan sin un 'return False', significa que todo pasó
        print("✅ Todas las cajas han sido validadas correctamente. Avanzando al siguiente paso de la receta.")
        
        return True

    def finalize_test(self, serial_number, status):
        test_info = self.active_tests.pop(serial_number, None)
        if test_info:
            if "device" in test_info:
                test_info["device"].close()
            color = COLOR_OK if status == "PASSED" else COLOR_NOK
            self.update_box_status(test_info["box_number"], color, serial=serial_number)
            print(f"Test para {serial_number} finalizado con estado: {status}.\n")

    def abort_test_process(self):
        for serial_number in list(self.active_tests.keys()):
            self.finalize_test(serial_number, "FAILED")
        print("Todos los tests activos han sido abortados.")

    def find_available_box(self):
        print(f"Estamos en find_available_box--> valor de active_tests deberia estar vacio al inicio de un test --> {self.active_tests}\n")
        assigned_boxes = [info["box_number"] for info in self.active_tests.values()]
        for i in range(1, self.num_boxes + 1):
            if i not in assigned_boxes:
                return i
        return None

    def imprimir(self, packaging_units):
        """Placeholder para la función de impresión."""
        
        serials_en_etiqueta = ""

        # Primero haremos una query para obtener los datos de producto Model
        model = self.db.execute_query(
            "SELECT model FROM products WHERE erp_code = %s", (self.erp_combobox.get(),))
        
        # extraemos model para convertirlo a string
        if model:
            model = model[0][0]
        
        print(f"\nContenido de la variable modelo directamente de la query: {model}\n")
        
        erp_code = self.erp_combobox.get()
        print(f"Este es el ERP Code del combobox: {erp_code}\n")

        for unit_info in self.packaging_units.items():
            serials_en_etiqueta += f"{unit_info[1]['serial']};"
        
        print(f"Serials en la etiqueta: {serials_en_etiqueta}\n")

        Nb_serial = f'{serials_en_etiqueta.replace(";", "")}'  # Eliminamos el último punto y coma
        print(f"Este es el número de serie de la etiqueta: {Nb_serial}\n")

        # Extraemos el numero de lote
        Batch_n = self.batch_entry_var.get()
        print(f"Este es el número de lote del cuadro de texto: {Batch_n}\n")

        lote = self.packaging_units[1]['lote']
        print(f"Este es el numero de lote cogido de packaging_units: {lote}\n")
        
        font_size_std = 32  # Tamaño de la fuente
        address_font_size = 23  # Tamaño de la fuente para la dirección


        font_path = self.RUBIK_FONT_PATH
        print(f"directorio y fuente cargada --> {font_path}\n")

        fuente_std = ImageFont.truetype(self.RUBIK_FONT_PATH, font_size_std)
        fuente_address = ImageFont.truetype(self.RUBIK_FONT_PATH, address_font_size)
        
        print(f'valor de font --> {fuente_std} y de font_size --> {font_size_std}\n')

        # Crear la etiqueta
        label = Image.new("RGB", (self.label_width, self.label_height), "white")
        
        logo_path = self.DIRECTORIO_LOGO
        print(f'Imagen logo --> {logo_path}\n')

        logo = Image.open(logo_path,"r").resize((int(39 * self.mm_to_px), int(7 * self.mm_to_px)))

        label.paste(logo, (0, 0))

        # Insertar texto
        draw = ImageDraw.Draw(label)
        #print(f'creado draw --> {draw}')
        draw.text((2 * self.mm_to_px, 6 * self.mm_to_px), "Viriat 47, 10th Floor, 08014 Barcelona, Spain",font=fuente_address ,  fill='black')
        #print(f'creado el texto de la dirección de viriat')
        draw.text((0 * self.mm_to_px, 14 * self.mm_to_px), "Model:  " + model, font=fuente_std, fill="black")
        #print(f'creado el texto para el Model')
        draw.text((0 * self.mm_to_px, 19 * self.mm_to_px), "ERP Code:  " + erp_code,font=fuente_std,  fill="black")
        #print(f'creado el texto para el ERP')
        draw.text((0 * self.mm_to_px, 24 * self.mm_to_px), "Serial Nb:  " + Nb_serial, font=fuente_std, fill="black")

        draw.text((0 * self.mm_to_px, 29 * self.mm_to_px), "Batch:  " + lote, font=fuente_std, fill="black")
        
        # Insertar código Data Matrix
        datam = erp_code + ";" + Nb_serial +";"+ Batch_n
        encoded = encode(datam.encode('utf8'))
        dmtx = Image.frombytes('RGB', (encoded.width, encoded.height), encoded.pixels)
        dmtx = dmtx.resize((int(10 * self.mm_to_px), int(10 * self.mm_to_px)))
        label.paste(dmtx, (int(39*self.mm_to_px), int(9 * self.mm_to_px)))

        # Guardar la etiqueta como archivo

        # 1. Define la ruta base con la tilde
        base_output_path = "~/Surge_protection/output"
    
        # 2. Expande la tilde a una ruta de usuario real y válida
        expanded_output_path = os.path.expanduser(base_output_path)
        
        # 3. Verifica y crea el directorio si no existe
        if not os.path.exists(expanded_output_path):
            os.makedirs(expanded_output_path)
            print(f"Directorio creado: {expanded_output_path}")

        # 4. Define el nombre del archivo de la etiqueta
        label_name = f"{Nb_serial}.png"
        
        # 5. Combina el directorio y el nombre del archivo de forma segura
        archivo_label = os.path.join(expanded_output_path, label_name)
        
        # 6. Muestra la ruta final para depuración
        print(f"La ruta y el nombre del archivo es --> {archivo_label}")
        
        # 7. Guarda la etiqueta en la ruta correcta
        label.save(archivo_label)




        #output_path = os.path.expanduser("home/ws-prod23/Surge_protection/output/packaging_label.png") 
        #output_path = "~/Surge_protection/output/"     
        #output_dir = os.path.dirname(output_path)
        #if not os.path.exists(output_dir):
        #    os.makedirs(output_dir)  
        #label_name = f"{Nb_serial}.png"
        #archivo_label = output_path+label_name
        #print(f" la ruta y el nombre del archivo es --> {archivo_label}")
        #label.save(archivo_label)
        
        # Insertamos en base de datos los datos de la etiqueta
        timestamp = datetime.datetime.now()
        status = "PASSED"
        try:
            self.db.execute_query(
                "INSERT INTO packaging_list (erp_code, serials, batch_number,status ,model, timestamp, serial) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (erp_code, serials_en_etiqueta, lote, status ,model, timestamp, Nb_serial),
                fetch=False
               
            )
            print(f"Datos de la etiqueta insertados en la base de datos.\n")
        except Exception as e:
            print(f"Error al insertar los datos de la etiqueta en la base de datos: {e}\n")
            messagebox.showerror("Error", f"No se pudo insertar los datos de la etiqueta en la base de datos:\n{e}")
            return
        
        # Enviar el archivo a la impresora configurada
        try:
            #os.system(f'lp -o orientation-requested=3 -d {self.IMPRESORA} {output_path}{label_name}')
            os.system(f'lp -o orientation-requested=3 -d {self.IMPRESORA} {archivo_label}')
           
            messagebox.showinfo("Impresión", "La etiqueta se envió a la impresora correctamente.")
            

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo imprimir la etiqueta:\n{e}")
            
        return 

if __name__ == "__main__":
    root = tk.Tk()
    app = SurgeTester(root)
    root.mainloop()


