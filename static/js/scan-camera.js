/* FEAT-024 — Scanner caméra navigateur (fallback hors OfeliaScan).
 *
 * Activé quand `localStorage['bibliofelia.scan-mode'] === "camera"` et que la
 * page est servie en HTTPS (window.isSecureContext === true). `scan-handoff.js`
 * appelle `BibliOfelia.scan.openCamera(btn)` au lieu de créer un handoff.
 *
 * Décodage 100 % local via html5-qrcode (BarcodeDetector API natif, fallback
 * ZXing-JS embarqué dans la lib). Lazy-load au premier usage pour ne pas
 * charger 375 KB sur chaque page.
 *
 * UX :
 *   - viseur 100 % largeur, overlay sombre, bouton « Annuler ».
 *   - à la première détection : stoppe la caméra, ferme le modal, applique
 *     le résultat via `BibliOfelia.scan.applyResult(btn, {value})`.
 *   - en cas d'erreur (permission, pas de caméra, lib KO) : flashMessage +
 *     restauration du bouton (l'utilisateur peut taper la valeur à la main).
 */
(function () {
    "use strict";

    var LIB_URL = "/static/js/html5-qrcode.min.js";
    var libPromise = null;

    function getI18n() {
        var el = document.getElementById("scan-mode-i18n");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function t(key, fallback) {
        var i18n = getI18n();
        return (i18n && i18n[key]) || fallback;
    }

    function loadLib() {
        if (libPromise) return libPromise;
        libPromise = new Promise(function (resolve, reject) {
            if (window.Html5Qrcode) { resolve(window.Html5Qrcode); return; }
            var s = document.createElement("script");
            s.src = LIB_URL;
            s.async = true;
            s.onload = function () {
                if (window.Html5Qrcode) resolve(window.Html5Qrcode);
                else reject(new Error("html5-qrcode-missing-after-load"));
            };
            s.onerror = function () {
                libPromise = null;
                reject(new Error("html5-qrcode-load-failed"));
            };
            document.head.appendChild(s);
        });
        return libPromise;
    }

    function makeModal() {
        var overlay = document.createElement("div");
        overlay.className = "scan-camera-modal";
        overlay.setAttribute("role", "dialog");
        overlay.setAttribute("aria-modal", "true");
        overlay.setAttribute("aria-label", t("modal_title", "Scanner un code"));
        overlay.innerHTML = ""
            + "<div class='scan-camera-card'>"
            + "  <div class='scan-camera-header'>"
            + "    <span class='scan-camera-title'>" + t("modal_title", "Scanner un code") + "</span>"
            + "    <button type='button' class='scan-camera-close' aria-label='" + t("cancel", "Annuler") + "'>×</button>"
            + "  </div>"
            + "  <div class='scan-camera-viewfinder' id='scan-camera-viewfinder'></div>"
            + "  <div class='scan-camera-hint'>" + t("hint", "Pointez la caméra vers le code-barres.") + "</div>"
            + "  <div class='scan-camera-error' role='alert'></div>"
            + "  <div class='scan-camera-actions'>"
            + "    <button type='button' class='btn btn--ghost scan-camera-cancel'>" + t("cancel", "Annuler") + "</button>"
            + "  </div>"
            + "</div>";
        return overlay;
    }

    function closeModal(state) {
        if (!state || state.closed) return Promise.resolve();
        state.closed = true;
        document.body.classList.remove("scan-camera-open");
        var p = Promise.resolve();
        if (state.scanner && state.scannerActive) {
            try {
                p = state.scanner.stop().catch(function () { /* tolérant */ });
            } catch (e) { /* idem */ }
        }
        return p.finally(function () {
            try {
                if (state.scanner && typeof state.scanner.clear === "function") {
                    state.scanner.clear();
                }
            } catch (e) { /* idem */ }
            if (state.overlay && state.overlay.parentNode) {
                state.overlay.parentNode.removeChild(state.overlay);
            }
            document.removeEventListener("keydown", state.onKey);
        });
    }

    function showError(state, message) {
        var err = state.overlay.querySelector(".scan-camera-error");
        if (err) err.textContent = message;
    }

    function startScanner(state, btn) {
        var Html5Qrcode = window.Html5Qrcode;
        if (!Html5Qrcode) {
            showError(state, t("lib_error", "Impossible de charger le scanner."));
            return;
        }
        var formats;
        if (window.Html5QrcodeSupportedFormats) {
            var F = window.Html5QrcodeSupportedFormats;
            formats = [
                F.EAN_13, F.EAN_8, F.UPC_A, F.UPC_E,
                F.CODE_39, F.CODE_128, F.ITF, F.QR_CODE
            ];
        }
        var scanner = new Html5Qrcode("scan-camera-viewfinder", { verbose: false });
        state.scanner = scanner;
        var config = {
            fps: 10,
            qrbox: function (vw, vh) {
                var edge = Math.floor(Math.min(vw, vh) * 0.8);
                return { width: edge, height: Math.floor(edge * 0.6) };
            },
            aspectRatio: 1.5,
            formatsToSupport: formats,
            disableFlip: false
        };
        scanner.start(
            { facingMode: { ideal: "environment" } },
            config,
            function onScan(decodedText) {
                if (state.consumed) return;
                state.consumed = true;
                closeModal(state).then(function () {
                    window.BibliOfelia.scan.setBusy(btn, false);
                    var consumed = window.BibliOfelia.scan.applyResult(btn, { value: decodedText });
                    if (!consumed) {
                        window.BibliOfelia.scan.flashMessage(btn, t("scanned", "Valeur scannée :") + " " + decodedText);
                    }
                });
            },
            function onScanFailure(/* err */) { /* ignoré (tentatives ratées normales) */ }
        ).then(function () {
            state.scannerActive = true;
        }).catch(function (err) {
            console.error("[scan-camera] start failed", err);
            var msg = t("camera_error", "Impossible d’accéder à la caméra.");
            if (err && err.name === "NotAllowedError") {
                msg = t("permission_denied", "Permission caméra refusée.");
            } else if (err && err.name === "NotFoundError") {
                msg = t("no_camera", "Aucune caméra détectée sur cet appareil.");
            }
            showError(state, msg);
        });
    }

    function openCamera(btn) {
        if (!window.isSecureContext || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            window.BibliOfelia.scan.flashMessage(btn,
                t("needs_https", "Le scanner caméra nécessite HTTPS. Connectez-vous via internet."));
            return;
        }

        window.BibliOfelia.scan.setBusy(btn, true,
            "⏳ " + t("opening", "Ouverture de la caméra…"));

        var state = {
            overlay: makeModal(),
            scanner: null,
            scannerActive: false,
            consumed: false,
            closed: false
        };
        state.onKey = function (ev) { if (ev.key === "Escape") closeModal(state).then(function () {
            window.BibliOfelia.scan.setBusy(btn, false);
        }); };

        document.body.appendChild(state.overlay);
        document.body.classList.add("scan-camera-open");
        document.addEventListener("keydown", state.onKey);

        function cancel() {
            closeModal(state).then(function () {
                window.BibliOfelia.scan.setBusy(btn, false);
            });
        }
        state.overlay.querySelector(".scan-camera-close").addEventListener("click", cancel);
        state.overlay.querySelector(".scan-camera-cancel").addEventListener("click", cancel);
        state.overlay.addEventListener("click", function (ev) {
            if (ev.target === state.overlay) cancel();
        });

        loadLib().then(function () { startScanner(state, btn); })
            .catch(function (err) {
                console.error("[scan-camera] lib load", err);
                showError(state, t("lib_error", "Impossible de charger le scanner."));
            });
    }

    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.scan = window.BibliOfelia.scan || {};
    window.BibliOfelia.scan.openCamera = openCamera;
})();
