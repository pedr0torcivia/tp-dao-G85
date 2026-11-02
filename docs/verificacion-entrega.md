# Verificación de la entrega

Revisión del 1 de noviembre de 2026. Rama `integration/cierre-tp`, basada en `main` (`da48d34`).

## Resultado ejecutado

| Comprobación | Resultado |
|---|---|
| Backend dentro de Docker con PostgreSQL 17.11 | 193 pruebas aprobadas; incluye concurrencia, sin omisiones |
| Autenticación y protección de la API | 14 pruebas con sesiones reales y comprobación CSRF activa |
| Contrato y lógica del frontend | 18 pruebas aprobadas |
| Compilación TypeScript y Vite | Aprobada |
| Navegador Chrome contra frontend Nginx, API y PostgreSQL en Docker | 8 recorridos aprobados |
| Migraciones | Aplicadas desde una base vacía; sin cambios pendientes |
| Datos reproducibles | Carga idempotente; cinco reportes contrastados con cantidades conocidas |
| Ruff | Sin errores |
| OpenAPI | Validación sin errores ni advertencias |
| Construcción y arranque con Compose | Imágenes construidas; los tres servicios saludables |
| Persistencia tras reiniciar contenedores | Cantidad de ejemplares conservada y libro creado desde el navegador recuperado con su título y autor |
| Sesión tras reiniciar backend | Identidad autenticada conservada; lectura del mismo libro y cierre de sesión confirmados |
| Acceso a través del frontend | Inicio, salud, Swagger y esquema OpenAPI responden HTTP 200 |

Los recorridos de navegador cubren acceso protegido, rechazo de clave incorrecta, restauración de sesión, cierre, vencimiento; alta de libro con autor y persistencia tras recarga; préstamo local y devolución; interbibliotecario con remito de ida y retorno; reserva cumplida; cinco reportes consultados al servidor con exportación CSV.

La verificación final usa Docker Desktop 28.5.1: frontend compilado servido por Nginx, backend con Gunicorn y PostgreSQL 17.11, sin mocks. Se aplicaron las migraciones desde una base vacía y se cargaron los datos de demostración. Repetir la carga conservó los cambios existentes. Las pruebas también se ejecutaron con PostgreSQL local y SQLite durante el desarrollo, omitiendo en SQLite las dos comprobaciones que requieren bloqueos de PostgreSQL.

## Alcance de verificación

El build, el arranque completo de Compose y la persistencia después de reiniciar los contenedores se comprobaron localmente. Los servicios quedan en ejecución para revisar la aplicación en `http://localhost:5173/`. No se borraron volúmenes del usuario.

El script `scripts/verificar-docker.ps1` construye, espera servicios saludables, carga ejemplos, ejecuta pruebas con PostgreSQL y compara la cantidad de ejemplares después de reiniciar. El workflow `.github/workflows/verificacion.yml` prepara esas comprobaciones en un entorno limpio, además de las pruebas de navegador. El workflow queda pendiente de ejecutarse al publicar la rama.

La matriz completa está en `matriz-cumplimiento.md`. La presentación del grupo y el DER A4 están en `docs/`. `scripts/empaquetar-entrega.ps1` prepara `output/Entrega-grupo-85.zip` con el código y la documentación; su integridad y los archivos requeridos se comprobaron, excluyendo `.env`, dependencias instaladas, datos locales y metadatos de Git.

## Repetir las pruebas

Con Docker Desktop funcionando, desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verificar-docker.ps1
```

Para las pruebas de navegador contra esos contenedores:

```powershell
cd frontend
npm ci
$env:E2E_BASE_URL = "http://localhost:5173"
$env:E2E_API_URL = "http://localhost:8000/api"
npm run test:e2e
```

Se utiliza Chrome instalado. En un entorno sin Chrome se puede instalar Chromium con `npx playwright install chromium` y configurar `E2E_BROWSER_CHANNEL=chromium`. Las pruebas crean registros identificados con valores únicos; ejecutarlas en una base de demostración, ya que conservan sus registros para inspección.

Para desarrollo local, iniciar Django en el puerto 8000 con PostgreSQL y ejecutar en frontend:

```powershell
npm ci
npm test
npm run build
npm run test:e2e
```

Playwright inicia y detiene Vite automáticamente si no se indicó E2E_BASE_URL. El modo mock se habilita únicamente de forma explícita y conserva sus propias pruebas.

## Cierre del grupo

Quedan la revisión entre integrantes, la publicación y fusión de la rama a `main`, la ejecución del workflow remoto y el ensayo de la defensa. Confirmar la fecha oficial y el mecanismo de entrega con la cátedra. Las explicaciones de patrones y el guion están en `patrones.md` y `guion-demostracion.md`.


## Escenario final para exposición

Se respaldó la base anterior antes de reemplazar los datos de biblioteca. Las cuentas se conservaron. El escenario final contiene 30 títulos con portadas locales, 90 ejemplares, 3 sedes, 6 socios, 7 solicitudes, 3 préstamos, una reserva y 3 remitos. No se conservan registros generados por las pruebas de navegador. Ms. Marvel fue retirado del catálogo.

Se verificó el ABMC de un ejemplar desde Chrome y su aparición como ALTA, MODIFICACION y BAJA en RP05, además de su efecto en RP04. Los cinco reportes requieren y aplican rango Desde/Hasta. Se exportaron y revisaron documentos PDF desde la aplicación. La guía PDF contiene siete páginas con pasos, cálculos, criterios y resultados esperados. Los datos y documentos son de demostración; las obras y portadas corresponden a títulos reales.
