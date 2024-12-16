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

            # Si hay más de un JMB en la misma posición, no es válido
            if conteo[posicion]["JMB"] > 1:
                return False

            # Si hay un JMB, no puede haber otros aviones
            if conteo[posicion]["JMB"] > 0 and (conteo[posicion]["STD"] > 0):
                return False

            # Si hay más de dos aviones en total, no es válido
            if conteo[posicion]["STD"] + conteo[posicion]["JMB"] > 2:
                return False
        
        return True


    # Aplicar la restricción para cada franja horaria
    for franja in range(franjas_horarias):
        variables_franja = [f"Avion_{avion['id']}_t{franja}" for avion in aviones]
        problem.addConstraint(restriccion_talleres, variables_franja)


    def criterio_asignacion_logica(valor, estado_ubicaciones, franja):
        """
        Evalúa una asignación tentativa considerando el estado de ocupación de las ubicaciones.
        - Aviones sin tareas -> Parking libre.
        - Aviones con tareas de tipo 2 -> Taller especial (SPC) disponible, si no, otro lugar.
        - Aviones con solo tareas de tipo 1 -> Taller estándar (STD) o especial (SPC) disponible.
        """
        posicion = valor["posicion"]
        tipo_ubicacion = valor["tipo_ubicacion"]
        tareas_tipo_1 = valor["tareas_tipo_1"]
        tareas_tipo_2 = valor["tareas_tipo_2"]

        # Verificar si la posición está ocupada
        ocupacion = estado_ubicaciones[franja][posicion]["ocupado"]

        # Aviones sin tareas deben estar en un parking libre
        if tareas_tipo_1 == 0 and tareas_tipo_2 == 0:
            return tipo_ubicacion == "PRK" and not ocupacion

        # Aviones con tareas de tipo 2 deben ir a talleres especiales
        if tareas_tipo_2 > 0:
            if tipo_ubicacion == "SPC" and not ocupacion:
                return True
            # Si no hay talleres especiales disponibles, permitir cualquier lugar libre
            return not ocupacion

        # Aviones con solo tareas de tipo 1 pueden estar en STD o SPC
        if tareas_tipo_1 > 0:
            return tipo_ubicacion in ["STD", "SPC"] and not ocupacion

        # Si llega aquí, significa que no hay talleres disponibles
        # Permitir asignación a un parking como opción de respaldo
        return tipo_ubicacion == "PRK" and not ocupacion
    
        
    # Aplicar el criterio lógico de asignación para cada avión y franja horaria
    for avion in aviones:
        for franja in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{franja}"

            def restriccion_asignacion(valor, estado=estado_ubicaciones, t=franja):
                return criterio_asignacion_logica(valor, estado, t)

            problem.addConstraint(restriccion_asignacion, [variable])

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