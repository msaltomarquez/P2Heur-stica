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

    # Precalcular franjas necesarias por avión
    franjas_necesarias = {
        avion["id"]: {
            "tipo_1": avion["tareas_tipo_1"],
            "tipo_2": avion["tareas_tipo_2"]
        }
        for avion in aviones
    }

    # Definir variables y reducir dominios según franjas necesarias
    for avion in aviones:
        for franja in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{franja}"
            dominio = []

            # Determinar dominio por tipo de franja
            if franjas_necesarias[avion["id"]]["tipo_2"] > 0:
                dominio = [{"posicion": pos, "tipo_ubicacion": "SPC", "id_avion": avion["id"], "tipo": avion["tipo"]} for pos in talleres_spc]
                franjas_necesarias[avion["id"]]["tipo_2"] -= 1
            elif franjas_necesarias[avion["id"]]["tipo_1"] > 0:
                dominio = [{"posicion": pos, "tipo_ubicacion": "STD", "id_avion": avion["id"], "tipo": avion["tipo"]} for pos in talleres_std]
                franjas_necesarias[avion["id"]]["tipo_1"] -= 1
            else:
                dominio = [{"posicion": pos, "tipo_ubicacion": "PRK", "id_avion": avion["id"], "tipo": avion["tipo"]} for pos in parkings]

            problem.addVariable(variable, dominio)

    # Restricción de talleres y parkings: máximo 2 aviones, no 2 jumbos juntos
    def restriccion_taller_y_parking(*valores):
        conteo = {}
        for valor in valores:
            posicion = valor["posicion"]
            tipo_avion = valor["tipo"]
            if posicion not in conteo:
                conteo[posicion] = {"total": 0, "jumbo": 0}
            conteo[posicion]["total"] += 1
            if tipo_avion == "JMB":
                conteo[posicion]["jumbo"] += 1
            if conteo[posicion]["total"] > 2 or conteo[posicion]["jumbo"] > 1:
                return False
        return True

    # Aplica la restricción de talleres y parkings
    for franja in range(franjas_horarias):
        variables_franja = [f"Avion_{avion['id']}_t{franja}" for avion in aviones]
        problem.addConstraint(restriccion_taller_y_parking, variables_franja)

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
