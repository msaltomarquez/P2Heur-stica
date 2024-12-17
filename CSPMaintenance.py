import sys
from constraint import Problem

def leer_entrada(ruta_entrada):
    with open(ruta_entrada, "r") as archivo:
        lineas = archivo.readlines()

    franjas_horarias = int(lineas[0].split(":")[1].strip())
    filas, columnas = map(int, lineas[1].split("x"))

    def parse_coordenadas(linea):
        coordenadas = linea.split(":")[1].strip()
        return [tuple(map(int, coord.strip("()").split(","))) for coord in coordenadas.replace(" ", "").split(")(")]

    talleres_std = parse_coordenadas(lineas[2])
    talleres_spc = parse_coordenadas(lineas[3])
    parkings = parse_coordenadas(lineas[4])

    aviones = []
    for linea in lineas[5:]:
        partes = linea.strip().split("-")
        aviones.append({
            "id": int(partes[0]),
            "tipo": partes[1],
            "restr": partes[2] == "T",
            "tareas_tipo_1": int(partes[3]),
            "tareas_tipo_2": int(partes[4]),
        })

    return franjas_horarias, filas, columnas, talleres_std, talleres_spc, parkings, aviones

def crear_mapa(filas, columnas, talleres_std, talleres_spc, parkings):
    mapa = [["VACIO" for _ in range(columnas)] for _ in range(filas)]

    for x, y in talleres_std:
        mapa[x][y] = "STD"
    for x, y in talleres_spc:
        mapa[x][y] = "SPC"
    for x, y in parkings:
        mapa[x][y] = "PRK"

    return mapa

def imprimir_mapa(mapa):
    print("\nMapa del aeropuerto:")
    for fila in mapa:
        print(" ".join(fila))

def adyacentes_validos(pos, filas, columnas):
    x, y = pos
    adyacentes = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
    return [(nx, ny) for nx, ny in adyacentes if 0 <= nx < filas and 0 <= ny < columnas]

def definir_modelo_csp(franjas_horarias, filas, columnas, talleres_std, talleres_spc, parkings, aviones, mapa):
    problem = Problem()

    # Definir variables y dominios
    for avion in aviones:
        tareas_tipo_2 = avion["tareas_tipo_2"]
        tareas_tipo_1 = avion["tareas_tipo_1"]

        for franja in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{franja}"
            if tareas_tipo_2 > 0:
                problem.addVariable(variable, [{"posicion": (x, y), "tarea": "T2", "tipo": avion["tipo"]} for x in range(filas) for y in range(columnas) if mapa[x][y] == "SPC"])
                tareas_tipo_2 -= 1
            elif tareas_tipo_1 > 0:
                problem.addVariable(variable, [{"posicion": (x, y), "tarea": "T1", "tipo": avion["tipo"]} for x in range(filas) for y in range(columnas) if mapa[x][y] in ["STD", "SPC"]])
                tareas_tipo_1 -= 1
            else:
                problem.addVariable(variable, [{"posicion": (x, y), "tarea": "PRK", "tipo": avion["tipo"]} for x in range(filas) for y in range(columnas) if mapa[x][y] == "PRK"])

    # Restricción: No permitir JMB+JMB y limitar a 2 aviones estándar
    def restriccion_capacidad(*valores):
        posiciones = {}
        for valor in valores:
            pos = valor["posicion"]
            tipo = valor["tipo"]
            if pos not in posiciones:
                posiciones[pos] = {"jumbos": 0, "estandar": 0}
            if tipo == "JMB":
                posiciones[pos]["jumbos"] += 1
            else:
                posiciones[pos]["estandar"] += 1

            # Restricciones combinadas: JMB+JMB prohibido, máximo 2 aviones estándar
            if posiciones[pos]["jumbos"] > 1:
                return False
            if posiciones[pos]["jumbos"] > 0 and posiciones[pos]["estandar"] > 1:
                return False
            if posiciones[pos]["estandar"] > 2:
                return False
        return True

    # Restricción: Un adyacente debe estar vacío y evitar JMB en adyacentes
    def restriccion_adyacentes(*valores):
        posiciones = [v["posicion"] for v in valores]
        for i, valor in enumerate(valores):
            pos = valor["posicion"]
            tipo = valor["tipo"]
            adyacentes = adyacentes_validos(pos, filas, columnas)

            # Verificar al menos un adyacente vacío
            if all(adj in posiciones for adj in adyacentes):
                return False

            # Prohibir dos JMB en adyacentes
            if tipo == "JMB":
                for j, otro_valor in enumerate(valores):
                    if i != j and otro_valor["tipo"] == "JMB" and otro_valor["posicion"] in adyacentes:
                        return False
        return True

    # Aplicar restricciones
    for t in range(franjas_horarias):
        variables = [f"Avion_{avion['id']}_t{t}" for avion in aviones]
        problem.addConstraint(restriccion_capacidad, variables)
        problem.addConstraint(restriccion_adyacentes, variables)

    return problem

def resolver_y_mostrar(problem):
    soluciones = list(problem.getSolutions())
    if not soluciones:
        print("No se encontraron soluciones.")
    else:
        print(f"Se encontraron {len(soluciones)} soluciones.")
        for idx, solucion in enumerate(soluciones):
            print(f"\nSolución {idx + 1}:")
            for variable, valor in sorted(solucion.items()):
                print(f"{variable} -> {valor}")

def main():
    if len(sys.argv) != 2:
        print("Uso: python CSPMaintenance.py <ruta_archivo_entrada>")
        sys.exit(1)

    ruta_entrada = sys.argv[1]
    franjas_horarias, filas, columnas, talleres_std, talleres_spc, parkings, aviones = leer_entrada(ruta_entrada)

    mapa = crear_mapa(filas, columnas, talleres_std, talleres_spc, parkings)
    imprimir_mapa(mapa)

    problem = definir_modelo_csp(franjas_horarias, filas, columnas, talleres_std, talleres_spc, parkings, aviones, mapa)
    print("\nResolviendo el CSP...")
    resolver_y_mostrar(problem)

if __name__ == "__main__":
    main()