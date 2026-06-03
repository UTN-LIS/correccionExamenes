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

        contextoEstatico = "Eres un profesor experto en evaluación académica. Tu tarea es corregir respuestas de estudiantes comparándolas con ejemplos de correcciones reales. Analiza la precisión conceptual, la completitud de la respuesta, el uso correcto de la terminología y la claridad de la explicación. Proporciona una breve justificación de la nota indicando los conceptos correctamente mencionados, los errores detectados y los conceptos importantes que faltan. Además, asigna una calificación numérica entre 0 y 10, donde 0 representa una respuesta completamente incorrecta o vacía y 10 una respuesta completamente correcta y completa."
        respuestaIdeal = "Ejemplos de corrección: Respuesta del estudiante: Los asserts o aserciones son métodos que permiten comprobar la validez de un dato o de una variable, entre otras cosas. Los asserts se emplean dentro de los tests para poder comprobar el correcto funcionamiento de los métodos codificados, pudiendo usar un assertTrue(valorEsperado, valorRecibido) para validar que lo que devuelve una función es lo mismo que se esperaba según la lógica definida del software. También pueden utilizarse para comprobar que el resultado de un método no es nulo o para verificar condiciones verdaderas o falsas mediante distintas aserciones. Son importantes porque constituyen el mecanismo que permite comprobar automáticamente que el código se comporta según lo esperado. Evaluación: Nota: 9 Justificación: La respuesta explica correctamente qué son las aserciones, cómo se utilizan dentro de los tests y por qué son importantes para verificar el comportamiento del software. Además, proporciona ejemplos concretos de uso, como la comparación de valores, la comprobación de valores nulos y la validación de condiciones booleanas. Aunque la explicación es sólida y técnicamente correcta, podría ampliarse mencionando otros tipos de aserciones, como la verificación de excepciones o su papel dentro de metodologías de desarrollo guiado por pruebas. Por ello, no alcanza la puntuación máxima. Respuesta del estudiante: Las assertions se pueden usar en los test para validar y comparar objetos o valores. Esto es importante porque, si una aserción falla, el test también falla. Esto ayuda a detectar errores en el código y a comprender mejor el comportamiento del programa. Evaluación: Nota: 6 Justificación: La respuesta identifica correctamente que las aserciones sirven para comparar valores u objetos y que un fallo en una aserción provoca el fallo del test. Sin embargo, la explicación es breve y superficial. No desarrolla adecuadamente cómo las aserciones verifican que el comportamiento real del código coincida con el esperado ni aporta ejemplos concretos de uso. La comprensión básica es correcta, pero faltan detalles relevantes para una evaluación más alta. Respuesta del estudiante: Se pueden utilizar por ejemplo cuando un campo no puede ser nulo, poniendo @NotNull para evitar campos vacíos y generar un error cuando no se cumple la condición. Evaluación: Nota: 2 Justificación: La respuesta confunde las aserciones utilizadas en pruebas de software con mecanismos de validación de datos, como la anotación @NotNull. Aunque menciona la comprobación de restricciones, no explica qué son las aserciones, cómo se utilizan dentro de los tests ni cuál es su función para verificar resultados esperados. La relación con el concepto evaluado es muy limitada, por lo que la calificación es baja."
        
        dataset_generator.crear_csv_resultados(fieldnames)

        for entrada, contextoDinamico, esperado in dataset_generator.dataset_batch():

            # corte opcional (para testing o batch controlado)
            if max_items and step >= max_items:
                break
            
            messagesForLLM = [ contextoEstatico, respuestaIdeal, contextoDinamico,  entrada]

            salida, tiempo = self.generar_salida(messagesForLLM)

            print(f"Progreso: {step + 1} ejemplos procesados")

            # Usar diccionario 
            buffer_salidas.append({
                'step': step,
                'entrada': entrada,
                'contexto': contextoDinamico,
                'salida': salida,
                'esperado': esperado,
                'tiempo': tiempo
            })
            
            # Flush cada 50 elementos
            if len(buffer_salidas) >= 50:
                dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)
                buffer_salidas.clear()
                print(f"Progreso: {step + 1} ejemplos procesados")
            
            step += 1
        
        # Flush final
        if buffer_salidas:
            dataset_generator.guardar_buffer_csv(buffer_salidas, fieldnames)


