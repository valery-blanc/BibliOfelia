/* FEAT-088 — moteur de recherche de devise.
 *
 * Val (2026-09-01) : « plutôt qu'une liste déroulante, fais un moteur de
 * recherche… Le moteur attend la 2ᵉ lettre. On pourra donc taper soit une
 * partie ou tout le trigramme, soit une partie ou tout le nom du pays. »
 *
 * Progressive enhancement : le champ est un `<input type="text"` ordinaire qui
 * part au serveur tel quel. Ce script ne fait qu'ajouter la liste de
 * suggestions. Sans lui, on tape « CHF » et le réglage marche toujours.
 *
 * Pas de dépendance : contrainte hors-ligne du projet.
 */
(function () {
    "use strict";

    var DEBOUNCE_MS = 180;

    function debounce(fn, wait) {
        var timer = null;
        return function () {
            var args = arguments, self = this;
            if (timer) { clearTimeout(timer); }
            timer = setTimeout(function () { fn.apply(self, args); }, wait);
        };
    }

    function setup(root) {
        var input = root.querySelector("[data-currency-input]");
        var list = root.querySelector("[data-currency-results]");
        var current = root.querySelector("[data-currency-current]");
        if (!input || !list) { return; }

        var url = root.dataset.url;
        var minLength = parseInt(root.dataset.minLength, 10) || 2;
        var items = [];
        var active = -1;
        // Le serveur répond dans le désordre quand on tape vite : on ignore
        // toute réponse plus ancienne que la dernière requête émise.
        var lastRequest = 0;

        function close() {
            list.hidden = true;
            list.innerHTML = "";
            input.setAttribute("aria-expanded", "false");
            items = [];
            active = -1;
        }

        function choose(item) {
            // On écrit le CODE, pas le libellé : c'est ce champ qui part au
            // serveur, et un libellé traduit y arriverait dans la langue de
            // l'écran.
            input.value = item.code;
            if (current) {
                current.textContent = item.code + " — " + item.name +
                    (item.countries ? " (" + item.countries + ")" : "");
            }
            close();
            input.focus();
        }

        function highlight(index) {
            var rows = list.querySelectorAll(".currency-result");
            for (var i = 0; i < rows.length; i++) {
                rows[i].classList.toggle("is-active", i === index);
                if (i === index) {
                    rows[i].setAttribute("aria-selected", "true");
                    rows[i].scrollIntoView({ block: "nearest" });
                } else {
                    rows[i].removeAttribute("aria-selected");
                }
            }
            active = index;
        }

        function render(results) {
            items = results || [];
            list.innerHTML = "";
            if (!items.length) {
                close();
                return;
            }
            items.forEach(function (item, index) {
                var row = document.createElement("button");
                row.type = "button";           // jamais un submit dans un form
                row.className = "currency-result";
                row.setAttribute("role", "option");
                row.innerHTML =
                    '<span class="currency-code"></span>' +
                    '<span class="currency-name"></span>' +
                    '<span class="currency-countries"></span>';
                row.querySelector(".currency-code").textContent = item.code;
                row.querySelector(".currency-name").textContent = item.name;
                row.querySelector(".currency-countries").textContent = item.countries;
                row.addEventListener("mousedown", function (event) {
                    // mousedown, pas click : le blur de l'input fermerait la
                    // liste avant que le click ne parte.
                    event.preventDefault();
                    choose(item);
                });
                row.addEventListener("mouseenter", function () { highlight(index); });
                list.appendChild(row);
            });
            list.hidden = false;
            input.setAttribute("aria-expanded", "true");
            highlight(-1);
        }

        function fetchResults(query) {
            var token = ++lastRequest;
            fetch(url + "?q=" + encodeURIComponent(query), {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                credentials: "same-origin"
            })
                .then(function (response) {
                    if (!response.ok) { throw new Error(response.status); }
                    return response.json();
                })
                .then(function (data) {
                    if (token !== lastRequest) { return; }
                    render(data.results);
                })
                .catch(function () {
                    // Recherche indisponible : on ferme la liste et on laisse
                    // la saisie manuelle faire son travail.
                    if (token === lastRequest) { close(); }
                });
        }

        var search = debounce(function () {
            var query = input.value.trim();
            if (query.length < minLength) {
                close();
                return;
            }
            fetchResults(query);
        }, DEBOUNCE_MS);

        input.addEventListener("input", search);
        input.addEventListener("focus", function () {
            if (input.value.trim().length >= minLength) { search(); }
        });
        input.addEventListener("blur", function () {
            setTimeout(close, 120);
        });
        input.addEventListener("keydown", function (event) {
            if (list.hidden || !items.length) {
                return;
            }
            if (event.key === "ArrowDown") {
                event.preventDefault();
                highlight(active + 1 >= items.length ? 0 : active + 1);
            } else if (event.key === "ArrowUp") {
                event.preventDefault();
                highlight(active - 1 < 0 ? items.length - 1 : active - 1);
            } else if (event.key === "Enter") {
                if (active >= 0) {
                    // Enter valide la suggestion, il ne soumet pas le
                    // formulaire : sinon un choix au clavier enregistrerait le
                    // réglage sans que l'utilisateur ait vu ce qu'il a pris.
                    event.preventDefault();
                    choose(items[active]);
                }
            } else if (event.key === "Escape") {
                close();
            }
        });
    }

    function init() {
        var roots = document.querySelectorAll("[data-currency-search]");
        for (var i = 0; i < roots.length; i++) { setup(roots[i]); }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
