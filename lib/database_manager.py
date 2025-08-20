import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host="localhost", database="Surge", user="selcimat", password="ws-prod23"):
        self.connection = None
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connect()

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print("Conexión a la base de datos exitosa.")
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")

    def execute_query(self, query, params=None, fetch=True):
        """Ejecuta una consulta SQL."""
        if not self.connection or not self.connection.is_connected():
            self.connect()

        if self.connection and self.connection.is_connected():
            cursor = self.connection.cursor()
            try:
                cursor.execute(query, params)
                if query.strip().upper().startswith("SELECT") and fetch:
                    result = cursor.fetchall()
                    return result
                elif not query.strip().upper().startswith("SELECT"):
                    self.connection.commit()
                    return True
            except Error as e:
                print(f"Error al ejecutar la consulta: {e}")
            finally:
                cursor.close()
        return None

    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada.")