/* Liste d'usagers : la frappe réduit les noms affichés. Le select reste
   le champ envoyé, donc le formulaire fonctionne aussi sans ce script. */
(function () {
  var root = document.querySelector("[data-member-picker]");
  if (!root) return;
  var input = root.querySelector("[data-member-filter]");
  var select = root.querySelector("select");
  if (!input || !select) return;

  var options = Array.prototype.slice.call(select.options);

  function fold(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function matches(text, query) {
    var hay = fold(text);
    var parts = fold(query).split(/\s+/).filter(Boolean);
    if (!parts.length) return true;
    for (var i = 0; i < parts.length; i++) {
      if (hay.indexOf(parts[i]) === -1) return false;
    }
    return true;
  }

  function apply() {
    var query = input.value;
    var selected = select.value;
    var searching = fold(query).length > 0;
    var fragment = document.createDocumentFragment();
    for (var i = 0; i < options.length; i++) {
      var option = options[i];
      var keep = option.value
        ? option.value === selected || matches(option.text, query)
        : !searching;
      if (keep) fragment.appendChild(option);
    }
    while (select.firstChild) select.removeChild(select.firstChild);
    select.appendChild(fragment);
    if (selected) select.value = selected;
  }

  input.addEventListener("input", apply);
  input.addEventListener("keydown", function (event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      select.focus();
      return;
    }
    if (event.key !== "Enter") return;
    event.preventDefault();
    var matching = [];
    for (var i = 0; i < options.length; i++) {
      var option = options[i];
      if (option.value && matches(option.text, input.value)) matching.push(option);
    }
    if (matching.length === 1) {
      select.value = matching[0].value;
      apply();
    }
  });
})();
