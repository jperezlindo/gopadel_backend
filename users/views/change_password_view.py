# users/views/change_password_view.py
from typing import Any, Mapping, Optional, cast
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from users.schemas.change_password_serializer import ChangePasswordSerializer
from users.services.user_service import UserService
from users.schemas.user_serializer import UserSerializer  # para devolver el user actualizado

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = UserService()
        
    def post(self, request, user_id: int):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ✅ Tipado explícito para Pylance
        data = cast(Mapping[str, Any], serializer.validated_data)
        old_password = cast(Optional[str], data.get("old_password"))
        new_password = cast(str, data["new_password"])

        user = self.service.change_password(
            actor=request.user,
            target_user_id=user_id,
            old_password=old_password,
            new_password=new_password,
        )
        return Response(
            {"message": "Password updated successfully.", "user": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )
