# Glosario

Pequeño léxico de los términos usados en BibliOfelia.

## Los diferentes códigos: ¿para qué sirven?

BibliOfelia usa varios tipos de códigos para identificar los libros
y los miembros. Es importante distinguirlos bien porque no sirven
para lo mismo.

### Código Ofelia (en las etiquetas y las tarjetas)

Es el **código de barras** que se escanea con el escáner u
OfeliaScan. Empieza por **290** para un libro, o **291** para una
tarjeta de miembro. Tiene 13 dígitos en total.

Ejemplos:

- `2900000000017` → etiqueta de un libro
- `2910000000444` → tarjeta de un miembro

Es el código que BibliOfelia genera automáticamente cuando crea un
nuevo ejemplar o un nuevo miembro. Es el que se imprime en las
etiquetas y en las tarjetas físicas. Es el que se escanea para los
préstamos, las devoluciones, el inventario.

Una vez impreso, este código nunca cambia. Si una etiqueta o una
tarjeta se pierde, **no se imprime la misma**: se crea una nueva
con otro código (vea [Libro perdido](faq.md#livre-perdu)
y [Tarjeta perdida](faq.md#carte-perdue)).

### Código interno (en la ficha del libro, no en la etiqueta)

Junto al código Ofelia, cada libro también tiene un **código
interno** más legible para el bibliotecario. Tiene la forma
**OFL-AAAAMMDD-NNNN**:

- `OFL-20260525-0014` → 14º libro registrado el 25 de mayo de 2026

Este código aparece en BibliOfelia en la ficha del ejemplar.
Permite identificar rápidamente cuándo se registró un libro. **No
se escanea, no se imprime** en la etiqueta: es solo para facilitar
la gestión en pantalla.

### ISBN-13 (en la cubierta del libro, impreso por el editor)

Es el código de 13 dígitos que el **editor** imprime al dorso del
libro, generalmente junto a un código de barras estándar.
Identifica el título universalmente.

Ejemplo: `9782070612758` → identifica *El Principito* en Gallimard.

Cuando crea un nuevo registro, BibliOfelia consulta la base
OpenLibrary a partir del ISBN-13 para rellenar el título, el autor
y el editor. El ISBN-13 sirve sobre todo para el **catálogo**, no
para el préstamo diario.

Para el préstamo, es el código Ofelia del libro que se escanea,
**no el ISBN** (un libro puede tener 3 ejemplares: tienen el mismo
ISBN, pero cada uno su código Ofelia).

### ISBN-10 (formato antiguo)

Antes de 2007, los libros tenían un código de editor de 10 dígitos:
es el ISBN-10. Puede encontrarlo en libros antiguos. BibliOfelia
acepta los dos: si escribe un ISBN-10, se convierte automáticamente
en ISBN-13.

### ISSN (revistas y periódicos)

El **ISSN** es el equivalente del ISBN para las **revistas y periódicos**.
En el código de barras del reverso de una revista, empieza por **977**.

A diferencia del ISBN, el ISSN identifica **el título de la revista**, no un
número concreto: todos los números de una misma revista comparten el mismo
ISSN. Por lo tanto, BibliOfelia crea **una sola ficha** por revista, a la
que cada número añade un ejemplar. Una revista se cataloga como un libro,
simplemente escaneando su código de barras 977.

### Número de tarjeta / número de miembro

Es el código Ofelia de una tarjeta de miembro (prefijo 291).
También se llama "número de tarjeta" o "número de miembro" — es lo
mismo.

## Los otros términos

### BibliOfelia

El software de gestión de biblioteca, instalado en la **Ofelia
Box**. Se accede desde cualquier ordenador o tableta de la
biblioteca vía un navegador web.

### Consulta in situ

Un libro leído en la biblioteca sin ser prestado (cómic hojeado,
diccionario consultado para una tarea). Puede registrarse para las
estadísticas. Vea [Consulta in situ](prets-retours/consultation.md).

### Escáner

Lector de códigos de barras conectado por cable USB al ordenador.
Se comporta como un teclado: se escanea, el código aparece en el
campo de entrada. La herramienta más rápida.

### Ejemplar

Una copia física de un libro. Un registro puede tener varios
ejemplares (por ejemplo, 3 copias de *El Principito* en estante).
Cada ejemplar tiene su propio código Ofelia. Vea [Gestionar los
ejemplares](catalogue/exemplaires.md).

### Ubicación

El estante o sección donde se guarda un libro. Identificado por un
código corto (`A1`, `JUV`, `BD`…). Vea
[Ubicaciones](catalogue/localisations.md).

### Miembro

Un lector inscrito en la biblioteca. Posee una tarjeta con un
número único. También llamado **usuario** o **lector**.

### Registro

La ficha descriptiva de un libro (título, autor, ISBN…).
Independiente de los ejemplares físicos: un registro puede existir
sin ejemplar (libro referenciado pero no recibido aún) o con
varios ejemplares (libro popular). Vea [Añadir un
libro](catalogue/ajouter-livre.md).

### Ofelia Box

La pequeña caja (un mini-ordenador Raspberry Pi) que alberga
BibliOfelia. Conectada a la red de la biblioteca, difunde la
aplicación a todos los puestos conectados. No necesita Internet
para funcionar.

### OfeliaScan

La aplicación Android compañera de BibliOfelia. Permite escanear
los códigos de barras con un teléfono. Vea [Activar
OfeliaScan](ofeliascan/activer.md).

### Préstamo

El préstamo de un libro por un miembro, con una fecha de
devolución. Vea [Hacer un préstamo](prets-retours/faire-pret.md).

### Inventario

Inventario físico de un estante: se recorren los estantes y se
escanea cada libro para verificar que está en su sitio. Vea
[Inventario](inventaire/recolement.md).

### Reserva

Una solicitud de préstamo de un libro actualmente no disponible.
El miembro será atendido prioritariamente cuando el libro vuelva.
Vea [Reservas](reservations/creer.md).
