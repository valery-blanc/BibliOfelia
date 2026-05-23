/* FEAT-024 — Toggle de mode de scan (OfeliaScan / Caméra navigateur).
 *
 * Injecte un chevron à côté de chaque `.js-scan-handoff` (et un overlay
 * en coin du `.scan-banner` du dashboard). Au clic : popover listant les 2
 * modes, persistance du choix dans `localStorage['bibliofelia.scan-mode']`.
 *
 * L'option « Caméra » est désactivée si `window.isSecureContext === false`
 * (getUserMedia exige HTTPS).
 */
(function () {
    "use strict";

    var STORAGE_KEY = "bibliofelia.scan-mode";

    function getI18n() {
        var el = document.getElementById("scan-mode-i18n");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function t(key, fallback) {
        var i18n = getI18n();
        return (i18n && i18n[key]) || fallback;
    }

    function readMode() {
        try {
            var v = window.localStorage && window.localStorage.getItem(STORAGE_KEY);
            return v === "camera" ? "camera" : "ofeliascan";
        } catch (e) {
            return "ofeliascan";
        }
    }

    function writeMode(mode) {
        try {
            if (window.localStorage) window.localStorage.setItem(STORAGE_KEY, mode);
        } catch (e) { /* mode privé Safari, etc. */ }
        document.documentElement.setAttribute("data-scan-mode", mode);
        document.dispatchEvent(new CustomEvent("bibliofelia:scan-mode-changed", { detail: { mode: mode } }));
    }

    function closeAllPopovers(except) {
        var popovers = document.querySelectorAll(".scan-mode-popover.is-open");
        popovers.forEach(function (p) {
            if (p !== except) p.classList.remove("is-open");
        });
    }

    function makePopover(toggleBtn) {
        var pop = document.createElement("div");
        pop.className = "scan-mode-popover";
        pop.setAttribute("role", "menu");
        var secure = window.isSecureContext === true;
        var current = readMode();
        var camDisabled = secure ? "" : " is-disabled";
        var camTooltip = secure ? "" : " title='" + t("needs_https", "Nécessite HTTPS — accédez via internet.") + "'";

        pop.innerHTML = ""
            + "<button type='button' role='menuitemradio' class='scan-mode-option" + (current === "ofeliascan" ? " is-active" : "") + "' data-mode='ofeliascan'>"
            + "  <span class='scan-mode-bullet'>" + (current === "ofeliascan" ? "●" : "○") + "</span>"
            + "  <span class='scan-mode-label'>" + t("mode_ofeliascan", "Application OfeliaScan") + "</span>"
            + "</button>"
            + "<button type='button' role='menuitemradio' class='scan-mode-option" + (current === "camera" ? " is-active" : "") + camDisabled + "' data-mode='camera'" + camTooltip + (secure ? "" : " aria-disabled='true'") + ">"
            + "  <span class='scan-mode-bullet'>" + (current === "camera" ? "●" : "○") + "</span>"
            + "  <span class='scan-mode-label'>" + t("mode_camera", "Caméra de l’appareil") + "</span>"
            + (secure ? "" : "  <span class='scan-mode-hint'>" + t("needs_https_short", "HTTPS requis") + "</span>")
            + "</button>";

        pop.addEventListener("click", function (ev) {
            var opt = ev.target.closest(".scan-mode-option");
            if (!opt) return;
            if (opt.classList.contains("is-disabled")) {
                ev.stopPropagation();
                return;
            }
            var mode = opt.dataset.mode;
            writeMode(mode);
            closeAllPopovers();
            // refresh other popovers' state at next open ; ce popover sera détruit.
        });

        return pop;
    }

    function attachToggle(btn) {
        // Évite la double injection.
        if (btn.dataset.scanModeToggleAttached === "1") return;
        btn.dataset.scanModeToggleAttached = "1";

        // Wrap le bouton dans un .scan-split si pas déjà fait.
        var wrap = btn.closest(".scan-split");
        var bannerMode = btn.classList.contains("scan-banner");
        if (!wrap && !bannerMode) {
            wrap = document.createElement("div");
            wrap.className = "scan-split";
            if (btn.classList.contains("btn--block")) {
                wrap.classList.add("scan-split--block");
            }
            btn.parentNode.insertBefore(wrap, btn);
            wrap.appendChild(btn);
        }
        var host = bannerMode ? btn : wrap;
        if (bannerMode) host.classList.add("scan-banner--with-toggle");

        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "scan-mode-toggle";
        toggle.setAttribute("aria-label", t("toggle_label", "Choisir le mode de scan"));
        toggle.setAttribute("aria-haspopup", "menu");
        toggle.setAttribute("aria-expanded", "false");
        toggle.innerHTML = "<span class='scan-mode-toggle-caret' aria-hidden='true'>▾</span>";

        // Empêche le clic sur le chevron de remonter au bouton parent (scan-banner = <a>).
        toggle.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var alreadyOpen = host.querySelector(".scan-mode-popover.is-open");
            closeAllPopovers();
            if (alreadyOpen) {
                toggle.setAttribute("aria-expanded", "false");
                return;
            }
            var pop = makePopover(toggle);
            host.appendChild(pop);
            requestAnimationFrame(function () { pop.classList.add("is-open"); });
            toggle.setAttribute("aria-expanded", "true");

            // Ferme au clic externe ; à poser une fois la popover effectivement
            // posée pour éviter l'auto-close immédiat.
            setTimeout(function () {
                document.addEventListener("click", function onDoc(e) {
                    if (!pop.contains(e.target) && e.target !== toggle) {
                        pop.classList.remove("is-open");
                        toggle.setAttribute("aria-expanded", "false");
                        if (pop.parentNode) pop.parentNode.removeChild(pop);
                        document.removeEventListener("click", onDoc);
                    }
                });
            }, 0);
        });

        host.appendChild(toggle);
    }

    function init() {
        // Initialise l'attribut html pour permettre des hooks CSS éventuels.
        document.documentElement.setAttribute("data-scan-mode", readMode());

        var btns = document.querySelectorAll(".js-scan-handoff");
        btns.forEach(attachToggle);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
