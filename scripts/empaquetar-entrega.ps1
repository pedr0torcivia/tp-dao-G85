$ErrorActionPreference = 'Stop'
$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $raiz

$archivos = @(git -c core.quotepath=false ls-files --cached --others --exclude-standard)
if ($LASTEXITCODE -ne 0) { throw 'No se pudo obtener la lista de archivos del proyecto.' }
$archivos = @($archivos | Sort-Object -Unique | Where-Object {
    $_ -notmatch '^(graphify-out|tmp|output|node_modules)/' -and
    ($_ -notmatch '(^|/)\.env($|\.)' -or $_ -match '(^|/)\.env\.example$')
})

$salida = Join-Path $raiz 'output'
New-Item -ItemType Directory -Path $salida -Force | Out-Null
$destino = Join-Path $salida 'Entrega-grupo-85.zip'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$flujo = [System.IO.File]::Open($destino, [System.IO.FileMode]::Create)
$zip = [System.IO.Compression.ZipArchive]::new($flujo, [System.IO.Compression.ZipArchiveMode]::Create)
$cantidad = 0
try {
    foreach ($relativo in $archivos) {
        $absoluto = [System.IO.Path]::GetFullPath((Join-Path $raiz $relativo))
        if (-not $absoluto.StartsWith($raiz + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Archivo fuera del proyecto: $relativo"
        }
        if (-not (Test-Path -LiteralPath $absoluto -PathType Leaf)) { continue }
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $zip, $absoluto, ('TP-DAO-Grupo-85/' + $relativo.Replace('\', '/')),
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
        $cantidad += 1
    }
} finally {
    $zip.Dispose()
    $flujo.Dispose()
}
Write-Output "Entrega preparada: $destino ($cantidad archivos). No incluye claves locales, datos de pruebas ni dependencias instaladas."
