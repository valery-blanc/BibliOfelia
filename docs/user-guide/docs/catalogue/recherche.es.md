# Búsqueda

BibliOfelia ofrece dos herramientas de búsqueda complementarias: la
**búsqueda global** desde cualquier página, y el **filtro del
catálogo** cuando ya está en la lista de libros.

## La búsqueda global

En la parte superior de cada página, un campo de búsqueda acepta:

- **Un título o una palabra del título** — "petit prince", "germinal"
- **Un nombre de autor** — "hugo", "saint-exupéry"
- **Un ISBN-13** — 9782070612758 (código del editor, al dorso del
  libro)
- **Un código Ofelia de ejemplar** — 2900000000017 (código de barras
  de la etiqueta BibliOfelia)
- **Un código Ofelia externo** — BCF13298781X (código puesto por otra
  biblioteca o por un donante, si lo ha registrado en el ejemplar)
- **Un nombre de miembro** — "rakoto", "dubois"
- **Un número de tarjeta** — 2910000000444 (código de barras de la
  tarjeta)

BibliOfelia detecta automáticamente de qué se trata (libro, miembro,
ejemplar) y le lleva directamente a la página correcta.

!!! tip "Escriba y pulse Enter"
    No es necesario hacer clic en un botón: escriba y pulse Enter,
    BibliOfelia se encarga del resto.

## El filtro del catálogo

Desde la página [**Catálogo**](/bibliofelia/es/catalog/){ target="_blank" },
la lista de registros puede filtrarse por:

- **Texto libre** (título, autor, editor)
- **Categoría** (Adultos, Juvenil, Documental…)
- **Idioma**
- **Ubicación**

![Lista del catálogo con filtros](../assets/screenshots/es/catalogue/record-list.png)

Los filtros se combinan: por ejemplo "Adultos" + "francés" +
"Gallimard" para ver solo las novelas Gallimard en francés para
adultos.

## Buscar los ejemplares en lugar de los registros

Por defecto el catálogo muestra **una línea por libro** (por registro): si
tiene tres ejemplares de *El Principito*, verá una sola línea con un "3" en
la columna **Ej.**

La barra de filtros termina con dos botones, que lanzan la misma búsqueda pero
presentan el resultado de otra forma:

- **Buscar registros** — una línea por libro (la vista habitual);
- **Buscar ejemplares** — **una línea por ejemplar**. Los tres ejemplares de
  *El Principito* aparecerán entonces en tres líneas.

El botón del modo en curso se resalta: así ve de un vistazo qué está mirando. En
modo ejemplar, la columna "Ej." deja su sitio a tres columnas útiles:

- **Código Ofelia** — el código de barras de la etiqueta
- **Código Ofelia externo** — el código de otra biblioteca, si lo hay
- **Procedencia** — de dónde viene este ejemplar

Es la única pantalla que muestra que un mismo libro tiene un ejemplar
**comprado por la biblioteca** y otro **prestado por una biblioteca
asociada**. Combínela con el filtro **Procedencia** para localizar un fondo
entero, por ejemplo el día en que hay que devolverlo.

!!! tip "Devolver un fondo prestado"
    Marque **Buscar los ejemplares**, filtre por procedencia, marque
    **Seleccionar todo** y luego **Eliminar los ejemplares seleccionados**.
    Los libros salen del catálogo pero los registros se quedan: si la
    biblioteca asociada le presta los mismos títulos el año que viene, solo
    tendrá que volver a crear ejemplares. Véase
    [Procedencias](provenances.md).

## Una búsqueda tolerante

La búsqueda no es exigente: escribir "petit prince" también
encuentra "Le Petit Prince" y "petits princes". Puede escribir en
mayúsculas o minúsculas, con o sin acentos, en cualquier orden.
BibliOfelia hace el resto.

## Búsqueda por código de barras

Con un [escáner](../premiers-pas/saisie.md) o la [cámara de su
dispositivo](../premiers-pas/scanner-camera.md) (icono de cámara junto a la
barra de búsqueda), puede escanear directamente el código de barras de un
libro: la ficha del libro o del ejemplar se abre al instante.
