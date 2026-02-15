# Documento de Requisitos

## Introducción

Este documento especifica los requisitos para una aplicación que obtiene, categoriza y visualiza posts de Hacker News. La aplicación permitirá a los usuarios consultar posts de Hacker News, organizarlos por categorías y almacenarlos localmente en una base de datos SQLite para consultas posteriores.

## Glosario

- **Sistema**: La aplicación completa de reporte de Hacker News
- **API_HN**: La API pública de Hacker News (https://github.com/HackerNews/API)
- **Post**: Una publicación de Hacker News que puede ser una historia (story), comentario, trabajo (job), pregunta (ask) o encuesta (poll)
- **Categoría**: Clasificación de posts basada en su tipo (story, job, ask, poll)
- **Base_de_Datos**: Base de datos SQLite local que almacena los posts obtenidos
- **Lista**: Visualización ordenada de posts en la interfaz de usuario

## Requisitos

### Requisito 1: Obtención de Posts desde Hacker News

**Historia de Usuario:** Como usuario, quiero obtener posts de Hacker News, para poder acceder a contenido actualizado de la plataforma.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ conectarse a la API_HN para obtener posts
2. CUANDO se solicite obtener posts, EL Sistema DEBERÁ recuperar al menos los campos: id, título, autor, puntuación, URL, fecha de creación y tipo
3. CUANDO la API_HN no esté disponible, EL Sistema DEBERÁ registrar el error y notificar al usuario
4. EL Sistema DEBERÁ manejar límites de tasa (rate limits) de la API_HN de manera apropiada
5. CUANDO se obtengan posts, EL Sistema DEBERÁ validar que los datos recibidos sean completos antes de procesarlos

### Requisito 2: Almacenamiento en Base de Datos SQLite

**Historia de Usuario:** Como usuario, quiero que los posts se almacenen localmente, para poder consultarlos sin necesidad de conexión a internet.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ crear una Base_de_Datos SQLite si no existe
2. CUANDO se obtenga un post, EL Sistema DEBERÁ almacenarlo en la Base_de_Datos con todos sus campos
3. CUANDO se intente almacenar un post duplicado (mismo id), EL Sistema DEBERÁ actualizar el post existente en lugar de crear uno nuevo
4. EL Sistema DEBERÁ mantener índices en los campos id y tipo para optimizar consultas
5. CUANDO se almacenen datos, EL Sistema DEBERÁ validar la integridad de los datos antes de la inserción

### Requisito 3: Categorización de Posts

**Historia de Usuario:** Como usuario, quiero que los posts se organicen por categorías, para poder filtrar y encontrar contenido específico fácilmente.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ clasificar cada post en una categoría basada en su tipo (story, job, ask, poll)
2. CUANDO se almacene un post, EL Sistema DEBERÁ asignarle su categoría correspondiente
3. EL Sistema DEBERÁ permitir consultar posts filtrados por categoría
4. CUANDO un post no tenga un tipo reconocido, EL Sistema DEBERÁ asignarlo a una categoría "otros"

### Requisito 4: Visualización de Posts en Listas

**Historia de Usuario:** Como usuario, quiero visualizar los posts en listas organizadas, para poder navegar y leer el contenido de manera eficiente.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ mostrar posts en formato de lista con información clave visible (título, autor, puntuación, fecha)
2. CUANDO se visualice una lista, EL Sistema DEBERÁ ordenar los posts por fecha de creación (más recientes primero) por defecto
3. EL Sistema DEBERÁ permitir al usuario filtrar la visualización por categoría
4. CUANDO se muestre un post con URL, EL Sistema DEBERÁ hacer el enlace clickeable
5. EL Sistema DEBERÁ mostrar la categoría de cada post en la lista

### Requisito 5: Sincronización y Actualización de Datos

**Historia de Usuario:** Como usuario, quiero poder actualizar los datos de Hacker News, para mantener mi base de datos local sincronizada con contenido reciente.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ proporcionar una función para obtener posts nuevos desde la API_HN
2. CUANDO se ejecute una actualización, EL Sistema DEBERÁ obtener posts que no existan en la Base_de_Datos
3. CUANDO se complete una actualización, EL Sistema DEBERÁ informar al usuario cuántos posts nuevos se obtuvieron
4. EL Sistema DEBERÁ permitir al usuario especificar cuántos posts obtener en cada actualización

### Requisito 6: Manejo de Errores y Resiliencia

**Historia de Usuario:** Como usuario, quiero que la aplicación maneje errores de manera apropiada, para tener una experiencia confiable incluso cuando ocurran problemas.

#### Criterios de Aceptación

1. SI la conexión a la API_HN falla, ENTONCES EL Sistema DEBERÁ reintentar la solicitud hasta 3 veces con espera exponencial
2. CUANDO ocurra un error de base de datos, EL Sistema DEBERÁ registrar el error con detalles suficientes para diagnóstico
3. SI los datos recibidos de la API_HN están incompletos o son inválidos, ENTONCES EL Sistema DEBERÁ omitir ese post y continuar procesando los demás
4. EL Sistema DEBERÁ mantener la integridad de la Base_de_Datos incluso si el proceso de actualización se interrumpe
