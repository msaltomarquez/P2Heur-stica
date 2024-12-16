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
    
    # Restricción: Máximo 2 aviones por taller por franja horaria
    def restricciones_taller_y_parking(*asignaciones, franja_horaria=None):
        """
        Verifica que las restricciones de máximo 2 aviones en talleres y parkings
        (y máximo 1 avión tipo JMB en talleres) se cumplan.
        """
        # Inicializar contadores para talleres y parkings
        ocupaciones = {ubicacion: {'jumbos': 0, 'total': 0} for ubicacion in talleres_std + talleres_spc + parkings}

        # Contar ocupación por ubicación
        for idx, ubicacion in enumerate(asignaciones):
            avion = aviones[idx]
            es_jumbo = avion['tipo'] == 'JMB'

            # Actualizar contadores
            ocupaciones[ubicacion]['total'] += 1
            if es_jumbo:
                ocupaciones[ubicacion]['jumbos'] += 1

            # Validar restricciones:
            # - En talleres, si hay un JMB, no puede haber más aviones.
            # - En cualquier lugar (talleres o parkings), no más de 2 aviones.
            if ubicacion in talleres_std + talleres_spc:
                if ocupaciones[ubicacion]['jumbos'] > 1:
                    return False  # Más de 1 jumbo en un taller
                if ocupaciones[ubicacion]['jumbos'] == 1 and ocupaciones[ubicacion]['total'] > 1:
                    return False  # Un jumbo y otro avión en un taller
            if ocupaciones[ubicacion]['total'] > 2:
                return False  # Más de 2 aviones en un taller o parking


        return True


    # Aplicar la restricción a cada franja horaria con el índice correspondiente
    for t in range(franjas_horarias):
        problem.addConstraint(
            lambda *args, franja_horaria=t: restricciones_taller_y_parking(*args, franja_horaria=franja_horaria),
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
            # Ordenar las claves por franja horaria primero, luego por avión
            for variable in sorted(solucion.keys(), key=lambda x: (int(x.split("_")[2][1:]), int(x.split("_")[1]))):
                print(f"{variable} -> {solucion[variable]}")

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
    #print("Franjas horarias:", franjas_horarias)
    #print("Tamaño de la matriz:", tamano_matriz)
    #print("Talleres estándar:", talleres_std)
    #print("Talleres especialistas:", talleres_spc)
    #print("Parkings:", parkings)
    #print("Aviones:", aviones)

    #print("\nDefiniendo el modelo CSP...")
    problem = definir_modelo_csp(
        franjas_horarias, talleres_std, talleres_spc, parkings, aviones
    )

    print("\nResolviendo el CSP...")
    resolver_y_mostrar(problem, max_soluciones=1)  # Cambia el número de soluciones aquí según necesidad

if __name__ == "__main__":
    main()






# ULTIMO CÓDIGOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO

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
    
    # Dominio completo: todas las ubicaciones posibles
    dominio = talleres_std + talleres_spc + parkings
    
    # Crear variables para cada avión en cada franja horaria
    for avion in aviones:
        for t in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{t}"
            problem.addVariable(variable, dominio)
    
    # Restricción: Máximo 2 aviones por taller o parking por franja horaria
    def restricciones_taller_y_parking(*asignaciones):
        """
        Verifica que las restricciones de máximo 2 aviones en talleres y parkings
        (y máximo 1 avión tipo JMB en talleres) se cumplan.
        """
        ocupaciones = {ubicacion: {'jumbos': 0, 'total': 0} for ubicacion in dominio}

        # Contar ocupación por ubicación
        for idx, ubicacion in enumerate(asignaciones):
            avion = aviones[idx]
            es_jumbo = avion['tipo'] == 'JMB'

            ocupaciones[ubicacion]['total'] += 1
            if es_jumbo:
                ocupaciones[ubicacion]['jumbos'] += 1

            # Validar restricciones
            if ubicacion in talleres_std + talleres_spc:
                if ocupaciones[ubicacion]['jumbos'] > 1:
                    return False
                if ocupaciones[ubicacion]['jumbos'] == 1 and ocupaciones[ubicacion]['total'] > 1:
                    return False
            if ocupaciones[ubicacion]['total'] > 2:
                return False
        return True

    # Aplicar la restricción a cada franja horaria
    for t in range(franjas_horarias):
        problem.addConstraint(
            restricciones_taller_y_parking,
            [f"Avion_{avion['id']}_t{t}" for avion in aviones]
        )


    # Crear variables para el estado de las tareas pendientes
    for avion in aviones:
        for t in range(franjas_horarias):
            variable_tareas = f"Tareas_{avion['id']}_t{t}"
            problem.addVariable(variable_tareas, [
                (avion["tareas_tipo_1"], avion["tareas_tipo_2"]),  # Estado inicial de tareas
                (max(0, avion["tareas_tipo_1"] - 1), avion["tareas_tipo_2"]),  # Tipo 1 realizado
                (avion["tareas_tipo_1"], max(0, avion["tareas_tipo_2"] - 1))   # Tipo 2 realizado
            ])

    # Restricción: Si hay tareas pendientes, asignar a un taller compatible
    def taller_compatible(ubicacion, tareas):
        tareas_tipo_1, tareas_tipo_2 = tareas
        if tareas_tipo_2 > 0:  # Tareas tipo 2 pendientes, solo talleres especializados
            return ubicacion in talleres_spc
        if tareas_tipo_1 > 0:  # Tareas tipo 1 pendientes, talleres estándar o especializados
            return ubicacion in talleres_std + talleres_spc
        return True  # Sin tareas pendientes, puede estar en cualquier lugar

    for avion in aviones:
        for t in range(franjas_horarias):
            problem.addConstraint(
                lambda ubicacion, tareas:
                taller_compatible(ubicacion, tareas),
                [f"Avion_{avion['id']}_t{t}", f"Tareas_{avion['id']}_t{t}"]
            )

    # Restricción: Orden de las tareas (tipo 2 antes que tipo 1)
    def orden_tareas(tareas_actual, tareas_siguiente):
        t1_actual, t2_actual = tareas_actual
        t1_siguiente, t2_siguiente = tareas_siguiente
        # Tipo 2 debe completarse antes que tipo 1
        return (t2_actual > 0 and t2_siguiente < t2_actual) or \
               (t2_actual == 0 and t1_siguiente <= t1_actual)

    for avion in aviones:
        for t in range(franjas_horarias - 1):
            problem.addConstraint(
                orden_tareas,
                [f"Tareas_{avion['id']}_t{t}", f"Tareas_{avion['id']}_t{t+1}"]
            )

    # Restricción: Reducir dinámicamente las tareas pendientes según la ubicación asignada
    def reducir_tareas_dinamicamente(tareas_previas, ubicacion):
        tareas_tipo_1, tareas_tipo_2 = tareas_previas
        if ubicacion in talleres_spc and tareas_tipo_2 > 0:
            return (tareas_tipo_1, tareas_tipo_2 - 1)  # Completa una tarea tipo 2
        elif ubicacion in talleres_std + talleres_spc and tareas_tipo_1 > 0:
            return (tareas_tipo_1 - 1, tareas_tipo_2)  # Completa una tarea tipo 1
        return (tareas_tipo_1, tareas_tipo_2)  # No cambia si está en un parking
    
    for avion in aviones:
        for t in range(franjas_horarias - 1):
            def restriccion_transicion_tareas(tareas_previas, ubicacion, tareas_siguientes):
                resultado = reducir_tareas_dinamicamente(tareas_previas, ubicacion)
                print(f"Evaluando transiciones para Avión {avion['id']} en franja {t}: {tareas_previas} -> {ubicacion} -> {resultado}, esperado: {tareas_siguientes}")
                return resultado == tareas_siguientes
            
            problem.addConstraint(
                restriccion_transicion_tareas,
                [f"Tareas_{avion['id']}_t{t}", f"Avion_{avion['id']}_t{t}", f"Tareas_{avion['id']}_t{t+1}"]
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
    resolver_y_mostrar(problem, max_soluciones=1)

if __name__ == "__main__":
    main()




















# CARLOSSSSS
from constraint import *

def leer_datos_archivo(ruta_archivo):
    """Lee los datos del archivo de entrada y los estructura."""
    with open(ruta_archivo, 'r') as archivo:
        lineas = archivo.readlines()

    franjas_horarias = int(lineas[0].strip())
    tamanio_matriz = tuple(map(int, lineas[1].strip().split('x')))
    talleres_std = [tuple(map(int, coord[1:-1].split(','))) for coord in lineas[2].strip().replace('STD:', '').split()]
    talleres_spc = [tuple(map(int, coord[1:-1].split(','))) for coord in lineas[3].strip().replace('SPC:', '').split()]
    parkings = [tuple(map(int, coord[1:-1].split(','))) for coord in lineas[4].strip().replace('PRK:', '').split()]
    aviones = [linea.strip() for linea in lineas[5:]]

    return franjas_horarias, tamanio_matriz, talleres_std, talleres_spc, parkings, aviones

def crear_modelo(franjas_horarias, talleres_std, talleres_spc, parkings, aviones, debug=False):
    """Crea el modelo del problema usando python-constraint."""
    problem = Problem()

    # Inicializar tareas requeridas por cada avión
    tareas_por_avion = {}
    for avion in aviones:
        id_avion = avion.split('-')[0]
        t2 = int(avion.split('-')[3])  # Número de tareas tipo 2
        t1 = int(avion.split('-')[4])  # Número de tareas tipo 1
        tareas_por_avion[id_avion] = {"tipo_1": t1, "tipo_2": t2}

    # Crear variables para cada avión en cada franja horaria con dominios ajustados
    for avion in aviones:
        id_avion = avion.split('-')[0]
        tipo_tarea = avion.split('-')[2]  # Extraer si requiere tareas tipo 2 (T o F)
        if tipo_tarea == "T":
            dominios = talleres_spc  # Solo talleres especialistas para tareas tipo 2
        else:
            dominios = talleres_std + talleres_spc + parkings

        for franja in range(franjas_horarias):
            problem.addVariable(f"{id_avion}franja{franja}", dominios)

    if debug:
        print("Variables creadas con dominios ajustados.")

    # Restricción 1: Cada posición puede tener un único avión por franja horaria
    for franja in range(franjas_horarias):
        variables_franja = [f"{avion.split('-')[0]}franja{franja}" for avion in aviones]

        def no_repetidos(*asignaciones):
            return len(set(asignaciones)) == len(asignaciones)

        problem.addConstraint(no_repetidos, variables_franja)

    if debug:
        print("Restricción 1 aplicada.")

    # Restricción 2: Capacidad máxima de los talleres
    talleres = talleres_std + talleres_spc
    for franja in range(franjas_horarias):
        for taller in talleres:
            def capacidad_taller(*asignaciones):
                asignados = [a for a in asignaciones if a == taller]
                jumbos = sum(1 for a in asignados if a in talleres_spc)
                return len(asignados) <= 2 and jumbos <= 1

            variables_taller = [f"{avion.split('-')[0]}franja{franja}" for avion in aviones]
            problem.addConstraint(capacidad_taller, variables_taller)

    if debug:
        print("Restricción 2 aplicada.")

    # Restricción 3: Compatibilidad de talleres y tareas
    for avion in aviones:
        id_avion = avion.split('-')[0]
        tipo_tarea = avion.split('-')[2]  # Extraer si requiere tareas tipo 2 (T o F)
        if tipo_tarea == "T":
            for franja in range(franjas_horarias):
                def solo_talleres_especialistas(asignacion, talleres_spc=talleres_spc):
                    return asignacion in talleres_spc

                problem.addConstraint(
                    solo_talleres_especialistas,
                    [f"{id_avion}franja{franja}"]
                )

    if debug:
        print("Restricción 3 aplicada.")

    # Restricción 4: Orden y contabilización de las tareas
    for avion in aviones:
        id_avion = avion.split('-')[0]
        t2 = tareas_por_avion[id_avion]["tipo_2"]
        t1 = tareas_por_avion[id_avion]["tipo_1"]

        # Franjas para tareas tipo 2
        for franja in range(t2):
            def tareas_tipo2(asignacion, talleres_spc=talleres_spc):
                return asignacion in talleres_spc

            problem.addConstraint(
                tareas_tipo2,
                [f"{id_avion}franja{franja}"]
            )

        # Franjas para tareas tipo 1
        for franja in range(t2, t2 + t1):
            def tareas_tipo1(asignacion, talleres=talleres_std + talleres_spc):
                return asignacion in talleres

            problem.addConstraint(
                tareas_tipo1,
                [f"{id_avion}franja{franja}"]
            )

    if debug:
        print("Restricción 4 aplicada.")

    # Actualizar dinámicamente las tareas pendientes
    def actualizar_tareas(*asignaciones):
        tareas_restantes = {avion: tareas_por_avion[avion].copy() for avion in tareas_por_avion}
        for franja, asignacion in enumerate(asignaciones):
            for avion, posicion in zip(aviones, asignacion):
                id_avion = avion.split('-')[0]
                if posicion in talleres_spc and tareas_restantes[id_avion]["tipo_2"] > 0:
                    tareas_restantes[id_avion]["tipo_2"] -= 1
                elif posicion in talleres_std and tareas_restantes[id_avion]["tipo_1"] > 0:
                    tareas_restantes[id_avion]["tipo_1"] -= 1
        for avion, tareas in tareas_restantes.items():
            if tareas["tipo_2"] < 0 or tareas["tipo_1"] < 0:
                return False
        return True

    for franja in range(franjas_horarias):
        variables_franja = [f"{avion.split('-')[0]}franja{franja}" for avion in aviones]
        problem.addConstraint(actualizar_tareas, variables_franja)

    if debug:
        print("Tareas actualizadas dinámicamente.")

    # Restricción 5: Restricciones de maniobrabilidad
    movimientos = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for franja in range(franjas_horarias):
        variables_franja = [f"{avion.split('-')[0]}franja{franja}" for avion in aviones]

        def maniobrabilidad(*asignaciones):
            ocupadas = set(asignaciones)
            for asignacion in asignaciones:
                if asignacion is None:
                    continue
                x, y = asignacion
                # Generar posiciones adyacentes
                adyacentes = {(x + dx, y + dy) for dx, dy in movimientos}
                # Verificar que al menos una adyacente no esté ocupada
                if adyacentes.issubset(ocupadas):
                    return False  # Todas las adyacentes están ocupadas
            return True

        # Añadir restricción con addConstraint
        problem.addConstraint(maniobrabilidad, variables_franja)

    if debug:
        print("Restricción 5 aplicada.")

    # Restricción 6: Separación entre JUMBOS
    movimientos = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    aviones_jumbo = [avion for avion in aviones if avion.split('-')[1] == "JMB"]
    for franja in range(franjas_horarias):
        variables_franja = [f"{avion.split('-')[0]}franja{franja}" for avion in aviones_jumbo]

        def separacion_jumbos(*asignaciones):
            ocupadas = set(asignaciones)
            for asignacion in asignaciones:
                if asignacion is None:
                    continue
                (x, y) = asignacion
                adyacentes_ocupadas = any((x + dx, y + dy) in ocupadas for dx, dy in movimientos)
                if adyacentes_ocupadas:
                    return False
            return True

        problem.addConstraint(separacion_jumbos, variables_franja)

    if debug:
        print("Restricción 6 aplicada.")

    return problem

def guardar_resultados(ruta_salida, soluciones):
    """Guarda las soluciones encontradas en un archivo CSV."""
    with open(ruta_salida, 'w') as archivo:
        archivo.write(f"N. Sol: {len(soluciones)}\n")
        for i, solucion in enumerate(soluciones, start=1):
            archivo.write(f"Solución {i}:\n")
            for avion in sorted(solucion.keys()):  # Ordenar por clave (avión y franja)
                archivo.write(f"{avion}: {solucion[avion]}\n")

if __name__ == "_main_":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python CSPMaintenance.py <path maintenance>")
        sys.exit(1)

    ruta_entrada = sys.argv[1]
    ruta_salida = ruta_entrada.replace('.txt', '.csv')

    # Leer datos del archivo
    franjas_horarias, tamanio_matriz, talleres_std, talleres_spc, parkings, aviones = leer_datos_archivo(ruta_entrada)

    # Crear modelo y resolver
    problema = crear_modelo(franjas_horarias, talleres_std, talleres_spc, parkings, aviones, debug=True)

    # Reducir el número de soluciones computadas para evitar tiempos largos
    soluciones = problema.getSolutions()[:10]

    # Guardar resultados
    guardar_resultados(ruta_salida, soluciones)

    print(f"Resultados guardados en {ruta_salida}")





    ##### Cosas 

        def criterio_asignacion_logica(valor, estado_ubicaciones, franja):
            """
            Evalúa una asignación tentativa considerando el estado de ocupación de las ubicaciones.
            - Aviones sin tareas -> Parking libre.
            - Aviones con tareas -> Taller disponible, si no, Parking libre.
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
                return tipo_ubicacion == "SPC" and not ocupacion

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



















def restriccion_con_estado(valor, estado_ubicaciones, franja):
        """
        Evalúa una asignación considerando el estado dinámico de las ubicaciones.
        """
        posicion = valor["posicion"]
        tipo_ubicacion = valor["tipo_ubicacion"]
        tareas_tipo_1 = valor["tareas_tipo_1"]
        tareas_tipo_2 = valor["tareas_tipo_2"]

        # Verificar si la posición está ocupada
        if estado_ubicaciones[franja][posicion]["ocupado"]:
            return False

        # Lógica para asignación válida
        asignacion_valida = False
        if tareas_tipo_1 == 0 and tareas_tipo_2 == 0 and tipo_ubicacion == "PRK":
            asignacion_valida = True
        elif tareas_tipo_2 > 0 and tipo_ubicacion == "SPC":
            asignacion_valida = True
        elif tareas_tipo_1 > 0 and tipo_ubicacion in ["STD", "SPC"]:
            asignacion_valida = True

        # Si es válida, actualizar el estado
        if asignacion_valida:
            actualizar_estado(estado_ubicaciones, franja, posicion, valor["id_avion"], tipo_ubicacion)
            return True

        # Si no es válida, liberar el estado
        liberar_estado(estado_ubicaciones, franja, posicion)
        return False


    # Aplicar restricciones dinámicas al CSP
    for avion in aviones:
        for franja in range(franjas_horarias):
            variable = f"Avion_{avion['id']}_t{franja}"
            problem.addConstraint(
                lambda valor, estado=estado_ubicaciones, t=franja: restriccion_con_estado(valor, estado, t),
                [variable]
            )


    def actualizar_estado(estado_ubicaciones, franja, posicion, id_avion, tipo_ubicacion):
        """
        Marca una posición como ocupada por un avión en una franja horaria específica.
        """
        estado_ubicaciones[franja][posicion]["ocupado"] = True
        estado_ubicaciones[franja][posicion]["id_avion"] = id_avion
        estado_ubicaciones[franja][posicion]["tipo_ubicacion"] = tipo_ubicacion


    def liberar_estado(estado_ubicaciones, franja, posicion):
        """
        Libera una posición ocupada en una franja horaria específica.
        """
        estado_ubicaciones[franja][posicion]["ocupado"] = False
        estado_ubicaciones[franja][posicion]["id_avion"] = None
        estado_ubicaciones[franja][posicion]["tipo_ubicacion"] = None