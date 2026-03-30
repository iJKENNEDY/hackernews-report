"""Simple i18n support for HackerNews Report."""

from flask import request

TRANSLATIONS = {
    'es': {
        'nav_hn': '🟠 Post HN',
        'nav_personal': '🖊️ Post Personal',

        'fav_title': '⭐ Mis Favoritos',
        'fav_all': '📋 Todos',
        'fav_general': '⭐ General',
        'fav_manage': '⚙️ Gestionar Grupos',

        'cat_title': 'Categorías',
        'cat_all': 'Todos los Posts',
        'cat_story': '📖 Historias',
        'cat_job': '💼 Empleos',
        'cat_ask': '❓ Ask/Show HN',
        'cat_poll': '📊 Encuestas',
        'cat_other': '📝 Otros',

        'tags_title': 'Etiquetas Populares',
        
        'filters_title': 'Filtros',
        'filter_ai_on': '✅ Resaltado IA (Activado)',
        'filter_ai_off': '⬜ Resaltado IA (Desactivado)',
        'filter_pdf_on': '📄 Solo PDFs (Activado)',
        'filter_pdf_off': '📄 Solo PDFs (Desactivado)',

        'export_title': 'Exportar Reporte',
        'blogs_title': 'Blogs de Investigación',

        'btn_refresh': 'Actualizar Posts',
        'btn_refreshing': 'Actualizando...',
        'btn_refresh_done': '¡Listo!',
        'btn_refresh_error': 'Error',
        'toast_refresh_ok': 'Actualizacion completada: {count} {noun}.',
        'toast_refresh_ok_fallback': 'Actualizacion completada.',
        'toast_refresh_err': 'No se pudieron actualizar los posts.',
        'toast_post_singular': 'post nuevo',
        'toast_post_plural': 'posts nuevos',

        'view_list': 'Vista lista',
        'view_grid': 'Vista grilla',

        'post_points': 'puntos',
        'post_by': 'por',

        'empty_fav_title': 'No hay favoritos aún',
        'empty_fav_desc': 'Haz clic en el ❤️ de cualquier post para agregarlo a tus favoritos.',
        'empty_posts_title': 'No se encontraron posts',
        'empty_posts_desc': 'Intenta obtener posts desde la CLI:',

        'page_prev': '← Anterior',
        'page_next': 'Siguiente →',

        'modal_group_title': '⚙️ Gestionar Grupos de Favoritos',
        'modal_group_name': 'Nombre del grupo...',
        'modal_group_parent': '(Sin padre)',
        'modal_group_create': '+ Crear',
        'modal_group_loading': 'Cargando...',
        'modal_group_empty': 'No hay grupos creados aún.',

        'fav_add': 'Agregar a favoritos',
        'fav_remove': 'Quitar de favoritos',
        'fav_dropdown': 'Agregar a grupo:',

        'personal_title': 'Mis Posts Personales',
        'personal_new': '+ Nuevo Post',
        'personal_desc': 'Gestiona tus propios posts de interés, enlaces y notas.',
        
        'search_results': 'Resultados de búsqueda:'
    },
    'en': {
        'nav_hn': '🟠 HN Posts',
        'nav_personal': '🖊️ Personal Posts',

        'fav_title': '⭐ My Favorites',
        'fav_all': '📋 All',
        'fav_general': '⭐ General',
        'fav_manage': '⚙️ Manage Groups',

        'cat_title': 'Categories',
        'cat_all': 'All Posts',
        'cat_story': '📖 Stories',
        'cat_job': '💼 Jobs',
        'cat_ask': '❓ Ask/Show HN',
        'cat_poll': '📊 Polls',
        'cat_other': '📝 Other',

        'tags_title': 'Popular Tags',
        
        'filters_title': 'Filters',
        'filter_ai_on': '✅ AI Highlighting (On)',
        'filter_ai_off': '⬜ AI Highlighting (Off)',
        'filter_pdf_on': '📄 PDFs Only (On)',
        'filter_pdf_off': '📄 PDFs Only (Off)',

        'export_title': 'Export Report',
        'blogs_title': 'Research Blogs',

        'btn_refresh': 'Refresh Posts',
        'btn_refreshing': 'Refreshing...',
        'btn_refresh_done': 'Done!',
        'btn_refresh_error': 'Error',
        'toast_refresh_ok': 'Refresh completed: {count} {noun}.',
        'toast_refresh_ok_fallback': 'Refresh completed.',
        'toast_refresh_err': 'Could not refresh posts.',
        'toast_post_singular': 'new post',
        'toast_post_plural': 'new posts',

        'view_list': 'List view',
        'view_grid': 'Grid view',

        'post_points': 'points',
        'post_by': 'by',

        'empty_fav_title': 'No favorites yet',
        'empty_fav_desc': 'Click the ❤️ on any post to add it to your favorites.',
        'empty_posts_title': 'No posts found',
        'empty_posts_desc': 'Try fetching posts using the CLI:',

        'page_prev': '← Previous',
        'page_next': 'Next →',

        'modal_group_title': '⚙️ Manage Favorite Groups',
        'modal_group_name': 'Group name...',
        'modal_group_parent': '(No parent)',
        'modal_group_create': '+ Create',
        'modal_group_loading': 'Loading...',
        'modal_group_empty': 'No groups created yet.',

        'fav_add': 'Add to favorites',
        'fav_remove': 'Remove from favorites',
        'fav_dropdown': 'Add to group:',

        'personal_title': 'My Personal Posts',
        'personal_new': '+ New Post',
        'personal_desc': 'Manage your own posts of interest, links, and notes.',
        
        'search_results': 'Search Results:'
    }
}

def get_locale():
    # Attempt to get language from cookie, default to es (Spanish)
    return request.cookies.get('lang', 'es')

def gettext(key, **kwargs):
    lang = get_locale()
    dictionary = TRANSLATIONS.get(lang, TRANSLATIONS['es'])
    text = dictionary.get(key, key)
    # Simple kwargs interpolation if needed
    for k, v in kwargs.items():
        text = text.replace(f'{{{k}}}', str(v))
    return text
