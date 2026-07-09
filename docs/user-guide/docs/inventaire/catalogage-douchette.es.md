# Catalogar con el lector USB

Si su puesto tiene un **lector de código de barras USB** (un lector con cable
que se conecta como un teclado), puede catalogar una caja de libros **sin
cámara**: escanea los ISBN uno tras otro, directamente en la pantalla de
BibliOfelia.

Es el equivalente, con el lector, del [catalogado por
cámara](catalogage-scan.md): mismo resultado (BibliOfelia crea las fichas y los
ejemplares), pero controlado por el lector del puesto fijo.

!!! info "¿Lector o cámara?"
    El **lector USB** es ideal en un escritorio, en un puesto fijo, y funciona
    incluso sin conexión segura (`https://`). La **cámara** es ideal en
    movimiento, con la tableta en la mano. Ambos rellenan el mismo catálogo.

## Iniciar un lote con el lector

Desde [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" } → Inventario,
pulse
[**Catalogado con el lector**](/bibliofelia/es/catalog/scan/new-douchette/){ target="_blank" }.

Como en el catalogado por cámara, puede fijar **valores por defecto** para todo
el lote (categoría, ubicación, etiqueta). Podrá **cambiarlos línea por línea**
después.

## Escanear los ISBN uno tras otro

1. La página se abre con el campo de entrada **ya activo**: no tiene **nada que
   pulsar**.
2. Escanee el código de barras ISBN del **dorso** de cada libro (empieza por
   978 o 979) con el lector.
3. En cada lectura, la línea aparece en la lista: BibliOfelia busca
   automáticamente el título, el autor y el idioma (OpenLibrary, Google Books,
   BnF…).

!!! tip "Varios ejemplares del mismo libro"
    ¿Tiene dos copias idénticas? Escanee el mismo ISBN **dos veces**. En el
    segundo paso (tras unos segundos), BibliOfelia añade un ejemplar adicional a
    la misma ficha, sin crear un duplicado. Un reescaneo demasiado rápido se
    ignora, para evitar lecturas dobles.

!!! warning "Códigos Ofelia rechazados"
    El catalogado acepta los **ISBN** de libros (978/979) y los **ISSN** de
    revistas (977). Si escanea por error una etiqueta de código Ofelia
    (290/291) ya pegada en un documento, se rechaza: aquí se registran
    documentos nuevos, no ejemplares ya catalogados.

## Terminar y revisar el lote

Cuando haya terminado de escanear, pulse **Terminar y ver el lote**. Aparece la
lista del lote. Para cada línea ve el libro encontrado (autor, título, idioma) y
puede:

- cambiar la **categoría**, la **ubicación** o el **estado** — por línea, o para
  varias líneas a la vez con las casillas;
- ajustar el **número de ejemplares**;
- **eliminar** una línea (icono de papelera) en caso de error de escaneo.

## Guardar el lote

Pulse **Enviar al catálogo**. BibliOfelia crea todas las fichas que faltan y
todos los ejemplares, con sus códigos Ofelia. Después puede [imprimir solo las
etiquetas de este lote](../impressions/etiquettes.md).

## Véase también

- [Catalogar escaneando (cámara)](catalogage-scan.md) — lo mismo con la cámara
- [Modos de entrada](../premiers-pas/saisie.md) — lector, cámara, teclado
- [Etiquetas de libros](../impressions/etiquettes.md) — imprimir las etiquetas
  del lote
