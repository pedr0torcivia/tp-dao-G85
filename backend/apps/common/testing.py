"""Identidad de personal para pruebas de dominio a través de la API."""

from django.contrib.auth import get_user_model


def autenticar_personal(client):
    user = get_user_model().objects.create_user(username="personal-prueba", is_staff=True)
    client.force_authenticate(user=user)
