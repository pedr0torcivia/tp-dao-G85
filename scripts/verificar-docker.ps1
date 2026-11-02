$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

function Verificar-Salida {
    if ($LASTEXITCODE -ne 0) { throw "Falló el comando anterior ($LASTEXITCODE)." }
}

docker compose up -d --build --wait
Verificar-Salida
docker compose exec -T backend python manage.py preparar_exposicion
Verificar-Salida
docker compose exec -T backend python manage.py makemigrations --check --dry-run
Verificar-Salida
docker compose exec -T backend python manage.py test
Verificar-Salida

$consulta = 'from apps.catalogo.models import Ejemplar; print(Ejemplar.objects.count())'
$cantidadAntes = docker compose exec -T backend python manage.py shell -c $consulta
Verificar-Salida
docker compose restart
Verificar-Salida
docker compose up -d --wait
Verificar-Salida
$cantidadDespues = docker compose exec -T backend python manage.py shell -c $consulta
Verificar-Salida
if (($cantidadAntes -join "`n") -ne ($cantidadDespues -join "`n")) {
    throw 'La cantidad de ejemplares cambió después del reinicio.'
}
$salud = Invoke-RestMethod 'http://localhost:5173/api/health/'
if ($salud.status -ne 'ok') { throw 'El frontend no puede acceder al backend.' }
Write-Output 'Verificación completa. Aplicación: http://localhost:5173/'
