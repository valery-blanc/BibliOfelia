# Renovar un préstamo

Si un miembro quiere conservar un libro más tiempo, puede renovar su
préstamo sin que necesite traer el libro.

## Desde la ficha del miembro

La forma más sencilla: abra la [ficha del miembro](../usagers/fiche.md)
y encuentre el préstamo a renovar en la sección **Préstamos activos**.

![Préstamos activos en la ficha de un miembro](../assets/screenshots/es/usagers/member-detail.png)

A la derecha de cada línea, el botón **Renovar** prolonga la fecha
de devolución por una duración estándar (por defecto 21 días a
contar desde hoy).

## ¿Cuántas veces se puede renovar?

Por defecto, un préstamo puede renovarse una vez. Más allá,
BibliOfelia bloquea la renovación: el miembro debe devolver el libro
(aunque sea para volverlo a prestar si nadie lo ha reservado).

Este máximo es configurable por el administrador en los parámetros.

## Casos en los que se rechaza la renovación

- **El libro está reservado** por otro miembro: no es posible
  renovar, el miembro actual debe devolver el libro
- **El miembro ha alcanzado el número máximo de renovaciones** para
  este préstamo
- **La tarjeta del miembro está expirada**: renueve la tarjeta
  primero ([Renovación de tarjeta](../usagers/renouvellement.md))

## Caso especial: renovación sin tener el libro a mano

Si el miembro le llama para una renovación, abra su ficha desde la
búsqueda global (escriba su nombre), encuentre el libro afectado y
haga clic en **Renovar**. Sin necesidad de escaneo.
