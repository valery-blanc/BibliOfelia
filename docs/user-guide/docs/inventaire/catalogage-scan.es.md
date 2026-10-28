# Catalogar escaneando

Cuando llega una caja de libros, la **catalogación por escaneo** es la
forma más rápida de registrarlo todo: escanea los ISBN uno tras otro, y
BiblOFELIA crea las fichas y sus ejemplares de una vez.

Dos herramientas hacen el mismo trabajo. La **cámara** del teléfono o de
la tableta, y el **lector USB** conectado a un puesto fijo. Solo cambia la
forma de leer el código de barras. El lote, los valores por defecto, la
revisión y el envío al catálogo son los mismos.

Es, para la creación, el equivalente del [inventario](recolement.md)
para la verificación: un **escaneo continuo**, sin nada que pulsar entre
dos libros.

!!! info "¿Cámara o lector USB?"
    El **lector USB** es ideal en un escritorio, en un puesto fijo, y funciona
    incluso sin conexión segura (`https://`). La **cámara** es ideal en
    movimiento, con la tableta en la mano. Ambos rellenan el mismo catálogo.

## Para qué sirve una sesión de catalogación

Una **sesión** de catalogación (también llamada **lote**) sirve para añadir
**muchos libros a la vez** al catálogo. Funciona en tres tiempos:

1. **Abre un lote y escanea** todos los libros de la caja, uno tras otro. Nada
   entra todavía en el catálogo: el lote solo es una lista de trabajo, que puede
   corregir o vaciar.
2. **Comprueba la lista** — y sobre todo, aplica **modificaciones por lote**:
   marque varias líneas (o todas) y asígneles, con un solo clic, la misma
   **clasificación**, la misma **ubicación** en la biblioteca o el mismo **estado**.
   Ahí está todo el interés de catalogar juntos los libros que van juntos.
3. **Envía el lote al catálogo**: las fichas y los ejemplares se crean de verdad,
   con la **procedencia** elegida al inicio, y puede imprimir de una vez las
   etiquetas **solo de ese lote**.

Un lote validado sigue consultable: desde la lista de lotes, **Ver el lote**
recuerda qué libros contenía, con un enlace a cada ficha.

## Iniciar un lote

Las dos entradas abren **el mismo formulario**. Elija los
[valores por defecto](#defauts) y pulse **Iniciar la catalogación**.

### Con la cámara { #camera }

Desde el [**Catálogo**](/bibliofelia/es/catalog/){ target="_blank" },
pulse
[**Catalogar escaneando**](/bibliofelia/es/catalog/scan/){ target="_blank" }
y luego [**Nuevo lote**](/bibliofelia/es/catalog/scan/new/){ target="_blank" }.

La misma pantalla está también en
[**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" } → Inventario →
**Catalogación por escaneo**.

### Con el lector USB { #douchette }

Desde [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" } →
Inventario, pulse
[**Catalogación con lector de código de barras**](/bibliofelia/es/catalog/scan/new-douchette/){ target="_blank" }.

## Valores por defecto del lote { #defauts }

Antes de escanear, puede fijar **valores por defecto** para todo el lote.
**Es opcional**: un lote sin clasificación, sin ubicación y sin procedencia
se cataloga perfectamente.

Para usar uno de estos valores, hay que **haberlo creado antes**. El
formulario del lote solo ofrece lo que ya existe, y no permite añadir uno
nuevo. Estas listas están en
[**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" } → Metadatos:

- una [**clasificación**](/bibliofelia/es/catalog/categories/){ target="_blank" }
  por defecto (Juventud Documental, Adultos Ficción…). Las clasificaciones
  Ofelia ya vienen incluidas; abra la lista solo para añadir una;
- una [**ubicación**](/bibliofelia/es/catalog/locations/){ target="_blank" }
  por defecto (la estantería a la que irán estos libros);
- una [**procedencia**](/bibliofelia/es/catalog/provenances/){ target="_blank" }
  por defecto — de dónde vienen estos libros: compra de la biblioteca,
  donación, préstamo de otra biblioteca. **Todos los ejemplares del lote**
  la reciben. Es la elección adecuada para una caja de libros prestados: el
  día de la devolución, un filtro sobre esta procedencia los encuentra
  todos;
- un **nombre del lote**, para volver a encontrarlo más tarde. Se escribe
  directamente: no hay lista que preparar.

La clasificación y la ubicación se aplican a cada libro, y podrá
**cambiarlas después**, una línea o varias a la vez. La procedencia es la
de **todo el lote**: se elige aquí, antes de escanear. Para modificarla una
vez creados los ejemplares, pase por
[Procedencias](/bibliofelia/es/catalog/provenances/){ target="_blank" }.

## Escanear los ISBN en serie

El código de barras ISBN está en el **dorso** del libro. Empieza por 978 o
979. En cada lectura, BiblOFELIA busca automáticamente el título, el autor
y el idioma (OpenLibrary, Google Books, BnF…).

### Con la cámara

1. Pulse **Escanear libros**: la cámara se abre en modo continuo.
2. Escanee cada libro.
3. Un **pitido** confirma la lectura. La pantalla muestra el **título y el
   autor** encontrados — o, en su defecto, el ISBN y el idioma.
4. Pulse **Terminar**: la cámara se cierra y aparece la lista del lote,
   lista para revisarla.

### Con el lector USB

1. La página se abre con el campo de entrada **ya activo**: no tiene
   **nada que pulsar**.
2. Escanee cada libro con el lector. La línea aparece en la lista sobre la
   marcha.
3. Cuando haya terminado, pulse **Terminar y revisar el lote** para pasar
   a la revisión.

En ambos casos, el campo **Introducir un ISBN a mano** permite teclear un
código dañado y luego **Añadir**.

!!! tip "Varios ejemplares del mismo libro"
    ¿Tiene dos copias idénticas? Escanee el mismo ISBN **dos veces**. En el
    segundo paso (tras unos segundos), BiblOFELIA indica «ejemplar 2» — en
    grande en el visor de la cámara, en la lista con el lector. Añadirá un
    ejemplar más a la misma ficha, sin crear un duplicado. Un reescaneo
    demasiado rápido (menos de 3 segundos) se ignora, para evitar lecturas
    dobles.

!!! warning "Códigos Ofelia rechazados"
    La catalogación acepta los **ISBN** de libros (978/979) y los **ISSN**
    de revistas (977, ver más abajo). Si escanea por error una etiqueta de
    código Ofelia (290/291) ya pegada en un documento, se rechaza: aquí se
    registran documentos nuevos, no ejemplares ya catalogados.

## Catalogar una revista o un periódico

Las revistas y los periódicos no tienen ISBN, sino un **ISSN**: un código de
barras que empieza por **977**. No hace falta una herramienta aparte —
escanee ese código de barras 977 **en el mismo lote** que sus libros, con la
cámara o con el lector USB.

- BiblOFELIA reconoce el ISSN y busca el **título de la revista** (BnF, BNE).
- Todos los números de una misma revista comparten el **mismo ISSN**: por lo
  tanto recaen en una **única ficha «revista»**, a la que cada número
  escaneado añade un ejemplar.

!!! info "Un ISSN = una sola ficha de revista"
    Si escanea dos números diferentes de la misma revista, BiblOFELIA no
    crea dos fichas: añade un ejemplar a la ficha de la revista. Para
    distinguir los números (fecha, n.º), anótelos en las notas del ejemplar.

## Comprobar y ajustar el lote

La lista es la misma, tanto si el lote se escaneó con la cámara como con el
lector USB. Para cada línea, ve el libro encontrado (autor, título, idioma)
y puede:

- cambiar la **clasificación**, la **ubicación** o el **estado**: marque una
  o varias líneas (la casilla de la cabecera de la tabla las marca todas),
  elija los valores en **Modificar las filas marcadas** y luego **Aplicar a
  las filas marcadas**;
- ajustar el **número de ejemplares** en la línea;
- **eliminar** una línea (icono de papelera) en caso de error de escaneo.

**Guardar** conserva estos ajustes sin crear nada en el catálogo. Puede
retomar el lote más tarde.

!!! info "Ficha ya existente"
    Si un ISBN corresponde a un libro **ya presente** en el catálogo,
    BiblOFELIA no recrea la ficha: simplemente añade sus nuevos ejemplares
    a la ficha existente, sin modificarla.

## Enviar el lote al catálogo

Pulse **Enviar al catálogo**. BiblOFELIA crea todas las fichas que faltan y
todos los ejemplares, con sus códigos Ofelia y la **procedencia** elegida al
iniciar el lote.

## Imprimir solo las etiquetas de este lote

Cada ejemplar creado se vincula a **su lote de catalogación**. Así, al
imprimir las etiquetas, puede filtrar por este lote exacto: solo se ofrece
(y se marca de antemano) lo que acaba de registrar, sin sacar toda la
biblioteca. Consulte [Etiquetas de libros](../impressions/etiquettes.md).

## Véase también

- [Procedencias](../catalogue/provenances.md) — de dónde viene un ejemplar,
  y cómo volver a encontrar un fondo prestado
- [Escanear con la cámara](../premiers-pas/scanner-camera.md) — cómo
  funciona la cámara
- [Modos de entrada](../premiers-pas/saisie.md) — lector, cámara, teclado
- [Añadir un libro](../catalogue/ajouter-livre.md) — crear una sola ficha a
  mano
- [Etiquetas de libros](../impressions/etiquettes.md) — imprimir las
  etiquetas del lote
