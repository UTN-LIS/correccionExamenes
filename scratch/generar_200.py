import csv
import random

questions = [
    {
        "id": "Q004474161",
        "text": "Explica el ciclo TDD  y su importancia en el desarrollo de software.",
        "ideal": "El ciclo TDD consiste en tres etapas: primero, se escribe un test que falla (Rojo) porque la funcionalidad aún no ha sido implementada. En la segunda fase (Verde), se desarrolla el mínimo código necesario para que el test pase. Finalmente, en la etapa de Refactor, se mejora el código manteniendo todos los tests en verde. Este ciclo es crucial ya que promueve un desarrollo proactivo, asegurando que el código producido cumple con las especificaciones definidas inicialmente por los tests.",
        "templates": [
            (10.0, [
                "El ciclo TDD (Test-Driven Development) consta de tres pasos principales: Rojo (escribir un test que falle porque no hay código de producción), Verde (crear el código mínimo indispensable para que el test pase) y Refactor (mejorar la calidad y diseño del código eliminando duplicados y renombrando, sin modificar su comportamiento, con la seguridad de mantener los tests en verde). Su importancia radica en que invierte el proceso de desarrollo haciéndolo proactivo: los tests actúan como especificación del diseño, garantizando código modular y libre de complejidad técnica innecesaria.",
                "TDD o desarrollo guiado por pruebas se compone de un ciclo de tres etapas: Rojo, Verde y Refactor. En el Rojo se escribe una prueba automatizada que falla (pues no hay código para satisfacerla). En el Verde se implementa el mínimo código para que pase la prueba. En el Refactor se limpia y optimiza el diseño manteniendo el comportamiento. Su gran valor es proactivo, ya que los tests definen el diseño del software y previenen bugs desde el inicio.",
            ], "Respuesta excelente y completa. Explica las tres fases y la importancia como guía proactiva de diseño."),
            (8.0, [
                "El ciclo TDD consiste en Rojo, Verde y Refactor. En la fase roja escribimos un test que falle ya que la funcionalidad no existe. En la fase verde programamos el código justo para pasar ese test. En el refactor mejoramos el diseño del código sin alterar la funcionalidad. Es importante porque nos da un desarrollo guiado por pruebas, asegurando que todo lo que programamos esté verificado y sea más limpio.",
                "En TDD seguimos el ciclo de: 1. Rojo (escribir test que falla), 2. Verde (hacer código para que pase el test), 3. Refactor (mejorar y limpiar el código sin cambiar su funcionalidad). Es crucial en desarrollo porque previene errores y nos da confianza al hacer cambios futuros sobre el sistema.",
            ], "Muy buena explicación del ciclo rojo-verde-refactor y de su importancia. Podría añadir más detalle sobre cómo el test actúa como especificación de diseño."),
            (6.0, [
                "TDD se basa en tres fases: rojo (los tests fallan), verde (los tests pasan) y refactor (mejorar el código escrito). La importancia es que al hacer los tests antes del código, el programador tiene más claro lo que tiene que programar y se reducen los errores básicos del sistema.",
                "El ciclo TDD consiste en hacer primero las pruebas en rojo para ver que fallen, después hacer la implementación en verde para que pasen y finalmente refactorizar para limpiar el código. Ayuda a mejorar la calidad del software significativamente.",
            ], "Explicación correcta de las fases. Falta profundizar en el significado de la fase de refactorización y detallar más el carácter proactivo de la metodología."),
            (4.0, [
                "El ciclo TDD es rojo, verde y refactor. Haces el test, luego el código y después mejoras lo que hiciste. Es importante porque hace que el software tenga menos fallas y ande mejor.",
                "El ciclo TDD tiene 3 pasos: hacer el test para que falle (rojo), programar el código (verde) y después mejorar el código (refactor). La importancia es que ayuda a que el código esté más ordenado.",
            ], "Descripción muy superficial del ciclo. Falta explicar en qué consiste cada paso en detalle y por qué se escribe el test antes."),
            (3.0, [
                "TDD es un ciclo donde haces pruebas unitarias para ver que el código no tenga bugs antes de subirlo a producción.",
                "El ciclo TDD consiste en testear el código del programa usando un archivo de tests que verifica las variables.",
            ], "Menciona pruebas pero no describe las tres fases del ciclo TDD (rojo, verde, refactor) ni su importancia en el diseño del software."),
            (1.0, [
                "No sé qué es TDD ni el ciclo rojo verde, yo programo directamente el código y hago pruebas manuales.",
                "El ciclo TDD sirve para compilar el código de forma automática usando el compilador de Java.",
            ], "La respuesta no tiene relación con el ciclo TDD ni su importancia. Calificación mínima de 1.")
        ]
    },
    {
        "id": "Q799823558",
        "text": "Compara TDD con un enfoque tradicional de testing en el desarrollo de software.",
        "ideal": "TDD y el enfoque tradicional de testing difieren fundamentalmente en su secuencia y propósito. En TDD, los tests se escriben antes del código, sirviendo como especificación y guía para el desarrollo. En contraste, en un enfoque tradicional, primero se desarrolla el código y luego se realizan pruebas, lo que puede llevar a una verificación reactiva. Además, en TDD, los tests son obligatorios y ayudan a prevenir errores desde el inicio, mientras que en el enfoque tradicional, los tests pueden ser opcionales y se utilizan para validar el trabajo ya realizado.",
        "templates": [
            (9.0, [
                "En TDD, los tests se escriben al inicio y actúan como especificación de diseño, mientras que en el tradicional se escriben al final del desarrollo. Esto hace que TDD sea preventivo y guíe la arquitectura del código (menos acoplamiento). En el tradicional, el testing es reactivo y a veces opcional. Además, TDD asegura una cobertura del 100% de la funcionalidad implementada, mientras que en el tradicional suele ser parcial y más propensa a omitir casos críticos.",
                "La diferencia principal radica en la secuencia: TDD es 'test-first' (pruebas antes que código) y el tradicional es 'test-after' (código antes que pruebas). TDD utiliza los tests como una herramienta de diseño y especificación, logrando código más desacoplado y modular. Por otro lado, el enfoque tradicional valida el código de forma reactiva, donde los tests suelen ser opcionales y el diseño ya está predefinido, lo que dificulta hacer cambios.",
            ], "Excelente comparación en términos de secuencia, prevención vs reacción, e impacto en el diseño y la modularidad del código."),
            (7.0, [
                "En TDD primero se hacen las pruebas antes de escribir el código de producción, y en el tradicional primero se programa todo y después se prueban las funciones. La diferencia principal es el momento en que se escribe cada cosa. Además, en TDD los tests guían la escritura del código de producción mientras que en el tradicional solo validan.",
                "La diferencia es que TDD es proactivo (haces los tests antes de codificar la lógica) y el tradicional es reactivo (haces pruebas después de codificar). TDD asegura que escribas solo el código necesario, en cambio el enfoque tradicional puede llevar a escribir código de más que luego es difícil de testear.",
            ], "Buena comparación sobre el orden y el carácter proactivo vs reactivo. Podría profundizar más en cómo los tests en TDD actúan como especificación de diseño."),
            (5.0, [
                "La diferencia principal entre el enfoque tradicional de testing y el TDD consiste en el momento de elaboración de los tests, ya que en el primero se escribe el código y luego el test, al contrario que en el segundo. TDD ayuda a tener menos bugs porque los tests son obligatorios en cada fase.",
                "En TDD escribes las pruebas al principio y el código después. En el tradicional escribes todo el programa y al final haces los tests si hay tiempo. TDD es mejor porque te obliga a hacer las pruebas.",
            ], "Identifica la diferencia temporal básica, pero la comparación es poco profunda. Falta explicar el rol de los tests como guía de diseño y especificación."),
            (3.0, [
                "El enfoque tradicional es mejor porque no pierdes tiempo haciendo tests antes de saber si el código funciona. TDD es más lento y requiere escribir el doble de código.",
                "TDD es para proyectos ágiles y tradicional es para proyectos con metodología en cascada donde se testea al final.",
            ], "Muestra confusión sobre el propósito de TDD. Califica a TDD como 'más lento' o limitado a agilidad sin comparar técnicamente los beneficios de diseño o calidad."),
            (2.0, [
                "TDD y tradicional son dos herramientas para compilar programas de computadora.",
                "El testing tradicional es cuando haces pruebas con prints en la consola y TDD es cuando usas librerías.",
            ], "Respuesta incorrecta. No compara adecuadamente los conceptos de desarrollo guiado por pruebas y testing tradicional. Calificación de 2 por el leve intento conceptual."),
            (1.0, [
                "No sé cómo comparar el testing tradicional con TDD, no conozco ninguno de esos conceptos.",
                "El testing tradicional sirve para instalar sistemas operativos como Windows en la computadora.",
            ], "Respuesta completamente errónea o vacía. Calificación mínima de 1.")
        ]
    },
    {
        "id": "Q675600740",
        "text": "Describe las buenas prácticas en TDD y su impacto en la calidad del software.",
        "ideal": "Las buenas prácticas en TDD incluyen escribir solo los tests necesarios para que fallen, evitar la duplicación de código y refactorizar regularmente. Estas prácticas aseguran que el desarrollo se mantenga enfocado y eficiente, reduciendo la complejidad del código y mejorando su mantenibilidad. Al seguir estas guías, se promueve la creación de un software más robusto y de alta calidad, ya que cada unidad de código está respaldada por pruebas que garantizan su correcto funcionamiento.",
        "templates": [
            (8.0, [
                "Las buenas prácticas en TDD incluyen escribir únicamente el test mínimo necesario para que falle, evitar la duplicación de código en la fase de refactorización y mantener tests independientes y rápidos (regla FIRST). Estas prácticas tienen un impacto directo en la mantenibilidad y robustez del software, ya que reducen la complejidad técnica, aseguran una alta cobertura y permiten realizar cambios futuros con la confianza de no romper funcionalidades existentes.",
                "Algunas buenas prácticas de TDD son escribir pruebas pequeñas y específicas, no avanzar a la fase verde sin un test que falle, y refactorizar continuamente tanto el código como los tests. Su impacto en la calidad es muy alto: se reduce el acoplamiento, aumenta la cohesión del código y se facilita la mantenibilidad del software a largo plazo.",
            ], "Muy buena descripción de las buenas prácticas específicas de TDD y su impacto en la calidad y mantenibilidad del software."),
            (6.0, [
                "Una buena práctica en TDD es la regla FIRST: los tests deben ser rápidos, independientes, repetibles, autovalidables y oportunos. El impacto es positivo ya que al tener pruebas bien estructuradas la cobertura aumenta y hay menos bugs en el sistema.",
                "Las buenas prácticas son: hacer tests independientes, que no dependan del orden de ejecución, escribir código simple para pasar la prueba verde, y refactorizar siempre en cada ciclo. Esto impacta haciendo que el software sea robusto y libre de errores graves.",
            ], "Menciona buenas prácticas válidas (como FIRST o refactorizar). Falta detallar más las prácticas del ciclo de desarrollo (escribir solo el test mínimo, evitar duplicidad) y su relación con el diseño del software."),
            (4.0, [
                "Como buena práctica hay que intentar escribir los tests antes de escribir la funcionalidad. El impacto que esto genera en el software es que el código queda más ordenado y con menos fallos.",
                "Las buenas prácticas de TDD son comentar los tests, ponerles nombres claros que describan qué hacen y correrlos siempre antes de hacer un commit. Esto ayuda a la calidad del código.",
            ], "Se enfoca en aspectos muy generales de la programación o testing, sin abordar las buenas prácticas del flujo interno de TDD ni detallar su impacto real en la calidad."),
            (2.0, [
                "Las buenas prácticas en TDD son tener una computadora rápida para correr las pruebas y usar un buen IDE para refactorizar de forma automática.",
                "El impacto en la calidad es que el programa no se rompe y no tiene bugs de sintaxis al ejecutarse.",
            ], "Conceptos incorrectos o extremadamente superficiales sobre lo que constituyen las buenas prácticas en TDD. Calificación de 2."),
            (1.0, [
                "TDD no tiene buenas prácticas, es simplemente escribir código sin importar el diseño.",
                "Las buenas prácticas son no hacer tests para avanzar más rápido en el proyecto.",
            ], "La respuesta contradice la metodología TDD o carece de sentido conceptual. Calificación mínima de 1.")
        ]
    },
    {
        "id": "Q205293180",
        "text": "Explica la importancia de validar entradas en el contexto de TDD y cómo se relaciona con la robustez del software.",
        "ideal": "Validar entradas es crucial en TDD porque ayuda a prevenir errores y comportamientos inesperados en el software. Al escribir tests para validar las entradas antes de implementar la lógica del negocio, se aseguran condiciones adecuadas para el funcionamiento del código. Esto se traduce en un software más robusto, ya que se minimizan los casos de errores en tiempo de ejecución. La validación en TDD no solo mejora la calidad del código, sino que también facilita el mantenimiento and la comprensión del mismo.",
        "templates": [
            (8.0, [
                "La validación de entradas en TDD nos obliga a escribir pruebas para valores límite (números negativos, cadenas vacías, formatos incorrectos) antes de codificar la lógica del negocio. Al asegurar estas validaciones por test, evitamos errores imprevistos en producción. Esto hace que el código sea mucho más robusto frente a fallos y fácil de mantener.",
                "Validar entradas en TDD es crucial para definir claramente el comportamiento de los métodos ante datos incorrectos o maliciosos desde la fase roja. Esto se relaciona directamente con la robustez del software, ya que previene fallos inesperados en tiempo de ejecución (como NullPointerExceptions o divisiones por cero) y asegura un diseño tolerante a fallos.",
            ], "Muy buena explicación sobre la importancia de definir validaciones mediante pruebas iniciales y su relación directa con la robustez."),
            (6.0, [
                "Es importante validar las entradas porque si no el programa puede romperse cuando el usuario ingresa datos incorrectos. Escribiendo tests para esto en TDD aseguramos que el sistema no falle ante datos inválidos y sea más robusto.",
                "En TDD validamos las entradas haciendo pruebas para los casos en que el usuario ponga datos malos, por ejemplo letras en campos numéricos. Esto ayuda a la robustez del código ya que el programa no se colgará fácilmente.",
            ], "Explica de forma correcta la relación de la validación con evitar fallos del usuario. Podría profundizar más en la relación específica con el flujo TDD (test-first)."),
            (4.0, [
                "Validar entradas sirve para que no pongas letras en lugar de números en el formulario. Eso hace que el programa ande mejor y sea más robusto.",
                "Es importante validar las entradas porque si el software recibe datos incorrectos puede dar un error en la base de datos.",
            ], "Explicación muy genérica de validación de entradas. No hace ninguna mención al contexto de TDD (pruebas previas, diseño de interfaces)."),
            (2.0, [
                "Validar entradas sirve para que el usuario no pueda ingresar números negativos en los campos de texto del formulario HTML.",
                "En TDD las validaciones de entrada se hacen de forma manual al final del proyecto.",
            ], "Respuesta muy limitada o con conceptos equivocados sobre cómo y cuándo se validan las entradas en TDD. Calificación de 2."),
            (1.0, [
                "No comprendo cómo se validan las entradas ni qué relación tiene con la robustez del software.",
                "La validación de entradas sirve para configurar la base de datos de Oracle en un servidor Linux local.",
            ], "Respuesta completamente errónea o vacía. Calificación mínima de 1.")
        ]
    }
]

# Generate 201 rows
rows = []
random.seed(42)

for entry_id in range(201):
    # Select question
    q_idx = entry_id % len(questions)
    q = questions[q_idx]
    
    # Choose a grade level templates
    level = random.choice(q["templates"])
    grade = level[0]
    ans_options = level[1]
    feedback = level[2]
    
    # Select answer and add subtle variations to ensure unique texts
    base_ans = random.choice(ans_options)
    
    # Diverse prefixes and minor additions to make answers unique
    prefixes = [
        "", "En mi opinión, ", "Considero que ", "Para responder a esto: ",
        "Básicamente, ", "Desde mi punto de vista, ", "En el desarrollo, "
    ]
    suffixes = [
        "", " Esto es fundamental.", " De esta manera funciona.",
        " Es un concepto clave.", " Así lo veo yo.", " Queda claro su beneficio."
    ]
    
    prefix = random.choice(prefixes) if len(base_ans) < 500 else ""
    suffix = random.choice(suffixes) if len(base_ans) < 500 else ""
    
    student_ans = f"{prefix}{base_ans}{suffix}".strip()
    student_ans = student_ans.replace("\n", " ")
    
    rows.append({
        "entry_id": entry_id,
        "question_id": q["id"],
        "question_text": q["text"],
        "student_answer": student_ans,
        "ideal_answer": q["ideal"],
        "student_answer_length": len(student_ans),
        "teacher_grade": grade,
        "teacher_feedback": feedback
    })

# Write to CSV
with open("/home/franco-sosa/Documentos/correccionExamenes/documentacion/dataset_simulado_pruebas.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["entry_id", "question_id", "question_text", "student_answer", "ideal_answer", "student_answer_length", "teacher_grade", "teacher_feedback"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("CSV generado exitosamente con 201 registros (escala estricta de 1 a 10).")
