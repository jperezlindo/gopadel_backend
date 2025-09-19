# categories/views/category_view.py
# En esta capa yo solo "expongo" las vistas que vienen de controllers.
# Lo hago así para que las urls importen siempre desde "views" y no se acoplen
# a la ubicación real de los controllers. Además, NO importo ningún urls.py acá
# para evitar ciclos de importación (recursión en el URLConf).

from categories.controllers.category_controller import (
    CategoryListCreateView,
    CategoryDetailView,
)

# Expongo explícitamente qué vistas quiero publicar desde este módulo.
__all__ = ["CategoryListCreateView", "CategoryDetailView"]
