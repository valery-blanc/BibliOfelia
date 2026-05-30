# Recogida y expiración de una reserva

Una vez el libro ha llegado y el miembro ha sido avisado, hay que
ponerlo de lado mientras espera que venga a buscarlo. Si nadie
viene, la reserva expira y el libro se libera.

## Poner el libro de lado

Al momento de la devolución, si el libro desencadena una reserva,
BibliOfelia le indica con un mensaje:

> **A poner de lado para [Nombre del miembro]**

Guarde físicamente el libro en la zona de reservas (estantería
dedicada detrás del escritorio de recepción, por ejemplo), no en el
estante.

## Cuando el miembro viene a buscar

El miembro llega con su tarjeta. Haga un préstamo normal:

1. Abra la página **Préstamo**
2. Escanee la tarjeta
3. Escanee el libro

La reserva se transforma automáticamente en préstamo. Su fecha de
expiración se borra, su estado pasa a **Cumplida** en el historial.

## Expiración: el miembro no viene

Si el miembro avisado no viene a buscar su libro en un plazo
definido (por defecto 7 días), la reserva expira automáticamente.

Concretamente:

- La reserva pasa al estado **Expirada**
- El libro vuelve a estar disponible (o pasa al siguiente miembro
  de la cola)
- El botón **Poner de lado** desaparece: vuelva a poner el libro en
  el estante

!!! info "El plazo es configurable"
    El administrador puede ajustar la duración predeterminada en los
    parámetros (`pickup_hold_days`). Por defecto, es 7 días.

## Ver las reservas en riesgo de expirar

Desde **Informes → Reservas a recoger**, ve la lista de reservas
listas con su fecha de expiración. Las más próximas aparecen
arriba — es su lista de seguimientos prioritarios.

## Casos particulares

### El miembro quiere prolongar la espera

Si el miembro le dice que viene la próxima semana, puede abrir la
reserva y modificar la fecha de expiración manualmente para evitar
que expire demasiado pronto.

### El miembro renuncia

Si ya no quiere el libro, abra la reserva y haga clic en
**Cancelar**. El libro pasa al siguiente miembro o vuelve a estar
disponible.
