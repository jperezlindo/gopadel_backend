# users/views/user_view.py
# Este archivo actúa como un puente limpio entre urls.py y los controllers.
# La idea es mantener una importación estable (users.views.user_view) aunque
# internamente los controllers cambien de ubicación o nombre en el futuro.
# De esta forma, en urls.py se importa desde "views" y no se acopla al path real
# de controllers.

from users.controllers.user_controller import (
    UserListCreateView,
    UserDetailView,
    UserChangePasswordView,
)

# Expongo explícitamente lo que quiero publicar desde la capa "views".
# Con __all__ dejo claro qué se puede importar desde afuera.
__all__ = ["UserListCreateView", "UserDetailView", "UserChangePasswordView"]
