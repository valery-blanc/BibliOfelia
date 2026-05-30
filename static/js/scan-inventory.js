/* FEAT-045 — Contrôleur de la page de rapport de récolement.
 *
 * Câble le bouton `.js-scan-inventory` au scanner caméra en mode continu
 * (cf. scan-camera.js). Chaque code Ofelia confirmé est posté à l'endpoint
 * `inventory:add_scan` (JSON) ; le compteur live et la liste des derniers scans
 * sont mis à jour côté client. Un champ de saisie manuelle (repli hors caméra,
 * utile en LAN HTTP) poste vers le même endpoint. À la fermeture du viseur, la
 * page se recharge pour rafraîchir les tableaux de divergences.
 *
 * Config injectée dans `#scan-inventory-config` : {scanUrl, csrfToken, i18n}.
 */
(function () {
    "use strict";

    function readConfig() {
        var el = document.getElementById("scan-inventory-config");
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (e) { return null; }
    }
    var CFG = readConfig();
    if (!CFG) return;

    function t(key, fallback) {
        return (CFG.i18n && CFG.i18n[key]) || fallback;
    }

    var counterEl = document.getElementById("inv-scan-count");
    var expectedEl = document.getElementById("inv-scan-expected");
    var liveList = document.getElementById("inv-scan-live");

    // Dé-duplication : un code déjà pointé (dans cette session, y compris avant
    // un « Continuer l'inventaire ») est ignoré en silence — pas de bip, pas de
    // ligne, pas de doublon. Pré-rempli avec les codes déjà en base.
    function readSeen() {
        var el = document.getElementById("inv-scanned-eans");
        if (!el) return new Set();
        try { return new Set(JSON.parse(el.textContent) || []); } catch (e) { return new Set(); }
    }
    var seen = readSeen();

    function updateCounts(c) {
        if (!c) return;
        if (counterEl) counterEl.textContent = c.scanned;
        if (expectedEl) expectedEl.textContent = c.expected;
    }

    // « Titre — Auteur · exemplaire N » d'un exemplaire trouvé (sans location).
    function foundLabel(item, ean) {
        var s = (item && item.title) || ean;
        if (item && item.author) s += " — " + item.author;
        if (item && item.copy_index) s += " · " + t("copy", "exemplaire") + " " + item.copy_index;
        return s;
    }

    function renderRow(data) {
        var line = document.createElement("div");
        var label, cls;
        if (!data.known) {
            cls = "is-unknown";
            label = t("unknown", "Inconnu du catalogue") + " — " + data.ean;
        } else if (!data.created) {
            cls = "is-dup";
            label = t("already", "Déjà pointé") + " — " + ((data.item && data.item.title) || data.ean);
        } else {
            cls = "is-ok";
            label = foundLabel(data.item, data.ean)
                + (data.item && data.item.location_code ? " · " + data.item.location_code : "");
        }
        line.className = "inv-scan-row " + cls;
        line.textContent = label;
        if (liveList) {
            liveList.insertBefore(line, liveList.firstChild);
            // Borne la liste pour ne pas gonfler le DOM sur de longues sessions.
            while (liveList.children.length > 30) liveList.removeChild(liveList.lastChild);
        }
        updateCounts(data.counts);
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

    function handleCode(ean) {
        ean = (ean || "").trim();
        if (!ean || seen.has(ean)) return Promise.resolve();  // doublon → ignoré
        // Ajout optimiste : bloque les re-déclenchements pendant que le POST
        // est en vol. Annulé si le POST échoue (réseau / erreur applicative).
        seen.add(ean);
        return postScan(ean).then(function (res) {
            var d = res.data;
            if (!(d && d.ok)) { seen.delete(ean); return res; }
            renderRow(d);
            if (d.known && d.created) {
                var S = window.BibliOfelia && window.BibliOfelia.scan;
                if (S && S.continuousFeedback) {
                    S.continuousFeedback({
                        count: d.counts && d.counts.scanned,
                        label: foundLabel(d.item, ean)
                    });
                }
            }
            return res;
        }).catch(function () { seen.delete(ean); /* réseau : on réautorise */ });
    }

    var manualForm = document.getElementById("inv-manual-form");
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
        var btn = ev.target.closest(".js-scan-inventory");
        if (!btn) return;
        ev.preventDefault();
        var S = window.BibliOfelia && window.BibliOfelia.scan;
        if (!S || !S.openCamera) return;

        var info = S.cameraSupportInfo ? S.cameraSupportInfo() : { ok: true };
        if (!info.ok) {
            S.flashMessage(btn,
                t("cam_unavailable", "Caméra indisponible") + " — " + t("cam_manual_hint", "Saisissez le code à la main."),
                true);
            return;
        }
        S.openCamera(btn, {
            continuous: true,
            onCode: handleCode,
            onClose: function () { window.location.reload(); },
            onUnavailable: function () {
                S.flashMessage(btn,
                    t("cam_unavailable", "Caméra indisponible") + " — " + t("cam_manual_hint", "Saisissez le code à la main."),
                    true);
            }
        });
    });
})();
