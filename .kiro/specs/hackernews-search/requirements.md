# Documento de Requisitos

## Introducción

Este documento especifica los requisitos para un sistema de búsqueda de posts de Hacker News almacenados localmente. El buscador permitirá a los usuarios encontrar posts específicos usando múltiples criterios de búsqueda (texto, autor, tags, puntuación, fecha) y visualizar resultados ordenados y paginados. El sistema se integrará con la aplicación existente de Hackernews Report que almacena posts en una base de datos SQLite.

## Glosario

- **Sistema_de_Búsqueda**: El módulo completo de búsqueda de posts de Hacker News
- **Base_de_Datos**: Base de datos SQLite local que almacena los posts obtenidos
- **Criterio_de_Búsqueda**: Parámetro de filtrado (texto, autor, tag, puntuación, fecha)
- **Consulta**: Conjunto de criterios de búsqueda especificados por el usuario
- **Resultado**: Post que coincide con los criterios de búsqueda especificados
- **Búsqueda_Parcial**: Búsqueda que encuentra coincidencias parciales en texto (ej: "python" encuentra "Python 3.11")
- **Paginación**: División de resultados en páginas de tamaño fijo
- **Relevancia**: Métrica que determina qué tan bien un post coincide con la consulta
- **Sistema_de_Tags**: Módulo existente en src/tags.py que asigna tags automáticos a posts
- **Índice**: Estructura de base de datos que optimiza consultas específicas
- **Resaltado**: Marcado visual de términos de búsqueda en los resultados

## Requisitos

### Requisito 1: Búsqueda por Texto en Título

**Historia de Usuario:** Como usuario, quiero buscar posts por palabras en el título, para encontrar contenido sobre temas específicos.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione un término de búsqueda de texto, EL Sistema_de_Búsqueda DEBERÁ buscar coincidencias en el campo título de los posts
2. EL Sistema_de_Búsqueda DEBERÁ realizar búsqueda insensible a mayúsculas/minúsculas
3. EL Sistema_de_Búsqueda DEBERÁ soportar búsqueda parcial (substring matching) en títulos
4. CUANDO un término de búsqueda contenga múltiples palabras, EL Sistema_de_Búsqueda DEBERÁ encontrar posts que contengan todas las palabras en cualquier orden
5. CUANDO un término de búsqueda esté vacío o sea solo espacios en blanco, EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta y notificar al usuario

### Requisito 2: Búsqueda por Autor

**Historia de Usuario:** Como usuario, quiero buscar posts por nombre de autor, para encontrar todo el contenido publicado por usuarios específicos.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione un nombre de autor, EL Sistema_de_Búsqueda DEBERÁ buscar coincidencias exactas en el campo autor de los posts
2. EL Sistema_de_Búsqueda DEBERÁ realizar búsqueda insensible a mayúsculas/minúsculas para nombres de autor
3. EL Sistema_de_Búsqueda DEBERÁ soportar búsqueda parcial en nombres de autor (ej: "john" encuentra "johnsmith")
4. CUANDO un nombre de autor no exista en la Base_de_Datos, EL Sistema_de_Búsqueda DEBERÁ retornar una lista vacía

### Requisito 3: Búsqueda por Tags

**Historia de Usuario:** Como usuario, quiero buscar posts por tags temáticos, para encontrar contenido categorizado por tecnología o tema.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione uno o más tags, EL Sistema_de_Búsqueda DEBERÁ buscar posts que contengan al menos uno de los tags especificados
2. EL Sistema_de_Búsqueda DEBERÁ utilizar el Sistema_de_Tags existente para validar que los tags proporcionados sean válidos
3. CUANDO se proporcionen múltiples tags, EL Sistema_de_Búsqueda DEBERÁ retornar posts que coincidan con cualquiera de los tags (operación OR)
4. EL Sistema_de_Búsqueda DEBERÁ permitir al usuario listar todos los tags disponibles
5. CUANDO un tag no exista en el Sistema_de_Tags, EL Sistema_de_Búsqueda DEBERÁ notificar al usuario y sugerir tags válidos

### Requisito 4: Búsqueda por Rango de Puntuación

**Historia de Usuario:** Como usuario, quiero filtrar posts por rango de puntuación, para encontrar contenido popular o de alta calidad.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione una puntuación mínima, EL Sistema_de_Búsqueda DEBERÁ retornar solo posts con puntuación mayor o igual al mínimo
2. CUANDO un usuario proporcione una puntuación máxima, EL Sistema_de_Búsqueda DEBERÁ retornar solo posts con puntuación menor o igual al máximo
3. CUANDO un usuario proporcione ambos límites (mínimo y máximo), EL Sistema_de_Búsqueda DEBERÁ retornar posts dentro del rango inclusivo
4. SI la puntuación mínima es mayor que la máxima, ENTONCES EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta y notificar al usuario
5. EL Sistema_de_Búsqueda DEBERÁ aceptar solo valores enteros no negativos para puntuaciones

### Requisito 5: Búsqueda por Rango de Fechas

**Historia de Usuario:** Como usuario, quiero filtrar posts por rango de fechas, para encontrar contenido reciente o de períodos específicos.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione una fecha de inicio, EL Sistema_de_Búsqueda DEBERÁ retornar solo posts creados en o después de esa fecha
2. CUANDO un usuario proporcione una fecha de fin, EL Sistema_de_Búsqueda DEBERÁ retornar solo posts creados en o antes de esa fecha
3. CUANDO un usuario proporcione ambas fechas (inicio y fin), EL Sistema_de_Búsqueda DEBERÁ retornar posts dentro del rango inclusivo
4. SI la fecha de inicio es posterior a la fecha de fin, ENTONCES EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta y notificar al usuario
5. EL Sistema_de_Búsqueda DEBERÁ aceptar fechas en formato ISO 8601 (YYYY-MM-DD)

### Requisito 6: Combinación de Múltiples Criterios

**Historia de Usuario:** Como usuario, quiero combinar múltiples criterios de búsqueda, para realizar búsquedas precisas y específicas.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione múltiples criterios de búsqueda, EL Sistema_de_Búsqueda DEBERÁ aplicar todos los criterios simultáneamente (operación AND)
2. EL Sistema_de_Búsqueda DEBERÁ permitir cualquier combinación válida de criterios (texto, autor, tags, puntuación, fecha)
3. CUANDO no se proporcione ningún criterio de búsqueda, EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta y notificar al usuario
4. CUANDO ningún post coincida con todos los criterios especificados, EL Sistema_de_Búsqueda DEBERÁ retornar una lista vacía con un mensaje informativo

### Requisito 7: Ordenamiento de Resultados

**Historia de Usuario:** Como usuario, quiero ordenar los resultados de búsqueda, para ver primero el contenido más relevante, reciente o popular.

#### Criterios de Aceptación

1. EL Sistema_de_Búsqueda DEBERÁ soportar ordenamiento por relevancia (coincidencia de términos de búsqueda)
2. EL Sistema_de_Búsqueda DEBERÁ soportar ordenamiento por fecha de creación (ascendente y descendente)
3. EL Sistema_de_Búsqueda DEBERÁ soportar ordenamiento por puntuación (ascendente y descendente)
4. CUANDO no se especifique un orden, EL Sistema_de_Búsqueda DEBERÁ ordenar por relevancia por defecto
5. CUANDO se busque solo por criterios no textuales (autor, tags, puntuación, fecha), EL Sistema_de_Búsqueda DEBERÁ ordenar por fecha descendente por defecto

### Requisito 8: Paginación de Resultados

**Historia de Usuario:** Como usuario, quiero ver resultados paginados, para navegar eficientemente por grandes conjuntos de resultados.

#### Criterios de Aceptación

1. EL Sistema_de_Búsqueda DEBERÁ dividir resultados en páginas de tamaño configurable
2. CUANDO un usuario solicite una página específica, EL Sistema_de_Búsqueda DEBERÁ retornar solo los resultados de esa página
3. EL Sistema_de_Búsqueda DEBERÁ proporcionar información sobre el número total de resultados y páginas disponibles
4. CUANDO un usuario solicite una página que no existe, EL Sistema_de_Búsqueda DEBERÁ retornar una lista vacía
5. EL Sistema_de_Búsqueda DEBERÁ usar un tamaño de página por defecto de 20 resultados

### Requisito 9: Resaltado de Términos de Búsqueda

**Historia de Usuario:** Como usuario, quiero ver los términos de búsqueda resaltados en los resultados, para identificar rápidamente las coincidencias.

#### Criterios de Aceptación

1. CUANDO se realice una búsqueda por texto, EL Sistema_de_Búsqueda DEBERÁ marcar los términos coincidentes en los títulos de los resultados
2. EL Sistema_de_Búsqueda DEBERÁ usar marcadores visuales claros para el resaltado (ej: **término** o colores en CLI)
3. EL Sistema_de_Búsqueda DEBERÁ resaltar todas las ocurrencias de los términos de búsqueda en cada resultado
4. CUANDO no haya búsqueda por texto, EL Sistema_de_Búsqueda NO DEBERÁ aplicar resaltado

### Requisito 10: Optimización con Índices

**Historia de Usuario:** Como desarrollador, quiero que las búsquedas sean eficientes, para proporcionar respuestas rápidas incluso con grandes volúmenes de datos.

#### Criterios de Aceptación

1. EL Sistema_de_Búsqueda DEBERÁ crear un Índice en el campo título para optimizar búsquedas de texto
2. EL Sistema_de_Búsqueda DEBERÁ crear un Índice en el campo autor para optimizar búsquedas por autor
3. EL Sistema_de_Búsqueda DEBERÁ crear un Índice en el campo tags para optimizar búsquedas por tags
4. EL Sistema_de_Búsqueda DEBERÁ crear un Índice en el campo score para optimizar filtros por puntuación
5. EL Sistema_de_Búsqueda DEBERÁ reutilizar el Índice existente en created_at para búsquedas por fecha
6. CUANDO se inicialice el esquema de búsqueda, EL Sistema_de_Búsqueda DEBERÁ crear todos los índices necesarios si no existen

### Requisito 11: Integración con CLI Existente

**Historia de Usuario:** Como usuario, quiero acceder al buscador desde la línea de comandos, para mantener consistencia con la interfaz existente.

#### Criterios de Aceptación

1. EL Sistema_de_Búsqueda DEBERÁ proporcionar un comando "search" en la CLI existente
2. EL Sistema_de_Búsqueda DEBERÁ aceptar todos los criterios de búsqueda como argumentos de línea de comandos
3. EL Sistema_de_Búsqueda DEBERÁ mostrar resultados en el mismo formato de tabla que el comando "list"
4. EL Sistema_de_Búsqueda DEBERÁ proporcionar mensajes de ayuda claros para todos los parámetros de búsqueda
5. CUANDO ocurra un error de búsqueda, EL Sistema_de_Búsqueda DEBERÁ mostrar mensajes de error descriptivos

### Requisito 12: Manejo de Errores y Validación

**Historia de Usuario:** Como usuario, quiero recibir mensajes claros cuando mis búsquedas tengan errores, para corregirlos fácilmente.

#### Criterios de Aceptación

1. CUANDO un usuario proporcione parámetros inválidos, EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta con un mensaje descriptivo
2. CUANDO un usuario proporcione un formato de fecha inválido, EL Sistema_de_Búsqueda DEBERÁ indicar el formato correcto esperado
3. CUANDO un usuario proporcione valores de puntuación negativos, EL Sistema_de_Búsqueda DEBERÁ rechazar la consulta
4. SI ocurre un error de base de datos durante la búsqueda, ENTONCES EL Sistema_de_Búsqueda DEBERÁ registrar el error y notificar al usuario
5. EL Sistema_de_Búsqueda DEBERÁ validar todos los parámetros antes de ejecutar la consulta en la Base_de_Datos
