# Catalogar desde Excel

Muchas bibliotecas llegan al proyecto Ofelia con un fondo ya escrito en una
**hoja de cálculo Excel** (un identificador propio, un título, un autor, a
veces un ISBN). La **catalogación Excel** ofrece dos herramientas para
aprovechar ese archivo:

1. **Verificar un archivo** — BibliOfelia anota su hoja de cálculo con lo
   que las bases de datos en línea conocen de cada libro, sin modificar nada
   en el catálogo. Ideal **antes** de una migración, para medir la calidad
   del archivo y corregirlo a mano.
2. **Importar en el catálogo** — BibliOfelia convierte una lista de ISBN en
   fichas y ejemplares, de una sola vez.

!!! info "Solo para bibliotecarios"
    La catalogación Excel se encuentra en el menú **Avanzado**, disponible
    para bibliotecarios y administradores.

## Abrir la catalogación Excel

Desde el menú [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" },
sección **Inventario**, haga clic en
[**Catalogación Excel**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" }.

La página muestra dos recuadros uno al lado del otro: **Verificar un
archivo** (a la izquierda) e **Importar en BibliOfelia** (a la derecha).

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

Su archivo `.xlsx` debe contener al menos una columna **`ISBN`**. Se
reconocen dos columnas adicionales, si las añade:

| Columna | Contenido |
|---|---|
| `ISBN` | **obligatorio** |
| `LOCATION` | opcional: el código de ubicación (de lo contrario el ejemplar se crea sin ubicación) |
| `CATEGORY` | opcional: el nombre de una categoría existente |

En el recuadro
[**Importar en BibliOfelia**](/bibliofelia/es/catalog/excel-catalog/){ target="_blank" },
elija su archivo y haga clic en **Importar en el catálogo**.

Cada ISBN se convierte en una ficha y un ejemplar. Si un ISBN **ya existe**
en el catálogo, BibliOfelia no recrea la ficha: simplemente añade un
ejemplar a la ficha existente.

La importación crea un **lote de catalogación**: una vez terminado el
trabajo, haga clic en **Ver el lote importado** para abrirlo, o vuelva a
encontrarlo en
[**Catalogación por escaneo**](/bibliofelia/es/catalog/scan/){ target="_blank" },
exactamente como un lote escaneado con la cámara.

!!! tip "Completar títulos y autores"
    La importación registra los ISBN, pero todavía no los títulos y autores.
    Lance después un **enriquecimiento** sobre el lote para buscar los
    metadatos en línea.

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
