# Escanear con la cámara

BibliOfelia puede escanear códigos de barras **directamente con la
cámara** de su dispositivo: teléfono, tableta o portátil con webcam.
Sin aplicación que instalar: todo ocurre en el navegador.

Es el modo que usan todos los botones **Escanear** del sitio (la franja
del panel, las páginas Préstamo y Devolución, la búsqueda y el campo ISBN
de una ficha).

## Cómo funciona

1. Pulse un botón **Escanear** (o el icono redondo de cámara junto a un
   campo de búsqueda).
2. La cámara se abre en una ventana, con una **banda de mira** en el centro
   de la pantalla.
3. Coloque el código de barras del libro o de la tarjeta **dentro de la
   banda central**. No hace falta apuntar a toda la imagen: solo se lee lo
   que pasa por la banda.
4. En cuanto se reconoce el código, oirá un **pitido** (y el teléfono
   vibra). El código se rellena automáticamente.

!!! tip "Apunte a la banda, no a toda la pantalla"
    La lectura se limita a propósito a una banda horizontal en el centro de
    la imagen. Así se evita leer por error un código de barras vecino cuando
    hay varios libros juntos. Acerque el libro hasta que su código de barras
    ocupe el ancho de la banda.

## Dos formas de escanear

Según la página, la cámara funciona de forma distinta:

- **Escaneo único** (Préstamo, Devolución, búsqueda, ISBN): la cámara lee
  **un** código, luego se cierra y rellena el campo. Vuelva a iniciar el
  escaneo para el siguiente.
- **Escaneo continuo** (Inventario, Catalogación por escaneo): la cámara
  **permanece abierta** y encadena las lecturas. Aparece un contador y un
  pitido confirma cada libro nuevo. Recorre toda una estantería o una caja
  sin volver a pulsar. Pulse **Terminar** cuando acabe.

## Qué lee la cámara

La cámara solo reconoce **códigos de barras de libros y de tarjetas**
(formato EAN-13, 13 cifras). Es intencionado: hace la lectura mucho más
fiable y evita lecturas falsas. Se reconocen:

- los **ISBN** del dorso de los libros (que empiezan por 978 o 979);
- los **códigos Ofelia** de las etiquetas y de las tarjetas de socio (que
  empiezan por 290 o 291).

## ¿La cámara no se abre?

Algunos puntos que comprobar:

!!! warning "Se requiere conexión segura (HTTPS)"
    Por seguridad, los navegadores solo permiten la cámara con una conexión
    **segura (https://)**. Si accede a BibliOfelia por una dirección local
    en `http://` (por ejemplo `http://ofelia.local`), la cámara no podrá
    abrirse. En ese caso, use un **lector de códigos** o la **entrada por
    teclado**, o pida al administrador de la Box la dirección segura.

- **Permiso denegado**: la primera vez, el navegador pide permiso para usar
  la cámara. Responda **Permitir**. Si lo rechazó, vuelva a autorizar la
  cámara en los ajustes del sitio (el icono de candado a la izquierda de la
  dirección).
- **Ninguna cámara detectada**: en un puesto fijo sin webcam, la cámara no
  está disponible — use un lector de códigos o el teclado.
- **Mensaje de error claro**: si algo falla, BibliOfelia muestra el motivo
  exacto y le invita a **escribir el código a mano**. Nunca se queda
  bloqueado.

## ¿Y si no tengo cámara?

Todos los flujos siguen siendo utilizables **sin cámara**:

- un **lector** USB de códigos se comporta como un teclado ultrarrápido;
- la **entrada por teclado** siempre es posible (escriba el código, luego
  **Intro** o **Validar**).

Consulte [Modos de entrada](saisie.md) para elegir la herramienta adecuada.

## Véase también

- [Hacer un préstamo](../prets-retours/faire-pret.md)
- [Catalogar escaneando](../inventaire/catalogage-scan.md)
- [Inventario](../inventaire/recolement.md)
