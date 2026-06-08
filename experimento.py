class Experimento:
    def __init__(self, cliente_llm, modelo="Modelo_XYZ"):

        self.cliente_llm = cliente_llm

        self.modelo = modelo

    def generar_salida(self, messages):

        salida, tiempo = self.cliente_llm.generar_salida(messages)
        return salida, tiempo


    def ejecutar_dataset(self, dataset_generator, max_items=None):
        """
        dataset_generator: yield (entrada, contextoDinamico, esperado)
        """
        buffer_salidas = []
        step = 0
        fieldnames = ['step', 'entrada', 'contexto', 'salida', 'esperado', 'tiempo']

        trabajoEspecifico = "Eres un profesor experto en evaluación académica. Tu tarea es corregir respuestas de" \
        " estudiantes, vas a obtener un par [Pregunta, Respuesta] tu funcion es evaluar la respuesta a la pregunta." \
        " Proporciona una breve justificación de la nota indicando los conceptos correctamente mencionados, " \
        "los errores detectados y los conceptos importantes que faltan. Además, asigna una calificación numérica " \
        "entre 0 y 10, donde 0 representa una respuesta completamente incorrecta o vacía y 10 una respuesta " \
        "completamente correcta y completa. Analiza la precisión conceptual, la completitud de la respuesta, " \
        "el uso correcto de la terminología y la claridad de la explicación."

        contextoEstatico = "Para que utilices como contexto tienes a continuacion las respuestas ideales a las " \
        "preguntas: [Pregunta: Explica el ciclo TDD  y su importancia en el desarrollo de software., " \
        "RespuestaIdeal: El ciclo TDD consiste en tres etapas: primero, se escribe un test que falla (Rojo) porque" \
        " la funcionalidad aún no ha sido implementada. En la segunda fase (Verde), se desarrolla el mínimo " \
        "código necesario para que el test pase. Finalmente, en la etapa de Refactor, se mejora el código " \
        "manteniendo todos los tests en verde. Este ciclo es crucial ya que promueve un desarrollo proactivo, " \
        "asegurando que el código producido cumple con las especificaciones definidas inicialmente por los tests.]" \
        "[Pregunta: Explica la importancia de validar entradas en el contexto de TDD y cómo se relaciona con la robustez del software.," \
        "RespuestaIdeal: Validar entradas es crucial en TDD porque ayuda a prevenir errores y comportamientos inesperados" \
        " en el software. Al escribir tests para validar las entradas antes de implementar la lógica del negocio, " \
        "se aseguran condiciones adecuadas para el funcionamiento del código. Esto se traduce en un software más " \
        "robusto, ya que se minimizan los casos de errores en tiempo de ejecución. La validación en TDD no solo mejora" \
        " la calidad del código, sino que también facilita el mantenimiento y la comprensión del mismo.]" \
        "[Pregunta: Describe las buenas prácticas en TDD y su impacto en la calidad del software.," \
        "ResuestaIdeal: Las buenas prácticas en TDD incluyen escribir solo los tests necesarios para que fallen, " \
        "evitar la duplicación de código y refactorizar regularmente. Estas prácticas aseguran que el desarrollo " \
        "se mantenga enfocado y eficiente, reduciendo la complejidad del código y mejorando su mantenibilidad." \
        " Al seguir estas guías, se promueve la creación de un software más robusto y de alta calidad, ya que" \
        " cada unidad de código está respaldada por pruebas que garantizan su correcto funcionamiento.]" \
        "[Pregunta: Compara TDD con un enfoque tradicional de testing en el desarrollo de software.," \
        "RespuestaIdeal: TDD y el enfoque tradicional de testing difieren fundamentalmente en su secuencia y propósito." \
        " En TDD, los tests se escriben antes del código, sirviendo como especificación y guía para el desarrollo." \
        " En contraste, en un enfoque tradicional, primero se desarrolla el código y luego se realizan pruebas," \
        " lo que puede llevar a una verificación reactiva. Además, en TDD, los tests son obligatorios y ayudan a" \
        " prevenir errores desde el inicio, mientras que en el enfoque tradicional, los tests pueden ser opcionales" \
        " y se utilizan para validar el trabajo ya realizado.]"
        
        dataset_generator.crear_csv_resultados(fieldnames)

        for entrada, contextoDinamico, esperado in dataset_generator.dataset_batch():

            # corte opcional (para testing o batch controlado)
            if max_items and step >= max_items:
                break

            messagesForLLM = [ trabajoEspecifico, contextoEstatico, contextoDinamico,  entrada]

            salida, tiempo = self.generar_salida(messagesForLLM)

            print(f"Progreso: {step + 1} ejemplos procesados")

            # Usar diccionario 
            buffer_salidas.append({
                'step': step,
                'entrada': [contextoDinamico, entrada],
                'contexto': [trabajoEspecifico, contextoEstatico],
                'salida': salida,
                'esperado': esperado,
                'tiempo': tiempo
            })
            
            # Flush cada 50 elementos
            if len(buffer_salidas) >= 20:
                dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()
                print(f"Progreso: {step + 1} ejemplos procesados")
            
            step += 1
        
        # Flush final
        if buffer_salidas:
            dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)


