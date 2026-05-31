# Inventario (revisión de las estanterías)

El **inventario** consiste en recorrer las estanterías y comprobar que cada
libro está en su sitio. Es la operación más potente del sistema: recorre las
estanterías escaneando con la **cámara**, y BibliOfelia se actualiza
automáticamente.

El inventario se hace ahora **directamente desde el sitio**, con la cámara de
su teléfono o tableta — sin aplicación que instalar. (OfeliaScan sigue siendo
posible para los inventarios masivos, véase al final de la página.)

## Preparar el inventario

Antes de empezar:

1. Elija la **estantería** a inventariar (una cada vez para no perderse).
2. Lleve un dispositivo con cámara (teléfono, tableta).
3. Abra la página **Avanzado → Inventario** en ese dispositivo.

!!! warning "Se requiere conexión segura para la cámara"
    La cámara solo funciona con una conexión **segura (https://)**. Consulte
    [Escanear con la cámara](../premiers-pas/scanner-camera.md) si la cámara
    se niega a abrirse.

## Iniciar una sesión de inventario

1. Pulse **Nueva sesión de inventario**.
2. Elija el **alcance**: una **ubicación** concreta (p. ej. «Estantería A1»)
   o **todo el fondo**. Si elige una ubicación, seleccionarla pasa a ser
   obligatorio.
3. Confirme: BibliOfelia abre directamente la página de **informe**, que
   sirve también como pantalla de registro.

## Escanear los libros en continuo

1. Pulse **Iniciar el inventario**: la cámara se abre en **modo continuo** y
   permanece abierta.
2. Escanee cada libro de la estantería, uno tras otro. Un **pitido** (y una
   vibración) confirma cada libro nuevo, y un **contador** sube en pantalla.
3. Para cada escaneo:
   - libro **en la estantería correcta**: se marca como «visto»;
   - libro **colocado en otro sitio** (alcance = una ubicación): BibliOfelia
     actualiza automáticamente su estantería a la que está inventariando;
   - **código desconocido**: se señala, a investigar.

El mismo libro escaneado dos veces se cuenta una sola vez. Si una ficha tiene
varios ejemplares, la pantalla indica «ejemplar 2», «ejemplar 3»… para
ayudarle a encontrarlos todos.

!!! tip "Vaya rápido, no piense"
    No hace falta comprobar cada escaneo: BibliOfelia lo ordena todo al final.
    Concéntrese en la velocidad y la cobertura completa de la estantería. La
    lista y los contadores se actualizan en directo.

Cuando haya recorrido la estantería, pulse **Terminar**.

## Leer el informe

El informe se muestra **por ficha**, ordenado por autor y título. Todos los
códigos Ofelia aparecen como pastillas:

- **verde**: ejemplar encontrado durante el inventario;
- **rojo**: ejemplar **ausente** (presente en la base, no visto en la
  estantería).

También ve el número de libros escaneados, desplazados automáticamente, y los
códigos desconocidos encontrados.

## ¿Qué hacer con los libros ausentes?

Para cada ejemplar en rojo, dos opciones:

- **Está en otro lugar de la biblioteca**: inventaríe las demás estanterías,
  se reposicionará automáticamente al pasar.
- **Está perdido**: marque el ejemplar como **Perdido** desde su ficha (véase
  [Libro perdido](../faq.md#livre-perdu)).

## Frecuencia recomendada

- **Biblioteca pequeña**: inventario completo 1 a 2 veces al año.
- **Biblioteca grande**: 1 estantería al mes por rotación.

Hágalo idealmente cuando la biblioteca esté tranquila (por la mañana, día de
cierre).

## ¿Y OfeliaScan?

Para los **inventarios grandes**, la aplicación móvil [OfeliaScan](../ofeliascan/activer.md)
también puede enviar una sesión entera de escaneos a BibliOfelia. La lógica es
la misma (libros vistos, desplazados, ausentes). Para el inventario corriente
de una sola estantería, la cámara del sitio descrita arriba es lo más sencillo.
