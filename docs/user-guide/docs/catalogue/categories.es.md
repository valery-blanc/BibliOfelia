# Categorías

Las **categorías** clasifican los libros: Novelas, Álbumes ilustrados,
Documentales… Cada registro recibe una, y es ella la que determina la
duración del préstamo por defecto.

Desde [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" }, abra
**Categorías** para crearlas, modificarlas o eliminarlas.

## Los campos

- **Código** — corto y sin espacios: `ENF-ALB`, `ADU-ROM`
- **Nombre** — lo que ven los bibliotecarios y los lectores
- **Abreviatura** — la **signatura** impresa en el lomo del libro (véase más
  abajo)
- **Categoría superior** — para colocar "Álbumes" bajo "Infancia"
- **Duración del préstamo** — en días; déjelo vacío para la duración por
  defecto de la biblioteca

## Las categorías incluidas

BibliOfelia viene con las **20 categorías oficiales Ofelia**: cinco franjas de
edad cruzadas con cuatro tipos de documento.

| | Ficción | Documental | Álbum | Cómic |
|---|---|---|---|---|
| Adultos | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Juvenil | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Adolescentes | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Infantil | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Primera infancia | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

El **código sirve también de signatura**: lo que se escribe en el lomo del libro
es lo que ve en el menú de categorías.

!!! info "El idioma no forma parte de la categoría"
    Un libro en inglés colocado en ficción para adultos va en `AD FIC`, no en una
    categoría «Inglés Adultos Ficción». El idioma se indica en la ficha del libro
    y se recupera con el filtro **Idioma** del catálogo. Una categoría por idioma
    multiplicaría las líneas sin aportar nada.

## La abreviatura, o signatura de estantería

Es la versión corta del nombre, la que cabe en una etiqueta de lomo. Para
"Novelas de ficción para adolescentes", se escribe `RO FI ADO`.

Vale para **todos** los registros de la categoría: se escribe una sola vez, y
dos libros de la misma categoría nunca podrán mostrar dos signaturas
distintas.

En la instalación, las 16 categorías incluidas reciben una abreviatura de
partida (`ENF ALB`, `ADU ROM`…). Puede sustituirlas por las suyas:
BibliOfelia nunca sobrescribirá una signatura que usted haya escrito.

Cuando las abreviaturas estén listas, imprima las
[etiquetas de lomo](../impressions/etiquettes.md).

## Eliminar una categoría

**No se elimina ningún libro.** Los registros afectados simplemente se
quedan sin categoría, y la pantalla de confirmación le dice cuántos son.
Podrá asignarles otra con las [operaciones por lotes](operations-lot.md).

## Ver también

- [Operaciones por lotes](operations-lot.md)
- [Imprimir las etiquetas](../impressions/etiquettes.md)
