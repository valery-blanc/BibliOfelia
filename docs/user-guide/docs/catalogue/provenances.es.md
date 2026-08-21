# Procedencias

Una **procedencia** dice de dónde viene un ejemplar: comprado por la
biblioteca, donado por alguien, prestado por una biblioteca asociada.

La lleva el **ejemplar**, no el libro. Esto importa: puede tener
perfectamente dos ejemplares del mismo título, uno comprado por Ofelia y
otro prestado por la mediateca vecina.

## Crear una procedencia

Desde [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" }, abra
**Procedencias** y haga clic en **Nueva procedencia**.

- **Código** — corto y sin espacios: `OFELIA`, `BM-GE`, `DON-DUPONT`
- **Nombre completo** — lo que verán los bibliotecarios en las listas:
  "Préstamo Biblioteca de Ginebra"
- **Notas** — el contacto, la fecha de devolución prevista, las condiciones
  del depósito

## Asignar una procedencia

Tres formas, de la más rápida a la más puntual:

1. **Al catalogar** — cuando inicia un lote de escaneo, elija una
   **procedencia por defecto**: todos los ejemplares del lote la recibirán.
   Es el método adecuado para una caja de libros prestados.
2. **Desde el catálogo** — marque **Buscar los ejemplares**, seleccione las
   líneas deseadas y luego **Asignar una procedencia**.
3. **De uno en uno** — el campo **Procedencia** del formulario de ejemplar.

La [importación Excel](../inventaire/catalogage-excel.md) también acepta una
columna `PROVENANCE`.

## Devolver un fondo prestado

Es el caso que justifica todo lo demás:

1. Abra el [**Catálogo**](/bibliofelia/es/catalog/){ target="_blank" }
2. Marque **Buscar los ejemplares**
3. Filtre por la procedencia correspondiente
4. **Seleccionar todo** y luego **Eliminar los ejemplares seleccionados**

Verá la lista exacta antes de confirmar. Los ejemplares desaparecen, los
registros se quedan en el catálogo.

!!! warning "Compruebe los préstamos en curso"
    La pantalla de confirmación le indica cuántos de esos libros están en
    manos de un lector. Su préstamo se cerrará como "perdido": mejor
    recuperarlos antes o esperar a que los devuelvan.

## Eliminar una procedencia

Mientras un ejemplar la lleve, BibliOfelia **se niega** a eliminarla: sería
perder el único rastro del origen de esos libros. La pantalla le propone
entonces ver los ejemplares afectados para tratarlos primero.

## Ver también

- [Gestionar los ejemplares](exemplaires.md)
- [Búsqueda](recherche.md)
- [Catalogar desde Excel](../inventaire/catalogage-excel.md)
