# Clasificaciones

Las **clasificaciones** ordenan los libros: Juventud Documental, Adultos
Ficción, Infancia Álbum… Cada ficha recibe una, y es ella la que determina
la duración del préstamo por defecto.

Desde [**Avanzado**](/bibliofelia/es/advanced/){ target="_blank" }, abra
**Clasificaciones** para crearlas, modificarlas o eliminarlas.

## Los campos

- **Código** — identificador único. En las clasificaciones Ofelia coincide
  con el código de clasificación (`JE DOC`)
- **Nombre** — lo que ven bibliotecarios y lectores (p. ej. « Juventud
  Documental »)
- **Código de clasificación** — lo que se **imprime en el lomo** del libro
  (véase más abajo)
- **Clasificación superior** — para agrupar una clasificación bajo otra
- **Duración del préstamo** — en días; déjelo vacío para el valor por
  defecto de la biblioteca

## Las clasificaciones incluidas

BibliOfelia llega con las **20 clasificaciones oficiales Ofelia**: cinco
franjas de edad cruzadas con cuatro tipos de documento.

| | Ficción | Documental | Álbum | Cómic |
|---|---|---|---|---|
| Adultos | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Juventud | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Adolescentes | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Niños | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Primera infancia | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

El **código sirve también de código de clasificación**: lo escrito en el
lomo es lo que ve en el menú.

!!! info "El idioma no forma parte de la clasificación"
    Un libro en inglés colocado en ficción adulta va a `AD FIC`, no a una
    clasificación « Inglés Adultos Ficción ». El idioma se indica en la ficha
    del libro y se recupera con el filtro **Idioma** del catálogo. Una
    clasificación por idioma multiplicaría las filas sin aportar nada.

## El código de clasificación

Es la versión corta del nombre, la que cabe en una etiqueta de lomo. Para
« Juventud Documental » se escribe `JE DOC`.

Vale para **todas** las fichas de la clasificación: una sola captura, y dos
libros de la misma clasificación no podrán mostrar nunca dos códigos
distintos.

En la instalación, las clasificaciones incluidas reciben un código de
partida (`JE DOC`, `AD FIC`…). Puede sustituirlos por los suyos:
BibliOfelia nunca reescribirá un código que usted haya tecleado.

Una vez los códigos en su sitio, imprima las
[etiquetas de lomo](../impressions/etiquettes.md).

## Eliminar una clasificación

**Ningún libro se elimina.** Las fichas afectadas quedan simplemente sin
clasificación, y la pantalla de confirmación le dice cuántas son. Podrá
asignarles otra con las [operaciones en lote](operations-lot.md).

## Véase también

- [Operaciones en lote](operations-lot.md)
- [Imprimir las etiquetas](../impressions/etiquettes.md)
