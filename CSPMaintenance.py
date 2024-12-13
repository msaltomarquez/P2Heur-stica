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
        # Eliminar todos los espacios dentro de las coordenadas y luego procesarlas
        coordenadas_limpias = coordenadas.replace(" ", "").split(")(")
        coordenadas_validas = []
        for coord in coordenadas_limpias:
            try:
                # Asegurarse de que cada coordenada sea válida
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
        if len(partes) == 5:  # Asegurarse de que la línea tiene todos los datos
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
    
    # Dominio completo: todas las ubicaciones posibles
    dominio = talleres_std + talleres_spc + parkings
    
    # Crear variables para cada avión en cada franja horaria
    for avion in aviones:
        for t in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{t}"
            problem.addVariable(variable, dominio)
    
    # Restricción básica: Cada avión debe estar en una única ubicación en cada franja horaria
    def ubicacion_valida(*asignaciones):
        # Cada ubicación asignada debe ser única
        return len(asignaciones) == len(set(asignaciones))
    
    for t in range(franjas_horarias):
        problem.addConstraint(
            ubicacion_valida,
            [f"Avion_{avion['id']}_t{t}" for avion in aviones]
        )
    
    return problem

def resolver_y_mostrar(problem, max_soluciones=3):
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
            for key, value in solucion.items():
                print(f"{key} -> {value}")

def main():
    """
    Función principal para ejecutar el código desde la línea de comandos.
    """
    if len(sys.argv) != 2:
        print("Uso: python CSPMaintenance.py <ruta_archivo_entrada>")
        sys.exit(1)

    ruta_entrada = sys.argv[1]
    franjas_horarias, tamano_matriz, talleres_std, talleres_spc, parkings, aviones = leer_entrada(ruta_entrada)

    # Mostrar los datos leídos
    print("Franjas horarias:", franjas_horarias)
    print("Tamaño de la matriz:", tamano_matriz)
    print("Talleres estándar:", talleres_std)
    print("Talleres especialistas:", talleres_spc)
    print("Parkings:", parkings)
    print("Aviones:", aviones)

    print("\nDefiniendo el modelo CSP...")
    problem = definir_modelo_csp(
        franjas_horarias, talleres_std, talleres_spc, parkings, aviones
    )

    print("\nResolviendo el CSP...")
    resolver_y_mostrar(problem, max_soluciones=3)  # Cambia el número de soluciones aquí según necesidad

if __name__ == "__main__":
    main()
