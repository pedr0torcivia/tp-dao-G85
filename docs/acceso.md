# Acceso y cuentas de personal

## Demostración local

Con los contenedores iniciados:

```powershell
docker compose exec backend python manage.py preparar_exposicion
```

Abrir `http://localhost:5173/` e ingresar con **biblioteca / demo**. Es una cuenta real de personal, cuya clave se guarda con el mecanismo de hash de Django. No tiene privilegios de superusuario. El comando solo crea la cuenta si no existe y conserva claves, permisos y datos modificados.

## Administración de cuentas

Crear la cuenta administradora con una clave propia:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Ingresar a `http://localhost:8000/admin/` con esa cuenta. En Usuarios se pueden crear cuentas, cambiar claves y desactivar usuarios. Para utilizar la aplicación, marcar **Activo** y **Es staff**. No hace falta conceder privilegios de superusuario ni permisos individuales sobre modelos para operar desde el frontend.

Cambiar la clave de la cuenta de demostración:

```powershell
docker compose exec backend python manage.py changepassword biblioteca
```

Las cuentas de personal pueden operar sobre toda la red. La sede elegida en la cabecera identifica el contexto de atención. Los socios del catálogo no son cuentas de acceso. La consigna no exige perfiles de permisos separados para logística y biblioteca.

## Sesión y protección

- `GET /api/auth/sesion/` devuelve la identidad actual o `usuario: null` y establece el token CSRF.
- `POST /api/auth/ingresar/` valida `username` y `password`; requiere CSRF incluso para usuarios anónimos. Devuelve la identidad y rota el token.
- `POST /api/auth/salir/` exige sesión y CSRF e invalida la sesión en el servidor.
- Las rutas de negocio de la API exigen personal activo autenticado. Las pantallas internas redirigen al acceso si falta la sesión y recuperan la ruta solicitada después de ingresar.
- La sesión dura hasta ocho horas. La cookie de sesión es HttpOnly y SameSite=Lax. El cierre elimina los datos cargados en la interfaz; la recarga restaura la identidad desde el servidor.
- El acceso limita los intentos anónimos a diez por minuto por dirección IP. Una cuenta desconocida, inactiva, sin permiso de personal o con clave incorrecta recibe el mismo mensaje.
- Salud, información general, contrato OpenAPI y Swagger son públicos; las operaciones expuestas en Swagger siguen exigiendo sesión y CSRF. Ingresar primero desde el frontend utilizando el mismo nombre de host.

El frontend utiliza cookies de sesión y el encabezado `X-CSRFToken` siguiendo la [autenticación por sesión de DRF](https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication) y la [protección CSRF de Django](https://docs.djangoproject.com/en/5.2/howto/csrf/).

## Configuración

`DJANGO_CSRF_TRUSTED_ORIGINS` permite los orígenes del frontend, con esquema y puerto. Por defecto se admiten `http://localhost:5173` y `http://127.0.0.1:5173`. Usar el mismo nombre de host para frontend y API en pruebas de navegador.

Para publicar con HTTPS, configurar `DJANGO_COOKIE_SECURE=true`, orígenes y hosts reales, `DJANGO_DEBUG=false` y una clave secreta propia. Las credenciales de demostración son para la entrega local. Las variables se configuran en `.env`, fuera del repositorio.

## Verificación

`apps/common/tests/test_auth.py` comprueba sesiones reales con CSRF activo, acceso anónimo, claves incorrectas, permisos revocados, cuenta inactiva, rechazo de orígenes ajenos, cierre e intentos limitados. Las pruebas de dominio autentican un usuario de personal para concentrarse en sus reglas. `frontend/e2e/acceso.spec.ts` verifica acceso, recarga, cierre y vencimiento en Chrome. Los cinco circuitos de biblioteca también ingresan por el formulario real.
