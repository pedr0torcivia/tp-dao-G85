# EntreLibros — Manual de identidad visual

Versión 1.0 · 9 de octubre de 2026 · Grupo 85

La identidad de EntreLibros representa una red de bibliotecas con un libro abierto y una sonrisa entre sus páginas. La página izquierda y «Entre» son verde bosque; la página derecha y «Libros» son naranja terracota. El nombre se escribe **EntreLibros**, unido y con E y L mayúsculas.

## 1. Archivos oficiales

Esta carpeta contiene únicamente estos tres archivos:

| Archivo | Contenido | Uso |
|---|---|---|
| [logo.svg](logo.svg) | Isotipo y nombre en una composición horizontal | Cabecera del sitio, acceso, documentos y comunicaciones |
| [isotipo.svg](isotipo.svg) | Libro con sonrisa | Favicon, acceso móvil y espacios reducidos |
| `manual-identidad.md` | Este manual | Referencia para diseño e implementación |

Los SVG son vectores reales: las letras están convertidas en trazados y no contienen imágenes incrustadas ni requieren fuentes instaladas. El fondo es transparente. La sonrisa y el espacio central también son transparentes.

### Logo completo

![Logo EntreLibros](logo.svg)

### Isotipo

<img src="isotipo.svg" alt="Isotipo EntreLibros: libro abierto con sonrisa" width="120">

## 2. Construcción y proporciones

El isotipo tiene dos páginas de igual ancho, separadas por una ranura vertical. La sonrisa tiene extremos redondeados y elevados respecto del centro: **el centro de la curva queda más abajo que sus extremos**. No invertirla.

El logo combina el isotipo a la izquierda y el nombre a la derecha. La palabra «Entre» utiliza bosque y «Libros» terracota. No insertar un espacio entre ambas partes. Mantener la composición, las curvas, el espaciado y las proporciones de los archivos oficiales.

### Área de protección

Definir **H** como la altura visible del libro, sin contar el margen transparente del archivo. Dejar al menos **H/4** libres alrededor de la marca, medidos desde sus formas visibles hasta cualquier texto, imagen, borde o control. El margen del SVG no reemplaza esta separación.

### Tamaños en la página

| Aplicación | Medida |
|---|---|
| Cabecera de escritorio | Logo de 200–240 px de ancho |
| Cabecera móvil con nombre | Logo de 160–190 px de ancho |
| Mínimo del logo completo | 160 px de ancho |
| Isotipo en navegación | 32–40 px de ancho |
| Mínimo del isotipo como elemento de interfaz | 24 px de ancho |
| Favicon | Usar `isotipo.svg`; comprobar reconocimiento a 16 y 32 px |

Escalar siempre con la relación de aspecto original. En CSS, definir el ancho y usar `height: auto`. Los mínimos de interfaz no garantizan el mismo detalle a 16 px; el favicon debe revisarse en el navegador de destino.

## 3. Fondos y usos permitidos

- Usar el logo a color sobre **papel**, **blanco** o **salvia**.
- Sobre una fotografía, colocarlo en una superficie uniforme de papel o blanco que respete el área de protección.
- Sobre un fondo oscuro, colocar la versión oficial en una superficie clara. Este paquete no incluye una variante invertida aprobada.
- Usar el isotipo cuando la marca ya está identificada por contexto o cuando no cabe el nombre completo.
- Usar el logo completo para presentar la marca por primera vez.

No estirar, comprimir, rotar, añadir sombras, degradados, contornos ni texturas. No cambiar los colores, reconstruir el nombre con una fuente parecida, separar los elementos, invertir la sonrisa ni sustituirla por otro gesto. No usar como botón de una operación ajena a la navegación de la marca.

## 4. Colores oficiales

| Nombre | HEX | RGB | Uso en la página |
|---|---|---|---|
| Verde bosque | `#234D3C` | 35, 77, 60 | Página izquierda, «Entre», acción principal, títulos |
| Naranja terracota | `#B84F36` | 184, 79, 54 | Página derecha, «Libros», detalles y acentos de marca |
| Papel | `#FAF7EF` | 250, 247, 239 | Fondo general de la página |
| Tinta | `#242B27` | 36, 43, 39 | Texto principal, tablas y formularios |
| Salvia | `#E6EDE5` | 230, 237, 229 | Superficies suaves y bloques secundarios |
| Blanco | `#FFFFFF` | 255, 255, 255 | Superficies de trabajo y texto sobre bosque |
| Texto secundario | `#626A62` | 98, 106, 98 | Ayudas, metadatos y leyendas |
| Borde | `#D9DFD6` | 217, 223, 214 | Separadores decorativos y límites suaves |

Papel y blanco predominan en las superficies. El verde identifica acciones y jerarquía. La terracota debe aparecer con moderación; evitar grandes superficies que compitan con la lectura.

### Estados funcionales

| Estado | Texto | Fondo | Ejemplo |
|---|---|---|---|
| Éxito | `#285C42` | `#E6EDE5` | Disponible |
| Advertencia | `#805516` | `#FFF1D6` | Próximo a vencer |
| Error | `#A1362D` | `#FAE8E5` | Operación rechazada |
| Información | `#285A70` | `#E6F0F5` | En tránsito |

La terracota es un color de marca; los errores utilizan su propio color y una explicación. Un estado siempre debe incluir una etiqueta, y un error debe indicar su causa y el siguiente paso.

### Contraste y foco

Las siguientes combinaciones de texto tienen relaciones de contraste calculadas con luminancia sRGB:

| Texto / fondo | Contraste |
|---|---|
| Tinta / papel | 13,53:1 |
| Texto secundario / papel | 5,22:1 |
| Blanco / bosque | 9,55:1 |
| Terracota / papel | 4,66:1 |
| Terracota / salvia | 4,18:1 |

Usar **4,5:1** como mínimo para texto normal. Terracota sobre salvia se reserva al logo o a elementos gráficos, no a etiquetas pequeñas. No usar papel o salvia como texto sobre blanco. El borde suave no basta por sí solo para identificar campos: usar un borde más oscuro cuando sea necesario para distinguir el control.

Dar foco visible a enlaces, botones y campos, por ejemplo un anillo bosque de 2 px separado por un anillo papel de 2 px. Comprobarlo contra el fondo real y no quitar el contorno sin reemplazo visible.

## 5. Tipografías para la página

### Lora

Tipografía editorial para títulos y piezas de marca. El nombre del logo se construye a partir de **Lora 600**, convertido a trazados: usar el archivo oficial para mostrarlo.

- Títulos principales de página: Lora 600, 28–36 px.
- Títulos de sección: Lora 500–600, 22–26 px.
- Piezas de presentación: Lora 500–600; usar tamaños mayores solo cuando el contexto lo justifique.
- Interlineado de títulos: 1,2–1,3.
- Alternativa de carga: `Georgia, serif`.

### DM Sans

Tipografía de interfaz para navegación, formularios, botones, ayudas, listas y tablas.

- Texto general: DM Sans 400, 16 px, interlineado 1,5.
- Navegación y botones: DM Sans 500–600, 14–16 px.
- Etiquetas y tablas: DM Sans 400–500, 14–16 px.
- Notas secundarias: DM Sans 400, 12–14 px; no reducir texto esencial a este tamaño.
- Alternativa de carga: `system-ui, sans-serif`.
- Usar números tabulares en fechas, cantidades y columnas comparables.

Fuentes oficiales: [Lora](https://github.com/google/fonts/tree/main/ofl/lora) y [DM Sans](https://github.com/google/fonts/tree/main/ofl/dmsans). Ambas se distribuyen con SIL Open Font License en sus respectivos directorios. Al incorporarlas al frontend, conservar sus licencias y configurar `font-display: swap`. Este paquete no incorpora archivos de fuentes.

## 6. Aplicación al frontend

Usar espaciado en múltiplos de 4 px: 8, 12, 16, 24 y 32 px. Radios orientativos: 6 px para controles compactos, 12 px para bloques y 20 px para piezas de presentación. Las tablas y pantallas operativas deben priorizar legibilidad, alineación y acciones claras.

La cabecera usa el logo completo sobre papel o blanco. En pantallas estrechas puede usar el isotipo, manteniendo el nombre de la aplicación accesible. No repetir la marca como adorno dentro de cada tarjeta.

Referencia de variables CSS para la futura implementación:

```css
:root {
  --color-brand: #234D3C;
  --color-brand-accent: #B84F36;
  --color-background: #FAF7EF;
  --color-surface: #FFFFFF;
  --color-surface-soft: #E6EDE5;
  --color-text: #242B27;
  --color-text-muted: #626A62;
  --color-border: #D9DFD6;
  --font-heading: 'Lora', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
}
```

Estos nombres son una referencia para la página, no una implementación de componentes. Al integrar, copiar los SVG a la carpeta pública de assets conservando los archivos originales como fuente de marca.

### Accesibilidad del logo

- Si el logo identifica la aplicación, usar `alt="EntreLibros"`.
- Si está dentro de un enlace al inicio, el enlace debe tener un nombre accesible como «EntreLibros, inicio».
- Si el símbolo acompaña al nombre ya visible y es redundante, usar `alt=""`.
- Preferir `<img>` para incorporar los archivos SVG. Los documentos SVG tienen títulos internos; no duplicar sus identificadores al insertarlos repetidamente en línea.
- Probar los textos con zoom, foco por teclado y ancho móvil; no comunicar estados únicamente por color.

## 7. Voz de marca

Tono cercano, claro y confiable, en español rioplatense. Ejemplos: «Buscá un libro», «Ver ejemplares», «Registrar devolución». En una operación, explicar el resultado sin adornos: «Este ejemplar ya no está disponible. Elegí otro para continuar».

El lema opcional **«Historias que nos acercan»** se utiliza en comunicación y presentación. No forma parte del logo y no debe agregarse dentro del SVG ni repetirse en pantallas de trabajo.
