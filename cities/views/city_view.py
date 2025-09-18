# cities/views/city_view.py
# Este archivo es un puente estable para que urls.py importe desde "views"
# y no se acople al path real de los controllers.

from cities.controllers.city_controller import (
    CityListCreateView,
    CityDetailView,
)

__all__ = ["CityListCreateView", "CityDetailView"]
