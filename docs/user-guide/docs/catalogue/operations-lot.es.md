# Operaciones en lote

Para ganar tiempo cuando tiene varios registros que modificar de la
misma manera, BibliOfelia ofrece **operaciones en lote** (o "acciones
masivas") desde la lista del catálogo.

## Seleccionar varios registros

Dos casillas, encima de la lista, marcan todo de una vez:

- **Seleccionar los N resultados visibles** — las líneas de la página mostrada.
- **Seleccionar los N resultados de la búsqueda** — **todas las páginas**. Esta
  casilla solo aparece si hay más de una página.

El número indicado es el real: así siempre sabe cuántos libros va a modificar o
eliminar.

!!! warning "No confunda las dos"
    Marcar «resultados visibles» solo toma la página actual: 25 líneas. En un
    fondo de varios cientos de libros, la casilla que necesita es la segunda.
    Marcar una desmarca la otra, y marcar una línea a mano cancela la selección
    ampliada.

Antes de una eliminación, la pantalla de confirmación recuerda el total. A
partir de 100 líneas solo muestra las 100 primeras e indica cuántas más
seguirán, pero **todas** se eliminarán.

Desde la página [**Catálogo**](/bibliofelia/es/catalog/){ target="_blank" },
cada línea de registro tiene una casilla de verificación a la izquierda. Marque los registros que quiere
procesar.

Aparece una barra de acciones arriba, con un contador ("3 registros
seleccionados") y las operaciones disponibles.

## Operaciones disponibles

### Asignar en masa desde el catálogo

En cuanto marca una línea, aparece una barra encima de la lista con menús
desplegables y un botón **Aplicar**.

**En modo registros** (la vista por defecto), dos menús:

- **Categoría** — se aplica a los registros marcados
- **Ubicación** — se aplica a **todos los ejemplares** de esos registros

**En modo ejemplares** (con "Buscar los ejemplares" marcado), un menú:

- **Procedencia** — se aplica a los ejemplares marcados

Cada información se ajusta donde vive: la categoría pertenece al libro, la
procedencia al ejemplar.

!!! tip "«No modificar» es el valor de partida"
    Un menú que se queda en **No modificar** no toca nada. Así puede cambiar la
    categoría sin vaciar la ubicación por descuido. Para quitar una asignación,
    elija **— (vaciar)**.

Después de aplicar, vuelve al catálogo **con sus filtros todavía activos**:
práctico para encadenar varios lotes.

### Eliminar los registros seleccionados

Para limpiar (libros que ya no están en la biblioteca, duplicados),
marque los registros y haga clic en **Eliminar los registros
seleccionados**.

!!! danger "Eliminación definitiva"
    Los registros Y todos sus ejemplares se eliminan. Los préstamos
    activos se marcan como **Perdido**, las reservas activas se
    cancelan. **Estas eliminaciones son definitivas.**

    Lea atentamente el mensaje de confirmación antes de validar. Los
    códigos de los ejemplares eliminados no podrán reutilizarse (vea
    [Casos frecuentes: libro perdido](../faq.md#livre-perdu)).

## Truco: seleccionar todo en la página

La casilla en la cabecera de la columna selecciona (o desmarca)
todos los registros visibles en la página. Si ha activado un filtro
(por ejemplo "categoría = Obsoleto"), solo selecciona los registros
filtrados.

!!! tip "Filtrar bien antes de marcar todo"
    Para una operación en lote, lo más seguro es **filtrar primero**
    para ver solo los registros a tratar, y luego **marcar todo**.
    Evita errores por descuido.
