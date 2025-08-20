import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import sys
import os

# Añade la carpeta principal del proyecto al path de Python para resolver las importaciones
# El script está en 'src/', por lo que subimos un nivel para llegar a la raíz del proyecto.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.database_manager import DatabaseManager


class RecipeEditor:
    def __init__(self, master):
        self.master = master
        self.db = DatabaseManager()
        self.master.title("Editor de Recetas de Prueba")
        self.master.attributes('-fullscreen', True)
        self.master.bind('<Escape>', self.exit_fullscreen)
        
        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Controles
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=10)

        ttk.Label(controls_frame, text="Código ERP:").pack(side=tk.LEFT, padx=5)
        self.erp_code_combobox = ttk.Combobox(controls_frame, state="readonly")
        self.erp_code_combobox.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.erp_code_combobox.bind("<<ComboboxSelected>>", self.load_recipe)

        # Botones de acción
        ttk.Button(controls_frame, text="Añadir Paso", command=self.add_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Copiar Receta", command=self.copy_recipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Guardar Cambios", command=self.save_recipe).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Cancelar", command=self.cancel_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Salir", command=self.master.quit).pack(side=tk.LEFT, padx=5)

        # Tabla de pasos de la receta (Treeview)
        # Se han añadido todas las columnas de la tabla 'test_recipes'.
        self.treeview = ttk.Treeview(main_frame, columns=("Step", "StepName", "Title", "Subtitle", "Description", "Command", "Operation", "Expected", "Data_min", "Data_max", "Image", "Label", "Report", "Boxes"), show="headings")
        self.treeview.heading("Step", text="Paso", anchor=tk.CENTER)
        self.treeview.heading("StepName", text="Nombre del Paso", anchor=tk.W)
        self.treeview.heading("Title", text="Título", anchor=tk.W)
        self.treeview.heading("Subtitle", text="Subtítulo", anchor=tk.W)
        self.treeview.heading("Description", text="Descripción", anchor=tk.W)
        self.treeview.heading("Command", text="Comando", anchor=tk.W)
        self.treeview.heading("Operation", text="Operación", anchor=tk.W)
        self.treeview.heading("Expected", text="Respuesta Esperada", anchor=tk.W)
        self.treeview.heading("Data_min", text="Mínimo", anchor=tk.W)
        self.treeview.heading("Data_max", text="Máximo", anchor=tk.W)
        self.treeview.heading("Image", text="Imagen", anchor=tk.W)
        self.treeview.heading("Label", text="Etiqueta", anchor=tk.W)
        self.treeview.heading("Report", text="Informe", anchor=tk.W)
        self.treeview.heading("Boxes", text="Boxes", anchor=tk.CENTER)
        
        # Ajustar el ancho de las columnas
        self.treeview.column("Step", width=50, stretch=False)
        self.treeview.column("StepName", width=120)
        self.treeview.column("Title", width=150)
        self.treeview.column("Subtitle", width=150)
        self.treeview.column("Description", width=200)
        self.treeview.column("Command", width=150)
        self.treeview.column("Operation", width=100)
        self.treeview.column("Expected", width=100)
        self.treeview.column("Data_min", width=80)
        self.treeview.column("Data_max", width=80)
        self.treeview.column("Image", width=100)
        self.treeview.column("Label", width=100)
        self.treeview.column("Report", width=100)
        self.treeview.column("Boxes", width=60, stretch=False)
        
        self.treeview.pack(fill=tk.BOTH, expand=True)

        # Evento para editar celda al hacer doble clic
        self.treeview.bind("<Double-1>", self.start_edit)

    def load_products(self):
        """Carga los códigos ERP de la tabla 'products' en el Combobox."""
        try:
            products = self.db.execute_query("SELECT erp_code FROM products")
            if products:
                self.erp_code_combobox['values'] = [p[0] for p in products]
            else:
                self.erp_code_combobox['values'] = []
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudieron cargar los productos: {e}")

    def load_recipe(self, event=None):
        """Carga los pasos de la receta para el ERP seleccionado en el Treeview."""
        selected_erp = self.erp_code_combobox.get()
        if not selected_erp:
            return

        self.treeview.delete(*self.treeview.get_children())
        
        try:
            # Se ha corregido el orden de las columnas para que coincida con el Treeview
            recipe_steps = self.db.execute_query(
                "SELECT step_number, step_name, title, subtitle, description, command, operation, expected_response, data_min, data_max, image_path, label, report, boxes "
                "FROM test_recipes WHERE erp_code = %s ORDER BY step_number", (selected_erp,))
            
            for step in recipe_steps:
                self.treeview.insert("", "end", values=step)
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudo cargar la receta: {e}")

    def start_edit(self, event):
        """Permite editar una celda del Treeview al hacer doble clic."""
        region = self.treeview.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.treeview.identify_column(event.x)
        item_id = self.treeview.identify_row(event.y)
        
        # Ignorar la edición de la columna de paso
        if column == "#1":
            return

        column_index = int(column[1:]) - 1
        x, y, width, height = self.treeview.bbox(item_id, column=column)

        # Crear el widget de edición
        entry_edit = ttk.Entry(self.treeview, style="Treeview")
        entry_edit.place(x=x, y=y, width=width, height=height)
        entry_edit.insert(0, self.treeview.item(item_id, "values")[column_index])
        entry_edit.focus()
        
        def on_edit_end(event):
            new_value = entry_edit.get()
            current_values = list(self.treeview.item(item_id, "values"))
            current_values[column_index] = new_value
            self.treeview.item(item_id, values=tuple(current_values))
            entry_edit.destroy()

        entry_edit.bind("<Return>", on_edit_end)
        entry_edit.bind("<FocusOut>", on_edit_end)

    def add_step(self):
        """Añade una nueva fila al Treeview para un nuevo paso de la receta."""
        children = self.treeview.get_children()
        new_step_number = len(children) + 1
        # Valores por defecto para todas las columnas, ahora con el orden correcto
        default_values = (new_step_number, "Nuevo Paso", "", "", "", "", "", "", "", "", "", "", "", 6)
        self.treeview.insert("", "end", values=default_values)
        print(f"Paso {new_step_number} añadido. Recuerda guardar los cambios.")

    def save_recipe(self):
        """Guarda todos los cambios realizados en el Treeview en la base de datos."""
        selected_erp = self.erp_code_combobox.get()
        if not selected_erp:
            messagebox.showerror("Error", "Selecciona un código ERP para guardar.")
            return

        if not messagebox.askyesno("Confirmar Guardado", "Esto sobrescribirá la receta actual. ¿Continuar?"):
            return

        try:
            # Eliminar la receta antigua para luego insertar la nueva
            self.db.execute_query("DELETE FROM test_recipes WHERE erp_code = %s", (selected_erp,), fetch=False)
            
            # Recorrer el Treeview e insertar los nuevos pasos
            for i, item_id in enumerate(self.treeview.get_children(), start=1):
                values = self.treeview.item(item_id, "values")
                insert_query = """
                INSERT INTO test_recipes 
                (erp_code, step_number, step_name, title, subtitle, description, command, operation, expected_response, data_min, data_max, image_path, label, report, boxes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                # Se ha corregido la lista de valores para que coincida con el número de placeholders
                self.db.execute_query(insert_query, 
                                     (selected_erp, i, values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13]),
                                     fetch=False)

            edit_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Receta para {selected_erp} guardada. Fecha de edición: {edit_date}")
            messagebox.showinfo("Guardado", f"Receta para {selected_erp} guardada con éxito.")

        except Exception as e:
            messagebox.showerror("Error de Guardado", f"Error al guardar la receta: {e}")

    def copy_recipe(self):
        """Permite copiar la receta actual a un nuevo código ERP."""
        selected_erp = self.erp_code_combobox.get()
        if not selected_erp:
            messagebox.showerror("Error", "Selecciona una receta para copiar.")
            return

        new_erp_code = simpledialog.askstring("Copiar Receta", "Introduce el nuevo código ERP:")
        if not new_erp_code:
            return

        if self.db.execute_query("SELECT erp_code FROM products WHERE erp_code = %s", (new_erp_code,)):
            messagebox.showerror("Error", "El código ERP ya existe. Elige otro.")
            return

        try:
            # Primero, inserta el nuevo producto
            self.db.execute_query("INSERT INTO products (erp_code) VALUES (%s)", (new_erp_code,), fetch=False)
            
            # Luego, copia los pasos de la receta
            for i, item_id in enumerate(self.treeview.get_children(), start=1):
                values = self.treeview.item(item_id, "values")
                insert_query = """
                INSERT INTO test_recipes 
                (erp_code, step_number, step_name, title, subtitle, description, command, operation, expected_response, data_min, data_max, image_path, label, report, boxes) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                # Se ha corregido la lista de valores para que coincida con el número de placeholders
                self.db.execute_query(insert_query, 
                                     (new_erp_code, i, values[1], values[2], values[3], values[4], values[5], values[6], values[7], values[8], values[9], values[10], values[11], values[12], values[13]),
                                     fetch=False)

            messagebox.showinfo("Copiado", f"Receta copiada de {selected_erp} a {new_erp_code} con éxito.")
            self.load_products() # Actualiza el combobox con el nuevo producto
            self.erp_code_combobox.set(new_erp_code)
            self.load_recipe()
            
        except Exception as e:
            messagebox.showerror("Error al Copiar", f"No se pudo copiar la receta: {e}")
            
    def cancel_changes(self):
        """Descarta los cambios no guardados recargando la receta."""
        self.load_recipe()
    
    def exit_fullscreen(self, event=None):
        """Sale del modo de pantalla completa."""
        self.master.attributes('-fullscreen', False)

if __name__ == "__main__":
    root = tk.Tk()
    app = RecipeEditor(root)
    root.mainloop()