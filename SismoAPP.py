import tkinter as tk
from tkinter import messagebox, filedialog
from fpdf import FPDF
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap
import webbrowser
import os
import platform
import matplotlib.pyplot as plt
import seaborn as sns
from ttkthemes import ThemedTk
from tkinter import ttk
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ManejadorDatos:
    def __init__(self):
        self.datos = None

    def cargar_datos(self, ruta_archivo):
        try:
            self.datos = pd.read_excel(ruta_archivo, engine='openpyxl', parse_dates=['FECHA_UTC'])
            if self.datos.empty:
                raise ValueError("El archivo seleccionado no contiene datos.")
            return True, f"Datos cargados: {len(self.datos)} registros."
        except Exception as e:
            return False, f"No se pudieron cargar los datos: {e}"

    def filtrar_datos_por_año(self, año):
        datos_filtrados = self.datos[self.datos['FECHA_UTC'].dt.year == int(año)]
        if datos_filtrados.empty:
            return None, f"No hay registros de sismos para el año {año}."
        return datos_filtrados, None

class Visualizacion:
    def __init__(self, marco_visualizacion):
        self.marco_visualizacion = marco_visualizacion
        self.canvas = None

    def crear_mapa_cluster(self, datos, año):
        lat_centro, lon_centro = -9.19, -75.0152
        mapa_sismos = folium.Map(location=[lat_centro, lon_centro], zoom_start=5)
        cluster_marcadores = MarkerCluster().add_to(mapa_sismos)

        for _, fila in datos.iterrows():
            folium.Marker(
                location=[fila['LATITUD'], fila['LONGITUD']],
                popup=f"<b>Sismo</b><br>Latitud: {fila['LATITUD']}<br>Longitud: {fila['LONGITUD']}<br>Magnitud: {fila['MAGNITUD']}<br>Fecha: {fila['FECHA_UTC'].strftime('%Y-%m-%d')}<br>",
            ).add_to(cluster_marcadores)

        nombre_mapa = f'Mapa_Clusteres_{año}.html'
        mapa_sismos.save(nombre_mapa)
        self.abrir_archivo(nombre_mapa)

    def crear_mapa_calor(self, datos, año):
        lat_centro, lon_centro = -9.19, -75.0152
        mapa_calor = folium.Map(location=[lat_centro, lon_centro], zoom_start=5)
        datos_calor = datos[['LATITUD', 'LONGITUD']].values.tolist()
        HeatMap(datos_calor).add_to(mapa_calor)

        nombre_mapa_calor = f'Mapa_Calor_{año}.html'
        mapa_calor.save(nombre_mapa_calor)
        self.abrir_archivo(nombre_mapa_calor)

    def abrir_archivo(self, nombre_archivo):
        if platform.system() == 'Darwin':  # macOS
            os.system(f"open {os.path.abspath(nombre_archivo)}")
        elif platform.system() == 'Windows':  # Windows
            os.startfile(os.path.abspath(nombre_archivo))
        else:  # Linux and others
            os.system(f"xdg-open {os.path.abspath(nombre_archivo)}")

    def mostrar_histograma(self, datos, año, var):
        fig = plt.Figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        sns.histplot(datos[var], bins=20, kde=True, ax=ax)
        ax.set_title(f"Histograma de {var.capitalize()} de Sismos en {año}")
        ax.set_xlabel(var.capitalize())
        ax.set_ylabel("Frecuencia")
        ax.grid(True)

        self.canvas = FigureCanvasTkAgg(fig, master=self.marco_visualizacion)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

class ReportePDF:
    def generar_pdf(self, datos, año):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, f"Reporte de Sismos en Perú - Año {año}", ln=True, align='C')

        pdf.set_font("Arial", size=10)
        for i, fila in datos.iterrows():
            pdf.cell(0, 10, f"Fecha: {fila['FECHA_UTC'].strftime('%Y-%m-%d')} - Latitud: {fila['LATITUD']} - Longitud: {fila['LONGITUD']} - Magnitud: {fila['MAGNITUD']} - Profundidad: {fila['PROFUNDIDAD']} km", ln=True)

        fig, ax = plt.subplots(1, 2, figsize=(14, 6))
        sns.histplot(datos['MAGNITUD'], bins=20, kde=True, ax=ax[0])
        ax[0].set_title(f"Histograma de Magnitudes de Sismos en {año}")
        ax[0].set_xlabel("Magnitud")
        ax[0].set_ylabel("Frecuencia")
        ax[0].grid(True)

        sns.histplot(datos['PROFUNDIDAD'], bins=20, kde=True, ax=ax[1])
        ax[1].set_title(f"Distribución de Profundidades de Sismos en {año}")
        ax[1].set_xlabel("Profundidad (km)")
        ax[1].set_ylabel("Frecuencia")
        ax[1].grid(True)

        temp_graphics = "temp_graphics.png"
        plt.savefig(temp_graphics, bbox_inches='tight')
        pdf.image(temp_graphics, x=10, y=None, w=190)
        plt.close()

        nombre_pdf = f'Reporte_Sismos_{año}.pdf'
        pdf.output(nombre_pdf)
        webbrowser.open_new_tab(os.path.abspath(nombre_pdf))
        os.remove(temp_graphics)
        return nombre_pdf

class AplicacionSismos:
    def __init__(self, root):
        self.root = root
        self.root.title("Visualización de Sismos en Perú")
        self.root.geometry('1200x800') 

        self.style = ttk.Style()
        available_themes = self.style.theme_names()
        self.style.theme_use('keramik' if 'keramik' in available_themes else 'equilux')

        self.configurar_ui()
        self.manejador_datos = ManejadorDatos()
        self.visualizacion = Visualizacion(self.marco_visualizacion)
        self.reporte_pdf = ReportePDF()

    def configurar_ui(self):
        self.marco_principal = ttk.Frame(self.root)
        self.marco_principal.pack(fill='both', expand=True)

        self.variable_visualizacion = tk.StringVar()
        self.variable_visualizacion.set("Mapa con Clústeres")
        self.variable_año = tk.StringVar()

        self.marco_visualizacion = ttk.Frame(self.marco_principal, borderwidth=2, relief='ridge')
        self.marco_visualizacion.pack(side='bottom', fill='both', expand=True, padx=10, pady=10)

        self.marco_controles = ttk.Frame(self.marco_principal, borderwidth=2, relief='ridge')
        self.marco_controles.pack(side='top', fill='x', padx=10, pady=10)

        self.logo_img = Image.open("logo2.png").resize((200, 100), Image.LANCZOS)
        self.logo_img = ImageTk.PhotoImage(self.logo_img)
        self.logo_label = ttk.Label(self.marco_controles, image=self.logo_img)
        self.logo_label.pack(side='left', padx=10, pady=10)

        self.boton_cargar = ttk.Button(self.marco_controles, text="Cargar Datos de Sismos", command=self.cargar_datos)
        self.boton_cargar.pack(side='left', padx=10, pady=10)

        self.label_año = ttk.Label(self.marco_controles, text="Seleccionar Año:")
        self.label_año.pack(side='left', padx=10, pady=10)
        self.dropdown_año = ttk.Combobox(self.marco_controles, textvariable=self.variable_año, state='disabled', width=10)
        self.dropdown_año.pack(side='left', padx=10, pady=10)

        self.label_visualizacion = ttk.Label(self.marco_controles, text="Seleccionar Visualización:")
        self.label_visualizacion.pack(side='left', padx=10, pady=10)
        self.dropdown_visualizacion = ttk.Combobox(self.marco_controles, textvariable=self.variable_visualizacion, state='readonly', width=30)
        self.dropdown_visualizacion['values'] = [
            'Mapa con Clústeres', 'Mapa de Calor', 'Histograma de Magnitudes', 'Distribución de Profundidades'
        ]
        self.dropdown_visualizacion.pack(side='left', padx=10, pady=10)

        self.boton_aplicar_filtros = ttk.Button(self.marco_controles, text="Aplicar Filtros y Visualizar", command=self.aplicar_filtros)
        self.boton_aplicar_filtros.pack(side='left', padx=10, pady=10)

        self.boton_generar_pdf = ttk.Button(self.marco_controles, text="Generar Reporte PDF", command=self.generar_pdf)
        self.boton_generar_pdf.pack(side='left', padx=10, pady=10)

        self.label_estado = ttk.Label(self.marco_controles, text="Estado: Sin datos cargados")
        self.label_estado.pack(side='left', padx=10, pady=10)

    def cargar_datos(self):
        ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx")])
        if ruta_archivo:
            exito, mensaje = self.manejador_datos.cargar_datos(ruta_archivo)
            if exito:
                self.label_estado.config(text=mensaje)
                self.dropdown_año.config(state='normal')
                self.dropdown_año['values'] = sorted(self.manejador_datos.datos['FECHA_UTC'].dt.year.unique())
                messagebox.showinfo("Carga de Datos", "Datos cargados correctamente.")
            else:
                messagebox.showerror("Error al Cargar Datos", mensaje)
        else:
            messagebox.showwarning("Carga de Datos", "No se seleccionó ningún archivo.")

    def aplicar_filtros(self):
        if self.visualizacion.canvas:
            self.visualizacion.canvas.get_tk_widget().pack_forget()

        año = self.variable_año.get()
        datos_filtrados, mensaje_error = self.manejador_datos.filtrar_datos_por_año(año)
        if mensaje_error:
            messagebox.showwarning("Datos Faltantes", mensaje_error)
            return

        tipo_visualizacion = self.variable_visualizacion.get()
        if tipo_visualizacion == 'Mapa con Clústeres':
            self.visualizacion.crear_mapa_cluster(datos_filtrados, año)
        elif tipo_visualizacion == 'Mapa de Calor':
            self.visualizacion.crear_mapa_calor(datos_filtrados, año)
        elif tipo_visualizacion == 'Histograma de Magnitudes':
            self.visualizacion.mostrar_histograma(datos_filtrados, año, 'MAGNITUD')
        elif tipo_visualizacion == 'Distribución de Profundidades':
            self.visualizacion.mostrar_histograma(datos_filtrados, año, 'PROFUNDIDAD')

    def generar_pdf(self):
        año = self.variable_año.get()
        datos_filtrados, mensaje_error = self.manejador_datos.filtrar_datos_por_año(año)
        if mensaje_error:
            messagebox.showwarning("Datos Faltantes", mensaje_error)
            return

        nombre_pdf = self.reporte_pdf.generar_pdf(datos_filtrados, año)
        self.label_estado.config(text=f"Reporte PDF generado: {nombre_pdf}")

if __name__ == "__main__":
    root = ThemedTk(theme='equilux')
    app = AplicacionSismos(root)
    root.mainloop()
