# Catalogar escaneando

Cuando llega una caja de libros, la **catalogación por escaneo** es la
forma más rápida de registrarlo todo: escanea los ISBN uno tras otro con
la cámara, y BibliOfelia crea las fichas y sus ejemplares de una vez.

Es, para la creación, el equivalente del [inventario](recolement.md)
para la verificación: un **escaneo continuo**, sin nada que pulsar entre
dos libros.

## Iniciar un lote de catalogación

Desde el [**Catálogo**](/bibliofelia/es/catalog/){ target="_blank" } (o
[**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" } → Inventario),
pulse
[**Catalogar escaneando**](/bibliofelia/es/catalog/scan/){ target="_blank" }
y luego [**Nuevo lote**](/bibliofelia/es/catalog/scan/new/){ target="_blank" }.

Antes de escanear, puede fijar **valores por defecto** para todo el lote:

- una **categoría** por defecto (Adultos, Infantil…);
- una **ubicación** por defecto (la estantería a la que irán estos libros);
- una **etiqueta** para volver a encontrar el lote más tarde.

Estos valores se aplican a cada libro del lote, pero podrá **cambiarlos
línea por línea** después.

## Escanear los ISBN en serie

1. Pulse **Iniciar el escaneo**: la cámara se abre en modo continuo.
2. Escanee el código de barras ISBN del **dorso** de cada libro (empieza por
   978 o 979).
3. En cada lectura, un **pitido** confirma y la línea aparece en la lista:
   BibliOfelia busca automáticamente el título, el autor y el idioma
   (OpenLibrary, Google Books, BnF…).
4. Durante el escaneo, la pantalla muestra el **título y el autor**
   encontrados — o, en su defecto, el ISBN y el idioma.

!!! tip "Varios ejemplares del mismo libro"
    ¿Tiene dos copias idénticas? Escanee el mismo ISBN **dos veces**. En el
    segundo paso (tras unos segundos), BibliOfelia muestra «ejemplar 2» en
    grande: añadirá un ejemplar más a la misma ficha, sin crear un
    duplicado. Un reescaneo demasiado rápido (menos de 3 segundos) se ignora,
    para evitar lecturas dobles.

!!! warning "Códigos Ofelia rechazados"
    La catalogación solo acepta **ISBN** (978/979). Si escanea por error una
    etiqueta de código Ofelia (290/291) ya pegada en un libro, se rechaza:
    aquí se registran libros nuevos, no ejemplares ya catalogados.

## Comprobar y ajustar el lote

Cuando pulse **Terminar**, aparece la lista del lote. Para cada línea, ve el
libro encontrado (autor, título, idioma) y puede:

- cambiar la **categoría**, la **ubicación** o el **estado** — por línea, o
  para varias líneas a la vez con las casillas y el botón **Marcar todo**;
- ajustar el **número de ejemplares**;
- **eliminar** una línea (icono de papelera) en caso de error de escaneo.

!!! info "Ficha ya existente"
    Si un ISBN corresponde a un libro **ya presente** en el catálogo,
    BibliOfelia no recrea la ficha: simplemente añade sus nuevos ejemplares
    a la ficha existente, sin modificarla.

## Guardar el lote

Pulse **Guardar el lote**. BibliOfelia crea todas las fichas que faltan y
todos los ejemplares, con sus códigos Ofelia.

## Imprimir solo las etiquetas de este lote

Cada ejemplar creado se vincula a **su lote de catalogación**. Así, al
imprimir las etiquetas, puede filtrar por este lote exacto: solo se ofrece
(y se marca de antemano) lo que acaba de registrar, sin sacar toda la
biblioteca. Consulte [Etiquetas de libros](../impressions/etiquettes.md).

## Véase también

- [Escanear con la cámara](../premiers-pas/scanner-camera.md) — cómo
  funciona la cámara
- [Añadir un libro](../catalogue/ajouter-livre.md) — crear una sola ficha a mano
- [Etiquetas de libros](../impressions/etiquettes.md) — imprimir las
  etiquetas del lote
