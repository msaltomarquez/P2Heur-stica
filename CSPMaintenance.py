import sys
from constraint import Problem

def leer_entrada(ruta_entrada):
    """
    Lee un archivo de entrada y devuelve la información en variables organizadas.
    """
    with open(ruta_entrada, "r") as archivo:
        lineas = archivo.readlines()

    # Leer el número de franjas horarias
    franjas_horarias = int(lineas[0].split(":")[1].strip())

    # Leer el tamaño de la matriz
    tamano_matriz = tuple(map(int, lineas[1].split("x")))

    # Leer las posiciones de talleres estándar, especialistas y parkings
    def parse_coordenadas(linea):
        """
        Convierte una línea con coordenadas en una lista de tuplas.
        Maneja casos con espacios extra o formatos inesperados.
        """
        coordenadas = linea.split(":")[1].strip()
        coordenadas_limpias = coordenadas.replace(" ", "").split(")(")
        coordenadas_validas = []
        for coord in coordenadas_limpias:
            try:
                coord = coord.strip("()")
                coordenadas_validas.append(tuple(map(int, coord.split(","))))
            except ValueError:
                print(f"Advertencia: Coordenada inválida ignorada: {coord}")
        return coordenadas_validas

    talleres_std = parse_coordenadas(lineas[2])
    talleres_spc = parse_coordenadas(lineas[3])
    parkings = parse_coordenadas(lineas[4])

    # Leer los datos de los aviones
    aviones = []
    for linea in lineas[5:]:
        partes = linea.strip().split("-")
        if len(partes) == 5:
            aviones.append({
                "id": int(partes[0]),
                "tipo": partes[1],
                "restr": partes[2] == "T",
                "tareas_tipo_1": int(partes[3]),
                "tareas_tipo_2": int(partes[4]),
            })
        else:
            print(f"Advertencia: Línea de avión inválida ignorada: {linea}")

    return franjas_horarias, tamano_matriz, talleres_std, talleres_spc, parkings, aviones

def definir_modelo_csp(franjas_horarias, talleres_std, talleres_spc, parkings, aviones):
    # Crear el problema CSP
    problem = Problem()

    # Estructura auxiliar para registrar las posiciones ocupadas en cada franja horaria
    estado_ubicaciones = {
        franja: {
            (x, y): {"ocupado": False, "id_avion": None, "tipo_ubicacion": None}
            for x, y in parkings + talleres_std + talleres_spc
        }
        for franja in range(franjas_horarias)
    }

    # Definir variables y dominios
    for avion in aviones:
        for franja in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{franja}"
            dominio = []

            # Construir dominio como lista de diccionarios con información detallada
            for posicion in parkings + talleres_std + talleres_spc:
                if posicion in talleres_spc or posicion in talleres_std:
                    tipo_ubicacion = "SPC" if posicion in talleres_spc else "STD"
                else:
                    tipo_ubicacion = "PRK"
                dominio.append({
                    "posicion": posicion,
                    "tipo_ubicacion": tipo_ubicacion,
                    "tipo_avion": avion['tipo'],
                    "tareas_tipo_1": avion['tareas_tipo_1'],
                    "tareas_tipo_2": avion['tareas_tipo_2']
                })
            
            # Agregar variable y dominio al problema
            problem.addVariable(variable, dominio)

    # Restricción de talleres: no más de 2 aviones, no más de un JMB
    def restriccion_talleres(*valores):
        conteo = {}
        for valor in valores:
            posicion = valor["posicion"]
            tipo_avion = valor["tipo_avion"]
            
            # Inicializar conteo para la posición
            if posicion not in conteo:
                conteo[posicion] = {"STD": 0, "JMB": 0}
            
            # Contar aviones en la posición
            conteo[posicion][tipo_avion] += 1

            # Restricciones específicas
            if conteo[posicion]["JMB"] > 1:
                return False  # No más de un JMB
            if conteo[posicion]["JMB"] > 0 and conteo[posicion]["STD"] > 0:
                return False  # Un JMB no puede coexistir con un STD
            if conteo[posicion]["STD"] + conteo[posicion]["JMB"] > 2:
                return False  # No más de dos aviones en total
        
        return True

    for franja in range(franjas_horarias):
        variables_franja = [f"Avion_{avion['id']}_t{franja}" for avion in aviones]
        problem.addConstraint(restriccion_talleres, variables_franja)

    # Función de criterio de asignación lógica
    def criterio_asignacion_logica(valor, estado_ubicaciones, franja):
        posicion = valor["posicion"]
        tipo_ubicacion = valor["tipo_ubicacion"]
        tareas_tipo_1 = valor["tareas_tipo_1"]
        tareas_tipo_2 = valor["tareas_tipo_2"]
        ocupacion = estado_ubicaciones[franja][posicion]["ocupado"]

        print(f"Evaluando Avión en {posicion} ({tipo_ubicacion}) - "
              f"Tareas Tipo 1: {tareas_tipo_1}, Tipo 2: {tareas_tipo_2}, Ocupado: {ocupacion}")

        if tareas_tipo_1 == 0 and tareas_tipo_2 == 0:
            return tipo_ubicacion == "PRK" and not ocupacion
        if tareas_tipo_2 > 0:
            return tipo_ubicacion == "SPC" and not ocupacion
        if tareas_tipo_1 > 0:
            return tipo_ubicacion in ["STD", "SPC"] and not ocupacion
        return False

    # Función para reducir tareas de aviones al final de cada franja horaria
    def reducir_tareas(aviones, estado_ubicaciones, franja):
        print(f"\n### Reducción de tareas - Franja {franja} ###")
        for avion in aviones:
            print(f"Avión {avion['id']} - Tareas antes: Tipo 1 = {avion['tareas_tipo_1']}, Tipo 2 = {avion['tareas_tipo_2']}")
            for posicion, datos in estado_ubicaciones[franja].items():
                if datos["id_avion"] == avion["id"]:
                    print(f"  Avión {avion['id']} está en {posicion} ({datos['tipo_ubicacion']})")
                    if datos["tipo_ubicacion"] == "SPC" and avion["tareas_tipo_2"] > 0:
                        avion["tareas_tipo_2"] -= 1
                        print(f"    Tarea tipo 2 reducida. Nueva cantidad: {avion['tareas_tipo_2']}")
                    elif datos["tipo_ubicacion"] == "STD" and avion["tareas_tipo_1"] > 0:
                        avion["tareas_tipo_1"] -= 1
                        print(f"    Tarea tipo 1 reducida. Nueva cantidad: {avion['tareas_tipo_1']}")

    # Aplicar restricciones y reducción de tareas por franja
    for franja in range(franjas_horarias):
        for avion in aviones:
            variable = f"Avion_{avion['id']}_t{franja}"

            def restriccion_asignacion(valor, estado=estado_ubicaciones, t=franja):
                return criterio_asignacion_logica(valor, estado, t)

            problem.addConstraint(restriccion_asignacion, [variable])

        # Llamada a la función para reducir tareas después de asignaciones
        reducir_tareas(aviones, estado_ubicaciones, franja)

    return problem



def resolver_y_mostrar(problem, max_soluciones):
    soluciones = []
    for solucion in problem.getSolutionIter():
        soluciones.append(solucion)
        if len(soluciones) >= max_soluciones:
            break

    if not soluciones:
        print("No se encontraron soluciones.")
    else:
        print(f"Se encontraron {len(soluciones)} soluciones (limitado a {max_soluciones}).")
        for idx, solucion in enumerate(soluciones):
            print(f"\nSolución {idx + 1}:")
            for variable in sorted(solucion.keys(), key=lambda x: (int(x.split("_")[2][1:]), int(x.split("_")[1]))):
                print(f"{variable} -> {solucion[variable]}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python CSPMaintenance.py <ruta_archivo_entrada>")
        sys.exit(1)

    ruta_entrada = sys.argv[1]
    franjas_horarias, tamano_matriz, talleres_std, talleres_spc, parkings, aviones = leer_entrada(ruta_entrada)
    problem = definir_modelo_csp(franjas_horarias, talleres_std, talleres_spc, parkings, aviones)
    print("\nResolviendo el CSP...")
    resolver_y_mostrar(problem, max_soluciones=3)

if __name__ == "__main__":
    main()