/* FEAT-044 — Click handler des boutons `.js-scan-handoff`.
 *
 * Révision Val 2026-05-30 : les boutons « Scanner » du site (dashboard,
 * prêt-carte, prêt-livre, retour, recherche catalogue/membres, champ ISBN)
 * utilisent UNIQUEMENT la caméra du navigateur (modal in-page, décodage
 * 100 % local — cf. scan-camera.js, double moteur html5-qrcode/Quagga). Le
 * handoff OfeliaScan a été retiré de ce flux — OfeliaScan reste réservé au
 * catalogage et au récolement en masse (FEAT-021).
 *
 * Au clic :
 *   - caméra disponible (HTTPS + getUserMedia + module chargé) → modal viseur.
 *   - caméra indisponible (HTTP, permission refusée, pas de caméra, lib KO…)
 *     → message d'erreur explicite à l'écran indiquant la raison exacte et
 *       invitant à saisir le code à la main. PAS de redirection silencieuse.
 *
 * Attributs déclaratifs (hérités de FEAT-023) :
 *   data-scan-target       : sélecteur CSS du <input> à pré-remplir
 *   data-scan-autosubmit   : "true" pour soumettre le form
 *   data-scan-dispatch-url : URL de redirection (?q= ajouté → core:search
 *                            aiguille ensuite vers notice / fiche membre)
 *
 * Helpers exposés via `window.BibliOfelia.scan` (consommés par scan-camera.js).
 */
(function () {
    "use strict";

    function getI18n() {
        var el = document.getElementById("scan-mode-i18n");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function t(key, fallback) {
        var i18n = getI18n();
        return (i18n && i18n[key]) || fallback;
    }

    function setBusy(btn, busy, label) {
        if (busy) {
            if (!btn.dataset.originalLabel) {
                btn.dataset.originalLabel = btn.innerHTML;
            }
            btn.disabled = true;
            btn.classList.add("is-busy");
            if (label) {
                btn.innerHTML = label;
            } else {
                btn.innerHTML = "⏳ " + (btn.dataset.busyLabel || "…");
            }
        } else {
            btn.disabled = false;
            btn.classList.remove("is-busy");
            if (btn.dataset.originalLabel) {
                btn.innerHTML = btn.dataset.originalLabel;
                delete btn.dataset.originalLabel;
            }
        }
    }

    function flashMessage(btn, text, isError) {
        var anchor = btn.parentNode;
        var note = anchor.querySelector(":scope > .scan-handoff-note");
        if (!note) {
            note = document.createElement("div");
            note.className = "scan-handoff-note muted text-sm";
            anchor.appendChild(note);
        }
        note.style.cssText = isError
            ? "margin-top:8px;font-size:13px;color:var(--burgundy);font-weight:600;"
            : "margin-top:8px;font-size:13px;color:var(--grey);";
        note.textContent = text;
        if (note._timer) { clearTimeout(note._timer); note._timer = null; }
        // Les erreurs restent affichées (le bibliothécaire doit lire la raison et
        // savoir qu'il peut saisir à la main) ; les messages neutres s'effacent.
        if (!isError) {
            note._timer = setTimeout(function () {
                if (note && note.parentNode) note.parentNode.removeChild(note);
            }, 6000);
        }
    }

    function applyResult(btn, res) {
        var targetSel = btn.dataset.scanTarget || "";
        var autoSubmit = btn.dataset.scanAutosubmit === "true";
        var dispatchUrl = btn.dataset.scanDispatchUrl || "";

        if (dispatchUrl) {
            var u;
            try { u = new URL(dispatchUrl, window.location.origin); }
            catch (e) { u = null; }
            if (u) {
                u.searchParams.set("q", res.value);
                window.location.href = u.toString();
                return true;
            }
        }
        if (targetSel) {
            var form = btn.closest("form");
            var target = form ? form.querySelector(targetSel) : document.querySelector(targetSel);
            if (target) {
                target.value = res.value;
                target.dispatchEvent(new Event("input", { bubbles: true }));
                if (autoSubmit && form) {
                    if (typeof form.requestSubmit === "function") form.requestSubmit();
                    else form.submit();
                    return true;
                }
            }
        }
        return false;
    }

    function cameraSupportInfo() {
        var info = {
            ok: false,
            isSecureContext: window.isSecureContext === true,
            hasMediaDevices: !!navigator.mediaDevices,
            hasGetUserMedia: !!(navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === "function"),
            hasModule: !!(window.BibliOfelia && window.BibliOfelia.scan && window.BibliOfelia.scan.openCamera),
            protocol: window.location.protocol
        };
        info.ok = info.isSecureContext && info.hasMediaDevices && info.hasGetUserMedia && info.hasModule;
        return info;
    }

    function cameraSupported() {
        return cameraSupportInfo().ok;
    }

    /* Traduit un code de raison technique en message lisible. Les codes
     * proviennent soit de cameraSupportInfo() (contexte pré-ouverture), soit
     * du callback onUnavailable de scan-camera.js (erreurs getUserMedia). */
    function reasonText(code) {
        var map = {
            "insecure-context": t("reason_https", "Accès caméra impossible : la page n’est pas en HTTPS."),
            "no-getusermedia": t("reason_no_getusermedia", "Ce navigateur ne permet pas l’accès à la caméra."),
            "no-module": t("reason_lib", "Le scanner n’a pas pu être chargé."),
            "permission-denied": t("reason_permission", "Permission caméra refusée."),
            "no-camera": t("reason_no_camera", "Aucune caméra détectée sur cet appareil."),
            "camera-busy": t("reason_busy", "La caméra est déjà utilisée par une autre application."),
            "lib-load-failed": t("reason_lib", "Le scanner n’a pas pu être chargé."),
            "lib-not-loaded": t("reason_lib", "Le scanner n’a pas pu être chargé."),
            "start-failed": t("reason_unknown", "Impossible de démarrer la caméra.")
        };
        return map[code] || t("reason_unknown", "Impossible de démarrer la caméra.");
    }

    function supportFailureCode(info) {
        if (!info.isSecureContext) return "insecure-context";
        if (!info.hasMediaDevices || !info.hasGetUserMedia) return "no-getusermedia";
        if (!info.hasModule) return "no-module";
        return "start-failed";
    }

    function showCameraError(btn, code, detail) {
        setBusy(btn, false);
        // Détail technique en console (support) ; message humain à l'écran.
        try { console.warn("[scan] caméra indisponible:", code, detail || ""); } catch (e) { /* noop */ }
        var msg = t("cam_unavailable", "Caméra indisponible") + " — " + reasonText(code)
            + " " + t("cam_manual_hint", "Saisissez le code à la main.");
        flashMessage(btn, msg, true);
    }

    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.scan = window.BibliOfelia.scan || {};
    window.BibliOfelia.scan.applyResult = applyResult;
    window.BibliOfelia.scan.flashMessage = flashMessage;
    window.BibliOfelia.scan.setBusy = setBusy;
    window.BibliOfelia.scan.cameraSupported = cameraSupported;
    window.BibliOfelia.scan.cameraSupportInfo = cameraSupportInfo;

    document.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".js-scan-handoff");
        if (!btn) return;
        if (btn.disabled || btn.classList.contains("is-busy")) {
            ev.preventDefault();
            return;
        }
        ev.preventDefault();

        var info = cameraSupportInfo();
        if (!info.ok) {
            showCameraError(btn, supportFailureCode(info));
            return;
        }

        window.BibliOfelia.scan.openCamera(btn, {
            // FEAT-052 : on n'accepte le préfixe 977 (périodique ISSN) que sur les
            // boutons de RECHERCHE générale (`data-scan-kind="auto"` : dashboard +
            // barre du catalogue), qui routent le code via classify_query → notice.
            // Les boutons prêt/retour (`book`/`card`) et le champ ISBN (`book`)
            // n'acceptent pas le 977 (un magazine s'y scanne via son code Ofelia 290).
            allowIssn: btn.dataset.scanKind === "auto",
            onUnavailable: function (reason, detail) {
                showCameraError(btn, reason, detail);
            }
        });
    });
})();
