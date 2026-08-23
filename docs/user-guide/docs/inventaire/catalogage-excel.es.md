# Catalogar desde Excel

Muchas bibliotecas llegan al proyecto Ofelia con un fondo ya escrito en una
**hoja de cálculo Excel** (un identificador propio, un título, un autor, a
veces un ISBN). La **catalogación Excel** ofrece cuatro herramientas para
aprovechar ese archivo:

1. **Verificar un archivo** — BibliOfelia anota su hoja de cálculo con lo
   que las bases de datos en línea conocen de cada libro, sin modificar nada
   en el catálogo. Ideal **antes** de una migración, para medir la calidad
   del archivo y corregirlo a mano.
2. **Importar en el catálogo** — BibliOfelia convierte una lista de ISBN en
   fichas y ejemplares, de una sola vez.
3. **Exportar el catálogo** — BibliOfelia le devuelve todo su fondo en una
   hoja de cálculo, una línea por ejemplar.
4. **Actualizar ejemplares** — usted devuelve esa hoja corregida y
   BibliOfelia aplica sus correcciones a los libros ya catalogados, sin
   crear nunca ninguno nuevo.

!!! info "Solo para bibliotecarios"
    La catalogación Excel se encuentra en el menú **Avanzado**, disponible
    para bibliotecarios y administradores.

## Abrir la catalogación Excel

Desde el menú [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" },
sección **Inventario**, haga clic en
[**Catalogación Excel**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" }.

La página muestra cuatro recuadros: **Verificar un archivo**, **Importar en
BibliOfelia**, **Exportar el catálogo** y **Actualizar ejemplares**.

## Verificar un archivo

Úselo para **revisar** una hoja de cálculo sin tocar el catálogo.

Su archivo debe ser un **`.xlsx`** cuya primera fila contenga al menos estas
cuatro columnas (mayúsculas y acentos tolerados):

| Columna | Contenido |
|---|---|
| `ID` | su identificador propio (se conserva tal cual) |
| `TITLE` | el título del libro |
| `AUTHOR` | el o los autores |
| `ISBN` | el ISBN completo (10 o 13 cifras) |

!!! warning "ISBN incompleto o erróneo"
    La búsqueda por ISBN solo acepta un ISBN **válido** (10 o 13 cifras). Un
    ISBN incompleto o falso se marca `ISBN_INVALID` y **no** permite
    encontrar el libro por ISBN — es justamente el caso catastrófico.
    Entonces son el `TITLE` y el `AUTHOR` los que salvan la situación,
    mediante la búsqueda por título + autor: cuide esas dos columnas.

En el recuadro
[**Verificar un archivo**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" },
elija su archivo y haga clic en **Iniciar la verificación**.

BibliOfelia consulta **OpenLibrary, Google Books, la BNF y la BNE**, primero
por ISBN y luego por título + autor. El procesamiento se realiza en segundo
plano: cuente unos **10 minutos por cada 300 filas**.

Cuando el trabajo termina, haga clic en **Descargar el archivo anotado**.
Recupera su hoja de cálculo original, enriquecida con columnas adicionales:

- `TITLE_FOUND_BY_ISBN`, `AUTHOR_FOUND_BY_ISBN`, `SOURCE_BY_ISBN` — lo que el
  ISBN permitió encontrar;
- `ISBN_FOUND_BY_TA`, `TITLE_FOUND_BY_TA`, `AUTHOR_FOUND_BY_TA` — lo que la
  búsqueda por título + autor encontró;
- `CONFIDENCE` — una puntuación de 0 a 100 sobre la fiabilidad de la
  coincidencia.

!!! tip "Leer los colores"
    Las celdas con una puntuación de confianza baja aparecen en
    **naranja**: son las filas que hay que revisar a mano. Un
    `ISBN_FOUND_BY_TA` distinto de su ISBN a menudo indica un **error de
    escritura** en el archivo original.

La verificación **no escribe nada** en el catálogo: puede lanzarla tantas
veces como necesite.

## Importar en el catálogo

Úselo para **crear** realmente las fichas y los ejemplares a partir de una
lista de ISBN.

Su archivo `.xlsx` debe contener al menos una columna **`ISBN`**. Todas las
demás columnas son **opcionales**: añada solo las que tenga, en cualquier
orden.

| Columna | Contenido |
|---|---|
| `ISBN` | **obligatorio** |
| `LOCATION` | el código de ubicación (de lo contrario el ejemplar se crea sin ubicación) |
| `CATEGORY` | el nombre de una categoría existente |
| `TITLE` | el título de la ficha |
| `AUTHOR` | el o los autores, separados por **puntos y comas** |
| `TYPE` | el tipo de documento (Libro, Cómic / manga, Revista, Periódico, CD de audio, Otro) |
| `EDITOR` | la editorial |
| `YEAR` | el año de publicación |
| `LANGUAGE` | el código de idioma (fr, en, es…) |
| `TAGS` | palabras clave separadas por **comas** |
| `EXTERNAL_CODE` | el código de otra biblioteca ya puesto en el libro |
| `PROVENANCE` | el código o el nombre de una procedencia existente |
| `CATEGORY_ABBR` | la abreviatura de la categoría (signatura) |
| `CONDITION` | el estado del ejemplar (Nuevo, Bueno, Desgastado, Dañado) |

En el recuadro
[**Importar en BibliOfelia**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" },
elija su archivo y haga clic en **Importar en el catálogo**.

Cada ISBN se convierte en una ficha y un ejemplar. Si un ISBN **ya existe**
en el catálogo, BibliOfelia no recrea la ficha: simplemente añade un
ejemplar a la ficha existente.

!!! info "Una columna rellenada reemplaza la información de la ficha"
    Si añade una de las columnas anteriores (título, autor, editorial…) y la
    **celda está rellenada**, su valor **sobrescribe** el campo
    correspondiente de la ficha — **incluso si la ficha ya existe**. Una
    **celda vacía no cambia nada**: se conserva la información ya presente.
    Para el autor y las etiquetas, la lista del archivo **reemplaza** la
    existente (no se añade a ella). Un valor no reconocido para `TYPE` o
    `CONDITION`, o un año que no es un número, se **ignora** y se señala en
    las advertencias del lote.

La importación crea un **lote de catalogación**: una vez terminado el
trabajo, haga clic en **Ver el lote importado** para abrirlo, o vuelva a
encontrarlo en
[**Catalogación por escaneo**](/bibliofelia/es/catalog/scan/){ target="_blank" },
exactamente como un lote escaneado con la cámara.

!!! tip "Completar lo que falta en línea"
    ¿Solo tiene los ISBN, sin título ni autor? Lance después un
    **enriquecimiento** sobre el lote para buscar los metadatos en línea
    (OpenLibrary, Google Books, BnF…). Las columnas del archivo siguen
    teniendo prioridad: el enriquecimiento solo completa lo que aún está
    vacío.

## Exportar el catálogo

Úselo para **recuperar todo su fondo** en una hoja de cálculo: para releerlo,
guardar una copia sin conexión o preparar una corrección masiva.

En el recuadro **Exportar el catálogo**, haga clic en **Exportar el
catálogo**. El archivo `catalogue-AAAA-MM-DD.xlsx` se descarga de inmediato:
no hay nada que esperar.

La hoja contiene **una línea por ejemplar**, no por título. Un libro que
usted tiene en tres ejemplares ocupa, pues, tres líneas: es normal, porque la
ubicación, el estado, la procedencia y el código externo pertenecen al
**ejemplar** y no a la ficha.

| Columna | Contenido |
|---|---|
| `OFELIA_CODE` | el código Ofelia del ejemplar (el código de barras de la etiqueta) |
| `INTERNAL_ID` | el código legible impreso junto al código de barras (`OFL-…`) |
| `EXTERNAL_CODE` | el código de otra biblioteca ya puesto en el libro |
| `ISBN`, `TITLE`, `AUTHOR`, `EDITOR`, `YEAR`, `LANGUAGE` | los datos de la ficha |
| `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `TAGS` | la clasificación |
| `CONDITION`, `PROVENANCE`, `LOCATION` | los datos del ejemplar |

!!! tip "Es el archivo de la actualización"
    Las columnas de la exportación son **exactamente** las que BibliOfelia
    sabe releer. Corrija lo que quiera en Excel y devuelva el mismo archivo
    por **Actualizar ejemplares**: no hay nada más que preparar.

## Actualizar ejemplares

Úselo para **corregir masivamente** libros **ya** presentes en el catálogo:
cambiar ubicaciones tras mover un estante, pasar una serie a «Desgastado»,
asignar códigos externos, arreglar títulos mal escritos.

!!! success "No se crea ningún libro"
    Esta herramienta **nunca** crea una ficha ni un ejemplar. Si una línea
    señala un ejemplar que no existe, se **avisa** y se deja de lado: nunca
    se convierte en un libro nuevo. Puede, pues, devolver una exportación sin
    riesgo de duplicar su biblioteca.

Cada línea debe decir **de qué ejemplar habla**. El archivo debe contener,
por tanto, al menos una de estas dos columnas:

| Columna | Contenido |
|---|---|
| `OFELIA_CODE` | el código Ofelia del ejemplar: el código de barras `290…` **o** el código legible `OFL-…` |
| `EXTERNAL_CODE` | el código de otra biblioteca puesto en el libro |

!!! info "Si las dos columnas están rellenadas"
    Es el **código Ofelia** el que designa el ejemplar, y el código externo
    de la línea **se le aplica**. Así se asignan códigos externos a muchos
    libros de una vez: una columna `OFELIA_CODE` para decir de qué libro se
    trata y una columna `EXTERNAL_CODE` con el código que hay que poner.

Se aceptan todas las demás columnas de la importación, y son **opcionales**:
`TITLE`, `AUTHOR`, `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `EDITOR`, `YEAR`,
`LANGUAGE`, `TAGS`, `CONDITION`, `PROVENANCE`, `LOCATION` e `ISBN`.

!!! warning "Una celda vacía no borra nada"
    Una celda **rellenada** sustituye el valor existente; una celda **vacía**
    deja el valor tal cual. Esta herramienta **no** sirve, pues, para vaciar
    un campo: para eso, abra la ficha del libro. Eso es lo que le permite
    devolver una exportación entera tras haber corregido solo dos columnas.

Elija su archivo, haga clic en **Actualizar los ejemplares** y siga el
trabajo como una importación. La página de detalle muestra:

- **Ejemplares modificados** — las líneas que cambiaron algo realmente;
- **Líneas sin cambio** — el ejemplar se encontró, pero el archivo ya decía
  lo mismo que el catálogo;
- **Errores** — las líneas no aplicadas, con un cartel rojo y el detalle más
  abajo.

| Advertencia | Qué significa |
|---|---|
| `OFELIA_CODE_UNKNOWN` | ningún ejemplar lleva este código Ofelia — línea ignorada |
| `EXTERNAL_CODE_UNKNOWN` | ningún ejemplar lleva este código externo — línea ignorada |
| `NO_KEY` | la línea no dice de qué ejemplar habla |
| `EXTERNAL_CODE_DUPLICATE` | este código externo ya está en otro libro — no aplicado, el resto de la línea sí |
| `ISBN_CONFLICT` | este ISBN ya pertenece a otra ficha — no aplicado, el resto sí |
| `LOCATION_UNKNOWN`, `CATEGORY_UNKNOWN`, `PROVENANCE_UNKNOWN` | el valor no existe en sus listas — ignorado, el resto se aplica |

!!! tip "Una ficha, varios ejemplares"
    El título, el autor o la editorial pertenecen a la **ficha**: corregirlos
    en la línea de un ejemplar los corrige para **todos** los ejemplares de
    ese libro. La ubicación, el estado, la procedencia y el código externo,
    en cambio, solo afectan al ejemplar de esa línea.

## Seguir sus trabajos

En la parte inferior de la página
[**Catalogación Excel**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" },
la sección **Trabajos recientes** enumera sus últimas verificaciones e
importaciones. Haga clic en **Detalles** para seguir el avance, descargar un
archivo anotado o consultar las advertencias fila por fila.

## Bueno saber

!!! warning "Formato y límites"
    - Solo se aceptan archivos **`.xlsx`** (ni `.xls`, ni `.csv`, ni
      `.ods`).
    - Tamaño máximo: **5 MB**, **10 000 filas**.
    - Para una mejor cobertura de los ISBN, el administrador puede
      configurar una **clave de Google Books**; sin ella, una cuota puede
      dejar algunas filas incompletas (columna `SOURCE_BY_ISBN` =
      `RATE_LIMITED`). Vuelva a lanzarlo al día siguiente: la cuota se
      reinicia cada día.

## Véase también

- [Catalogar escaneando](catalogage-scan.md) — la misma importación, pero
  con la cámara libro por libro
- [Añadir un libro](../catalogue/ajouter-livre.md) — crear una sola ficha a
  mano
