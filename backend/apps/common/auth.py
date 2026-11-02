from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


class UsuarioSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    nombre = serializers.CharField()


class SesionSerializer(serializers.Serializer):
    usuario = UsuarioSerializer(allow_null=True)
    csrfToken = serializers.CharField()


class CredencialesSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(trim_whitespace=False, write_only=True, max_length=256)


def datos_sesion(request):
    user = request.user
    return {
        "usuario": {
            "id": user.pk,
            "username": user.username,
            "nombre": user.get_full_name() or user.username,
        }
        if user.is_authenticated and user.is_active and user.is_staff
        else None,
        "csrfToken": get_token(request),
    }


class LimiteAcceso(AnonRateThrottle):
    scope = "login"


@method_decorator(never_cache, name="dispatch")
class SesionView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=SesionSerializer)
    def get(self, request):
        return Response(datos_sesion(request))


@method_decorator(csrf_protect, name="dispatch")
@method_decorator(never_cache, name="dispatch")
class IngresarView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LimiteAcceso]

    @extend_schema(request=CredencialesSerializer, responses={200: SesionSerializer})
    def post(self, request):
        datos = CredencialesSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        user = authenticate(request=request, **datos.validated_data)
        if user is None or not user.is_active or not user.is_staff:
            return Response({"error": {"detail": "Usuario o contraseña incorrectos."}}, status=400)
        login(request, user)
        return Response(datos_sesion(request))


@method_decorator(never_cache, name="dispatch")
class SalirView(APIView):
    @extend_schema(request=None, responses=SesionSerializer)
    def post(self, request):
        logout(request)
        return Response(datos_sesion(request))
