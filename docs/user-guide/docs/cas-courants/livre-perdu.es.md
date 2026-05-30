# Libro perdido o dañado

Cuando un libro no vuelve, se daña o debe salir del catálogo, hay
que sacarlo correctamente de BibliOfelia.

## Libro perdido durante un préstamo

Cuando un miembro declara haber perdido un libro:

1. Abra la [ficha del miembro](../usagers/fiche.md)
2. Encuentre el préstamo afectado en **Préstamos activos**
3. Haga clic en el botón **Perdido** a la derecha de la línea
4. Confirme

Consecuencias:

- El préstamo pasa al estado **Perdido**
- El ejemplar pasa al estado **Perdido**
- El ejemplar ya no aparece como disponible
- El miembro ya no tiene este préstamo en sus libros activos

El miembro conserva su historial y puede seguir prestando otros
libros. Le corresponde a usted gestionar el reemplazo o la multa
según sus reglas internas (BibliOfelia no gestiona la facturación).

## Libro dañado pero recuperado

Si el libro se devuelve demasiado dañado para ser prestado de nuevo:

1. Registre la **devolución** normalmente
2. Abra la [ficha del ejemplar](../catalogue/exemplaires.md)
3. Haga clic en **Descartar**

El libro permanece en el catálogo (para memoria) pero ya no se
puede prestar.

## Sacar definitivamente un libro del catálogo

Si el registro ya no tiene ningún ejemplar (todos perdidos, donados,
tirados), puede eliminar el registro mismo:

1. Abra la ficha del registro
2. Haga clic en **Eliminar el registro**
3. Confirme

O use la [operación en lote](../catalogue/operations-lot.md) para
eliminar varios de una vez.

!!! danger "El código Ofelia nunca se reutiliza"
    Cuando elimina un ejemplar, su código Ofelia queda reservado:
    ningún otro libro llevará el mismo código en el futuro. Esto
    evita que una etiqueta que aún circula en algún lugar (basura,
    libro donado) designe por error otro libro al ser escaneada.

    Concretamente: si la etiqueta de un libro eliminado se escanea
    más tarde, BibliOfelia responde "código desconocido" — y no
    "aquí está el libro X" que sería una confusión grave.

## Ver también

- [Gestionar los ejemplares](../catalogue/exemplaires.md)
- [Operaciones en lote](../catalogue/operations-lot.md)
