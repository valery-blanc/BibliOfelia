# Preguntas frecuentes

## Sobre la conexión y las cuentas

### Olvidé mi contraseña, ¿qué hago?

BibliOfelia funciona sin conexión y no envía correos de
restablecimiento. Pida al administrador de la Box que restablezca su
contraseña directamente desde la consola de administración.

### Mi cuenta está bloqueada tras varios intentos

Es una protección contra los intentos de intrusión. Espere unos
minutos o pida al administrador que desbloquee la cuenta.

## Sobre los préstamos y devoluciones

### ¿Puede un miembro prestar un libro ya prestado?

No. Pero puede **reservarlo**: en cuanto el libro vuelva, se pondrá
de lado para él. Vea [Crear una reserva](reservations/creer.md).

### ¿Cuántos libros puede prestar un miembro al mismo tiempo?

Depende de la categoría del miembro. Por defecto: 5 para un adulto,
3 para un niño. El administrador puede ajustar.

### ¿Se puede prestar a un miembro con tarjeta expirada?

No. Renueve la tarjeta primero (vea
[Renovación](usagers/renouvellement.md)), luego registre el
préstamo.

## Sobre el catálogo

### ¿Cómo añadir un libro rápidamente?

Si el libro tiene un ISBN, escríbalo en el formulario de nuevo
registro: BibliOfelia consulta OpenLibrary y rellena la ficha
automáticamente. Vea [Añadir un libro](catalogue/ajouter-livre.md).

### ¿Qué hacer si el ISBN no se encuentra?

Introduzca la información manualmente. Es raro pero posible para
libros muy recientes o muy antiguos.

### ¿Cómo reorganizar un estante?

Haga un inventario en la nueva ubicación: todos los
libros escaneados se reclasificarán automáticamente. Vea
[Inventario](inventaire/recolement.md).

## Sobre las reservas

### ¿Pueden varios miembros reservar el mismo libro?

Sí. Se colocan en una cola: el primero en reservar será atendido
primero cuando el libro vuelva.

### ¿Cómo saber cuándo avisar a un miembro?

El panel muestra permanentemente una tarjeta **Notificaciones por
hacer**. Vea [Notificaciones y
seguimientos](reservations/notifications.md).

## Sobre OfeliaScan

### ¿Hace falta un teléfono por bibliotecario?

No obligatorio. Pueden compartir un teléfono, o usar su propio
teléfono Android personal.

### ¿Necesita OfeliaScan Internet?

No. Se comunica con BibliOfelia vía el Wi-Fi local de la Ofelia
Box. No se requiere conexión a Internet para el uso diario.

## Sobre los idiomas

### ¿Puedo escribir un título en malagache?

Sí. BibliOfelia acepta todos los caracteres Unicode (acentos,
alfabetos no latinos). Escriba el título tal cual.

### ¿Puede el miembro francófono tener una tarjeta en francés aunque yo
trabaje en inglés?

Sí. Al imprimir la tarjeta, elija el idioma en el selector. Puede
generar PDFs en idiomas diferentes sin cambiar su propio idioma de
interfaz.

## Sobre las copias de seguridad

### ¿Están respaldados mis datos?

El administrador configura copias de seguridad automáticas diarias
en la Box. Ve la **Última copia de seguridad** en el panel **Estado
del sistema** del panel.

Si no es de hoy o ayer, avise al administrador.

## Casos difíciles

### Un libro está perdido o muy dañado, ¿cómo lo saco? { #livre-perdu }

Para un libro perdido durante un préstamo: abra la [ficha del
miembro](usagers/fiche.md), encuentre el préstamo en **Préstamos
activos** y haga clic en **Perdido**. El préstamo y el ejemplar pasan
al estado *Perdido*; el miembro conserva su historial y puede seguir
prestando. Para un libro devuelto demasiado dañado: registre la
devolución, luego en la [ficha del ejemplar](catalogue/exemplaires.md)
haga clic en **Descartar**. BibliOfelia no gestiona ni multas ni
facturación: el reemplazo depende de sus reglas internas.

### ¿Cómo eliminar definitivamente un registro del catálogo? { #supprimer-notice }

Si un registro ya no tiene ningún ejemplar (todos perdidos, donados,
tirados), abra su ficha y haga clic en **Eliminar el registro**, o use
una [operación en lote](catalogue/operations-lot.md). El código Ofelia
de un ejemplar eliminado queda reservado para siempre: una etiqueta que
aún circule nunca podrá designar otro libro por error.

### Un miembro perdió su tarjeta, ¿qué hago? { #carte-perdue }

Abra la [ficha del miembro](usagers/fiche.md) y haga clic en
**Reemplazar la tarjeta**: BibliOfelia asigna un nuevo número, retira
el antiguo definitivamente y conserva todo el historial. La tarjeta
antigua ya no funciona (cualquier escaneo devuelve un error) —
destrúyala si reaparece. Mientras espera la nueva tarjeta, el miembro
puede prestar siendo buscado por su nombre. Reimprima la tarjeta desde
[Imprimir las tarjetas](impressions/cartes.md).

### ¿Cómo gestionar un atraso prolongado? { #retard }

Siga los atrasos con el contador **Préstamos vencidos** del panel y
**Informes → Préstamos vencidos**. Según la gravedad: (1) llame al
miembro (teléfono visible en su ficha); (2) para bloquear sus
préstamos, **desactive** temporalmente al miembro desde su ficha y
reactívelo cuando devuelva los libros; (3) para un atraso de varios
meses, marque el préstamo como **Perdido**. BibliOfelia no genera
cartas de aviso: el teléfono, el SMS o un tablero siguen siendo lo más
eficaz en una biblioteca pequeña.

## ¿Una pregunta que no aparece?

Contacte al administrador de su Box.
