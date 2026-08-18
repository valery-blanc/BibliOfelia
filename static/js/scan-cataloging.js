/* FEAT-046 — Contrôleur de la page de lot de catalogage.
 *
 * Câble `.js-scan-cataloging` au scanner caméra continu (scan-camera.js).
 * Chaque ISBN confirmé est posté à `catalog:scan_add` ; c'est le SERVEUR qui
 * décide created / incremented / ignored / rejected (règle des 3 s — pas de set
 * `seen` côté client, contrairement au récolement). Un même livre re-présenté
 * après > 3 s crée un exemplaire supplémentaire : on affiche « exemplaire X » en
 * gros dans le viseur. À la fermeture, la page se recharge pour afficher le
 * tableau éditable des titres détectés.
 *
 * Config injectée dans `#scan-cataloging-config` : {scanUrl, csrfToken, i18n}.
 */
(function () {
    "use strict";

    function readConfig() {
        var el = document.getElementById("scan-cataloging-config");
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (e) { return null; }
    }
    var CFG = readConfig();
    if (!CFG) return;

    function t(key, fallback) {
        return (CFG.i18n && CFG.i18n[key]) || fallback;
    }

    var countEl = document.getElementById("cat-scan-count");
    var liveList = document.getElementById("cat-scan-live");

    function setCount(n) {
        if (countEl && typeof n !== "undefined" && n !== null) countEl.textContent = n;
    }

    // « exemplaire X » en gros : on accentue #scan-camera-last sur un 2ᵉ+ exemplaire.
    function emphasizeLast(isCopy) {
        var el = document.getElementById("scan-camera-last");
        if (!el) return;
        if (isCopy) el.classList.add("scan-camera-last--copy");
        else el.classList.remove("scan-camera-last--copy");
    }

    function renderRow(d) {
        if (!liveList) return;
        var line = document.createElement("div");
        var cls, label;
        if (d.action === "rejected") {
            cls = "is-unknown";
            label = (d.label || t("rejected", "Code refusé")) + " — " + d.isbn;
        } else if (d.action === "ignored") {
            return; // double-lecture d'un livre tenu en vue : silencieux
        } else if (d.action === "incremented") {
            cls = "is-ok";
            label = (d.title || (t("isbn", "ISBN") + " " + d.isbn))
                + " · " + t("copy", "exemplaire") + " " + d.copy_count;
        } else {
            cls = "is-ok";
            label = d.label || d.title || (t("isbn", "ISBN") + " " + d.isbn);
        }
        line.className = "inv-scan-row " + cls;
        line.textContent = label;
        liveList.insertBefore(line, liveList.firstChild);
        while (liveList.children.length > 30) liveList.removeChild(liveList.lastChild);
    }

    function feedback(d) {
        var S = window.BibliOfelia && window.BibliOfelia.scan;
        if (!S || !S.continuousFeedback) return;
        if (d.action === "created") {
            emphasizeLast(false);
            S.continuousFeedback({ count: d.count, label: d.label });
        } else if (d.action === "incremented") {
            emphasizeLast(true);
            S.continuousFeedback({
                count: d.count,
                label: t("copy", "exemplaire") + " " + d.copy_count
            });
        }
        // ignored / rejected : pas de bip ni de vibration
    }

    function postScan(ean) {
        return fetch(CFG.scanUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": CFG.csrfToken,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: "ean=" + encodeURIComponent(ean)
        }).then(function (r) {
            return r.json().then(function (d) { return { status: r.status, data: d }; });
        });
    }

    // Garde anti double-POST : un même code ne repart pas tant que sa requête
    // précédente est en vol (la caméra ré-émet le code ~0,6 s en continu). Le
    // serveur reste de toute façon idempotent (réconciliation), c'est une
    // optimisation pour éviter les requêtes redondantes.
    // BUG-024 : en mode douchette la page ne se recharge jamais, donc le tableau
    // rendu par le serveur devient périmé dès qu'un scan aboutit. Le bouton
    // « Terminer et voir le lot » n'est utile qu'à ce moment-là.
    function revealRefresh(d) {
        if (d.action !== "created" && d.action !== "incremented") return;
        var wrap = document.getElementById("cat-refresh-wrap");
        if (wrap) wrap.removeAttribute("hidden");
    }

    var inFlight = Object.create(null);

    function handleCode(ean) {
        ean = (ean || "").trim();
        if (!ean) return Promise.resolve();
        if (inFlight[ean]) return Promise.resolve();
        inFlight[ean] = true;
        return postScan(ean).then(function (res) {
            var d = res.data;
            if (!(d && d.ok)) return res;
            renderRow(d);
            feedback(d);
            setCount(d.count);
            revealRefresh(d);
            return res;
        }).catch(function () { /* réseau : on ignore, le scan reprend */ })
          .finally(function () { delete inFlight[ean]; });
    }

    var manualForm = document.getElementById("cat-manual-form");
    if (manualForm) {
        manualForm.addEventListener("submit", function (ev) {
            ev.preventDefault();
            var inp = manualForm.querySelector("input[name='ean']");
            var v = inp ? (inp.value || "").trim() : "";
            if (!v) return;
            handleCode(v);
            inp.value = "";
            inp.focus();
        });
    }

    document.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".js-scan-cataloging");
        if (!btn) return;
        ev.preventDefault();
        var S = window.BibliOfelia && window.BibliOfelia.scan;
        if (!S || !S.openCamera) return;
        S.openCamera(btn, {
            continuous: true,
            allowIssn: true,  // FEAT-052 : périodiques (préfixe 977) en catalogage
            onCode: handleCode,
            onClose: function () { window.location.reload(); },
            onUnavailable: function () {
                if (S.flashMessage) {
                    S.flashMessage(btn,
                        t("cam_unavailable", "Caméra indisponible") + " — "
                        + t("cam_manual_hint", "Saisissez l’ISBN à la main."),
                        true);
                }
            }
        });
    });
})();
