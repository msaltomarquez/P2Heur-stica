# Generador de archivo de entrada para CSPMaintenance

def generar_archivo_entrada(ruta_archivo, franjas_horarias, tamano_matriz, talleres_std, talleres_spc, parkings, aviones):
    with open(ruta_archivo, "w") as archivo:
        # Escribir el número de franjas horarias
        archivo.write(f"Franjas: {franjas_horarias}\n")

        # Escribir el tamaño de la matriz
        archivo.write(f"{tamano_matriz[0]}x{tamano_matriz[1]}\n")

        # Escribir las posiciones de los talleres estándar, especialistas y parkings
        archivo.write(f"STD:{' '.join(map(str, talleres_std))}\n")
        archivo.write(f"SPC:{' '.join(map(str, talleres_spc))}\n")
        archivo.write(f"PRK:{' '.join(map(str, parkings))}\n")

        # Escribir los datos de los aviones
        for avion in aviones:
            archivo.write(f"{avion['id']}-{avion['tipo']}-{avion['restr']}-{avion['tareas_tipo_1']}-{avion['tareas_tipo_2']}\n")

# Datos de ejemplo
franjas_horarias = 4
tamano_matriz = (5, 5)

# Coordenadas de talleres estándar, especialistas y parkings
talleres_std = [(0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 2), (3, 3), (4, 1), (4, 2)]
talleres_spc = [(0, 3), (2, 1), (2, 3), (3, 0), (4, 3)]
parkings = [(0, 0), (0, 2), (0, 4), (1, 4), (2, 4), (3, 1), (3, 2), (3, 4), (4, 0), (4, 4)]

# Datos de los aviones
aviones = [
    {"id": 1, "tipo": "JMB", "restr": "T", "tareas_tipo_1": 2, "tareas_tipo_2": 2},
    {"id": 2, "tipo": "STD", "restr": "F", "tareas_tipo_1": 3, "tareas_tipo_2": 0},
    {"id": 3, "tipo": "STD", "restr": "F", "tareas_tipo_1": 1, "tareas_tipo_2": 0},
    {"id": 4, "tipo": "JMB", "restr": "T", "tareas_tipo_1": 1, "tareas_tipo_2": 1},
    {"id": 5, "tipo": "STD", "restr": "T", "tareas_tipo_1": 2, "tareas_tipo_2": 2},
]

# Generar el archivo de entrada
generar_archivo_entrada("entrada.txt", franjas_horarias, tamano_matriz, talleres_std, talleres_spc, parkings, aviones)
print("Archivo de entrada generado: entrada.txt")
