import os

html_path = 'templates/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '⭐ Mis Favoritos': "{{ _('fav_title') }}",
    '📋 Todos': "{{ _('fav_all') }}",
    '⭐ General': "{{ _('fav_general') }}",
    '⚙️ Gestionar Grupos': "{{ _('fav_manage') }}",
    'Categorías': "{{ _('cat_title') }}", # Actually it is currently 'Categories' in html but we'll replace
    'Categories': "{{ _('cat_title') }}",
    'All Posts': "{{ _('cat_all') }}",
    '📖 Stories': "{{ _('cat_story') }}",
    '💼 Jobs': "{{ _('cat_job') }}",
    '❓ Ask/Show HN': "{{ _('cat_ask') }}",
    '📊 Polls': "{{ _('cat_poll') }}",
    '📝 Other': "{{ _('cat_other') }}",
    'Popular Tags': "{{ _('tags_title') }}",
    'Filters': "{{ _('filters_title') }}",
    '✅ AI Highlighting (On)': "{{ _('filter_ai_on') }}",
    '⬜ AI Highlighting (Off)': "{{ _('filter_ai_off') }}",
    '📄 Solo PDFs (On)': "{{ _('filter_pdf_on') }}",
    '📄 Solo PDFs (Off)': "{{ _('filter_pdf_off') }}",
    'Export Report': "{{ _('export_title') }}",
    'Blogs de Investigación': "{{ _('blogs_title') }}",
    'Actualizar Posts': "{{ _('btn_refresh') }}",
    'Actualizando...': "{{ _('btn_refreshing') }}",
    '¡Listo!': "{{ _('btn_refresh_done') }}",
    'Error al actualizar': "{{ _('btn_refresh_error') }}",
    'Vista lista': "{{ _('view_list') }}",
    'Vista grilla': "{{ _('view_grid') }}",
    'points': "{{ _('post_points') }}",
    'by ': "{{ _('post_by') }} ",
    'No hay favoritos aún': "{{ _('empty_fav_title') }}",
    'Haz clic en el ❤️ de cualquier post para agregarlo a tus favoritos.': "{{ _('empty_fav_desc') }}",
    'No posts found': "{{ _('empty_posts_title') }}",
    'Try fetching posts using the CLI:': "{{ _('empty_posts_desc') }}",
    '← Anterior': "{{ _('page_prev') }}",
    'Siguiente →': "{{ _('page_next') }}",
    '⚙️ Gestionar Grupos de Favoritos': "{{ _('modal_group_title') }}",
    'Nombre del grupo...': "{{ _('modal_group_name') }}",
    '(Sin padre)': "{{ _('modal_group_parent') }}",
    '+ Crear': "{{ _('modal_group_create') }}",
    'Cargando...': "{{ _('modal_group_loading') }}",
    'No hay grupos creados aún.': "{{ _('modal_group_empty') }}",
    'Agregar a favoritos': "{{ _('fav_add') }}",
    'Quitar de favoritos': "{{ _('fav_remove') }}",
    'Agregar a grupo:': "{{ _('fav_dropdown') }}",
    '🟠 Post HN': "{{ _('nav_hn') }}",
    '🖊️ Post Personal': "{{ _('nav_personal') }}"
}

for old, new in replacements.items():
    content = content.replace(old, new)


# Add the language toggle specifically
header_actions_start = '<div class="header-actions" style="display: flex; align-items: center; gap: 20px;">'
lang_toggle_html = '''<div class="header-actions" style="display: flex; align-items: center; gap: 20px;">
            <div class="lang-toggle">
                <button onclick="document.cookie='lang=en;path=/'; location.reload();" class="btn" style="border:none;background:none;cursor:pointer;font-size:1.2em;opacity:{% if current_lang == 'en' %}1{% else %}0.5{% endif %};" title="English">🇺🇸</button>
                <button onclick="document.cookie='lang=es;path=/'; location.reload();" class="btn" style="border:none;background:none;cursor:pointer;font-size:1.2em;opacity:{% if current_lang == 'es' %}1{% else %}0.5{% endif %};" title="Español">🇪🇸</button>
            </div>'''

if 'lang-toggle' not in content:
    content = content.replace(header_actions_start, lang_toggle_html)


# Update personal_posts.html
personal_path = 'templates/personal_posts.html'
with open(personal_path, 'r', encoding='utf-8') as f:
    content_p = f.read()

replacements_p = {
    'Mis Posts Personales': "{{ _('personal_title') }}",
    '+ Nuevo Post': "{{ _('personal_new') }}",
    'Gestiona tus propios posts de interés, enlaces y notas.': "{{ _('personal_desc') }}"
}

for old, new in replacements_p.items():
    content_p = content_p.replace(old, new)

if 'lang-toggle' not in content_p:
    content_p = content_p.replace(header_actions_start, lang_toggle_html)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

with open(personal_path, 'w', encoding='utf-8') as f:
    f.write(content_p)

print("Translation replacements applied successfully!")
