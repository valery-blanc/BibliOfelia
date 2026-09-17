/* FEAT-095 — liste déroulante d'emplacements à cases (filtre de recherche).
 *
 * Sans ce script, <details> s'ouvre quand même et les cases partent au GET.
 * Ici : libellé du bouton, « Tous emplacements » exclusif, clic hors du
 * panneau pour refermer.
 */
(function () {
    "use strict";

    function setup(root) {
        var labelEl = root.querySelector("[data-loc-label]");
        var allBox = root.querySelector("[data-loc-all]");
        var boxes = Array.prototype.slice.call(
            root.querySelectorAll('input[name="location"]')
        );
        var allLabel = root.getAttribute("data-all-label") || "";
        if (!labelEl || !allBox) {
            return;
        }

        function checkedBoxes() {
            return boxes.filter(function (box) {
                return box.checked;
            });
        }

        function refreshLabel() {
            var chosen = checkedBoxes();
            if (!chosen.length) {
                labelEl.textContent = allLabel;
                return;
            }
            var codes = chosen.map(function (box) {
                return box.getAttribute("data-loc-code") || box.value;
            });
            if (codes.length <= 3) {
                labelEl.textContent = codes.join(", ");
                return;
            }
            labelEl.textContent = codes.slice(0, 2).join(", ") + " +" + (codes.length - 2);
        }

        allBox.addEventListener("change", function () {
            if (allBox.checked) {
                boxes.forEach(function (box) {
                    box.checked = false;
                });
            }
            refreshLabel();
        });

        boxes.forEach(function (box) {
            box.addEventListener("change", function () {
                if (box.checked) {
                    allBox.checked = false;
                } else if (!checkedBoxes().length) {
                    allBox.checked = true;
                }
                refreshLabel();
            });
        });

        document.addEventListener("click", function (event) {
            if (!root.open) {
                return;
            }
            if (!root.contains(event.target)) {
                root.open = false;
            }
        });

        refreshLabel();
    }

    document.querySelectorAll("[data-location-filter]").forEach(setup);
})();
