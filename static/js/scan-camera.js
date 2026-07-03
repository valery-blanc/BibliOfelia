/* FEAT-044 — Scanner caméra navigateur (mode unique des boutons du site).
 *
 * Appelé par scan-handoff.js : `BibliOfelia.scan.openCamera(btn, opts)` où
 * `opts.onUnavailable(reason, detail)` est invoqué si la caméra ne peut pas
 * démarrer (lib KO, permission refusée, pas de caméra). Le caller affiche alors
 * un message d'erreur explicite (plus de fallback OfeliaScan sur le site).
 *
 * Mode continu (FEAT-045, récolement/catalogage) : `opts.continuous=true` +
 * `opts.onCode(value)`. Le viseur reste ouvert ; chaque code confirmé déclenche
 * un bip + un compteur live + `onCode`, puis le scan reprend après un cooldown.
 * `opts.onClose()` est appelé à la fermeture manuelle (« Terminer »).
 *
 * Double moteur de décodage, choisi selon les capacités du navigateur :
 *   - `BarcodeDetector` natif dispo (Chrome/Edge Android, Chrome desktop)
 *     → html5-qrcode avec useBarCodeDetectorIfSupported (quasi natif, rapide).
 *   - sinon (Safari iOS, Firefox Android) → QuaggaJS, lib spécialisée 1D/EAN,
 *     plus robuste que le repli ZXing-JS d'html5-qrcode en conditions difficiles.
 *
 * Décodage 100 % local, EAN-13 uniquement, aucune image envoyée au serveur.
 */
(function () {
    "use strict";

    // Les URLs des libs doivent respecter le préfixe de déploiement (prod sert
    // sous `/bibliofelia/static/…`) ET le hash de ManifestStaticFilesStorage.
    // On les lit depuis le template (`{% static %}` résout préfixe + hash) ;
    // fallbacks défensifs (dérivation depuis l'URL de ce script, puis chemin nu).
    function getCameraConfig() {
        var el = document.getElementById("scan-camera-config");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }
    var CAMERA_CONFIG = getCameraConfig();
    var SELF_SRC = (document.currentScript && document.currentScript.src) || "";
    function siblingUrl(name, configured) {
        return configured
            || (SELF_SRC ? SELF_SRC.replace(/scan-camera(\.[0-9a-f]+)?\.js(\?.*)?$/, name) : "")
            || ("/static/js/" + name);
    }
    var LIB_URL = siblingUrl("html5-qrcode.min.js", CAMERA_CONFIG.libUrl);
    var QUAGGA_URL = siblingUrl("quagga.min.js", CAMERA_CONFIG.quaggaUrl);

    // Validation clé de contrôle EAN-13 : rejette les lectures corrompues
    // (confusion 1↔7 / 1↔0 du décodeur logiciel) avant de les accepter.
    function isValidEan13(code) {
        if (!/^\d{13}$/.test(code)) return false;
        var sum = 0;
        for (var i = 0; i < 12; i++) {
            sum += (i % 2 === 0 ? 1 : 3) * (code.charCodeAt(i) - 48);
        }
        var check = (10 - (sum % 10)) % 10;
        return check === (code.charCodeAt(12) - 48);
    }

    // Un code n'est accepté QUE si c'est un EAN-13 à clé valide ET préfixe
    // plausible : 290/291 = codes Ofelia (exemplaire / carte membre),
    // 978/979 = ISBN. Tout le reste (autre format/préfixe, clé KO) est rejeté.
    // FEAT-052 : `allowIssn` (catalogage uniquement) ajoute le préfixe 977
    // (périodiques). Les flux prêt/retour/adhésion gardent le filtre par défaut.
    function isAcceptableCode(v, allowIssn) {
        if (!/^\d{13}$/.test(v) || !isValidEan13(v)) return false;
        var prefixes = allowIssn ? /^(290|291|977|978|979)/ : /^(290|291|978|979)/;
        return prefixes.test(v);
    }

    function getI18n() {
        var el = document.getElementById("scan-mode-i18n");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }

    function t(key, fallback) {
        var i18n = getI18n();
        return (i18n && i18n[key]) || fallback;
    }

    // Chargeur de script générique (lazy-load, mis en cache par promesse).
    function makeLoader(url, globalName, tag) {
        var promise = null;
        return function load() {
            if (promise) return promise;
            promise = new Promise(function (resolve, reject) {
                if (window[globalName]) { resolve(window[globalName]); return; }
                var s = document.createElement("script");
                s.src = url;
                s.async = true;
                s.onload = function () {
                    if (window[globalName]) resolve(window[globalName]);
                    else reject(new Error(tag + "-missing-after-load"));
                };
                s.onerror = function () { promise = null; reject(new Error(tag + "-load-failed")); };
                document.head.appendChild(s);
            });
            return promise;
        };
    }
    var loadLib = makeLoader(LIB_URL, "Html5Qrcode", "html5-qrcode");
    var loadQuagga = makeLoader(QUAGGA_URL, "Quagga", "quagga");

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
            + "  <div class='scan-camera-count' id='scan-camera-count' hidden></div>"
            + "  <div class='scan-camera-last' id='scan-camera-last' hidden></div>"
            + "  <div class='scan-camera-actions'>"
            + "    <button type='button' class='btn btn--ghost scan-camera-cancel'>" + t("cancel", "Annuler") + "</button>"
            + "  </div>"
            + "</div>";
        return overlay;
    }

    // Bip de confirmation (WebAudio) — mode continu. Tolérant (no-op si bloqué).
    function playBeep() {
        try {
            var Ctx = window.AudioContext || window.webkitAudioContext;
            if (!Ctx) return;
            var ctx = playBeep._ctx || (playBeep._ctx = new Ctx());
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = 880;
            gain.gain.value = 0.06;
            osc.start();
            setTimeout(function () { try { osc.stop(); } catch (e) { /* noop */ } }, 110);
        } catch (e) { /* noop */ }
    }

    function vibrate(ms) {
        try { if (navigator.vibrate) navigator.vibrate(ms || 120); } catch (e) { /* noop */ }
    }

    // Feedback d'une nouvelle trouvaille en mode continu — piloté par le
    // contrôleur de page (qui connaît la dé-duplication et les métadonnées).
    // opts : {count, label}. Bip + vibration + compteur + dernier livre trouvé.
    function continuousFeedback(opts) {
        opts = opts || {};
        playBeep();
        vibrate(120);
        var countEl = document.getElementById("scan-camera-count");
        if (countEl && typeof opts.count !== "undefined" && opts.count !== null) {
            countEl.hidden = false;
            countEl.textContent = t("scanned_count", "Scannés :") + " " + opts.count;
        }
        var lastEl = document.getElementById("scan-camera-last");
        if (lastEl && opts.label) {
            lastEl.hidden = false;
            lastEl.textContent = opts.label;
        }
    }

    // Quagga injecte un <video> + un <canvas.drawingBuffer> dans le viseur :
    // on s'assure qu'ils remplissent la zone (CSS injecté une seule fois).
    function ensureViewfinderCss() {
        if (document.getElementById("scan-engine-css")) return;
        var s = document.createElement("style");
        s.id = "scan-engine-css";
        s.textContent = "#scan-camera-viewfinder{position:relative;overflow:hidden}"
            + "#scan-camera-viewfinder video,#scan-camera-viewfinder canvas{width:100%;height:100%;object-fit:cover;display:block}"
            + "#scan-camera-viewfinder canvas.drawingBuffer{position:absolute;top:0;left:0}";
        document.head.appendChild(s);
    }

    function closeModal(state) {
        if (!state || state.closed) return Promise.resolve();
        state.closed = true;
        document.body.classList.remove("scan-camera-open");
        var p = Promise.resolve();
        if (state.stopEngine) {
            try { p = Promise.resolve(state.stopEngine()); } catch (e) { /* tolérant */ }
        }
        return p.catch(function () {}).then(function () {
            if (state.overlay && state.overlay.parentNode) {
                state.overlay.parentNode.removeChild(state.overlay);
            }
            document.removeEventListener("keydown", state.onKey);
        });
    }

    function classifyMediaError(err) {
        var name = err && err.name ? err.name : "";
        var reason = "start-failed";
        if (name === "NotAllowedError" || name === "SecurityError") reason = "permission-denied";
        else if (name === "NotFoundError" || name === "OverconstrainedError") reason = "no-camera";
        else if (name === "NotReadableError" || name === "AbortError") reason = "camera-busy";
        var detail;
        if (typeof err === "string") detail = err;
        else if (name || (err && err.message)) detail = name + (err && err.message ? ": " + err.message : "");
        else { try { detail = JSON.stringify(err); } catch (e) { detail = String(err); } }
        return { reason: reason, detail: detail };
    }

    // Cooldown entre 2 codes acceptés en mode continu : évite qu'un même livre
    // tenu en vue ne re-déclenche en boucle (le serveur reste idempotent, mais
    // ça lisse le feedback). ~1,8 s.
    var CONTINUOUS_COOLDOWN_MS = 800;

    // Garde-fous communs aux deux moteurs : checksum + préfixe, puis consensus
    // (2 lectures identiques d'affilée). Retourne true si la valeur est confirmée.
    function handleRead(state, v) {
        if (state.consumed) return false;
        if (state.continuous && Date.now() < (state.cooldownUntil || 0)) return false;
        v = (v || "").trim();
        if (!isAcceptableCode(v, state.allowIssn)) return false;
        if (state.lastRead === v) {
            state.readStreak = (state.readStreak || 1) + 1;
        } else {
            state.lastRead = v;
            state.readStreak = 1;
        }
        if (state.readStreak < 2) return false;
        if (state.continuous) {
            // On réarme pour le code suivant au lieu de latcher `consumed`.
            state.cooldownUntil = Date.now() + CONTINUOUS_COOLDOWN_MS;
            state.lastRead = null;
            state.readStreak = 0;
        } else {
            state.consumed = true;
        }
        return true;
    }

    // Code confirmé : mode continu = on émet `onCode` (le contrôleur de page
    // gère dé-dup + feedback via continuousFeedback) ; mode unique = ferme le
    // modal et applique la valeur (legacy).
    function onConfirmed(state, btn, v) {
        if (state.continuous) {
            if (typeof state.onCode === "function") state.onCode(v);
            return;
        }
        closeModal(state).then(function () {
            window.BibliOfelia.scan.setBusy(btn, false);
            var consumed = window.BibliOfelia.scan.applyResult(btn, { value: v });
            if (!consumed) {
                window.BibliOfelia.scan.flashMessage(btn, t("scanned", "Valeur scannée :") + " " + v);
            }
        });
    }

    // ---- Moteur 1 : html5-qrcode (BarcodeDetector natif quand dispo) ---------
    function startHtml5(state, btn, opts) {
        var Html5Qrcode = window.Html5Qrcode;
        if (!Html5Qrcode) {
            return closeModal(state).then(function () { opts.onUnavailable("lib-not-loaded"); });
        }
        var formats;
        if (window.Html5QrcodeSupportedFormats) {
            formats = [window.Html5QrcodeSupportedFormats.EAN_13]; // EAN-13 uniquement
        }
        var scanner = new Html5Qrcode("scan-camera-viewfinder", {
            verbose: false,
            experimentalFeatures: { useBarCodeDetectorIfSupported: true }
        });
        state.stopEngine = function () {
            var sp = Promise.resolve();
            if (state.scannerActive) {
                try { sp = scanner.stop().catch(function () {}); } catch (e) { /* idem */ }
            }
            return sp.finally(function () {
                try { if (typeof scanner.clear === "function") scanner.clear(); } catch (e) { /* idem */ }
            });
        };
        var config = {
            fps: 10,
            formatsToSupport: formats,
            // Zone de décodage restreinte à une bande centrale (~1/4 de hauteur) :
            // un seul code-barres y tient → aucune ambiguïté quand plusieurs codes
            // sont dans le champ. html5-qrcode ombre l'extérieur de cette bande
            // (guide visuel intégré).
            qrbox: function (vw, vh) {
                return {
                    width: Math.max(150, Math.floor(vw * 0.92)),
                    height: Math.max(70, Math.floor(vh * 0.25))
                };
            },
            // Haute résolution → petits codes nets ; via videoConstraints (le 1er
            // arg de start() doit avoir exactement 1 clé).
            videoConstraints: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };
        scanner.start(
            { facingMode: "environment" },
            config,
            function onScan(decodedText) {
                if (handleRead(state, decodedText)) onConfirmed(state, btn, (decodedText || "").trim());
            },
            function onScanFailure(/* err */) { /* tentatives ratées normales */ }
        ).then(function () {
            state.scannerActive = true;
        }).catch(function (err) {
            console.error("[scan-camera] html5 start failed", err);
            var info = classifyMediaError(err);
            closeModal(state).then(function () { opts.onUnavailable(info.reason, info.detail); });
        });
    }

    // ---- Moteur 2 : QuaggaJS (Safari iOS / Firefox Android) ------------------
    function startQuagga(state, btn, opts) {
        var Quagga = window.Quagga;
        if (!Quagga) {
            return closeModal(state).then(function () { opts.onUnavailable("lib-not-loaded"); });
        }
        ensureViewfinderCss();
        var target = document.getElementById("scan-camera-viewfinder");

        function onDet(result) {
            if (state.consumed || !result || !result.codeResult) return;
            var v = result.codeResult.code;
            if (handleRead(state, v)) onConfirmed(state, btn, (v || "").trim());
        }
        state.stopEngine = function () {
            try { Quagga.offDetected(onDet); } catch (e) { /* idem */ }
            try { Quagga.stop(); } catch (e) { /* idem */ }
            return Promise.resolve();
        };

        Quagga.init({
            inputStream: {
                type: "LiveStream",
                target: target,
                constraints: {
                    facingMode: "environment",
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                },
                // Zone de décodage restreinte à une bande centrale (~1/4 de
                // hauteur) : un seul code-barres y tient (cf. qrbox côté html5).
                area: { top: "37%", right: "0%", left: "0%", bottom: "37%" }
            },
            decoder: { readers: ["ean_reader"] }, // EAN-13 uniquement
            locator: { patchSize: "medium", halfSample: true },
            locate: true,
            numOfWorkers: 0, // décodage sur le thread principal (robuste hors-ligne)
            frequency: 10
        }, function (err) {
            if (err) {
                console.error("[scan-camera] Quagga.init failed", err);
                var info = classifyMediaError(err);
                closeModal(state).then(function () { opts.onUnavailable(info.reason, info.detail); });
                return;
            }
            Quagga.onDetected(onDet);
            try { Quagga.start(); } catch (e) { /* start est sync ici */ }
            // Guide visuel : Quagga n'ombre pas l'extérieur de l'area, on ajoute
            // une bande (haut/bas assombris) alignée sur l'area de décodage.
            var band = document.createElement("div");
            band.className = "scan-camera-band";
            target.appendChild(band);
            state.scannerActive = true;
        });
    }

    // iOS Safari exige que getUserMedia soit appelé DANS le geste utilisateur.
    // Comme on lazy-load ensuite la lib, on demande d'abord la permission ici
    // (synchrone dans le tap) ; la permission accordée persiste pour la session,
    // et le moteur pourra racquérir la caméra après chargement de la lib.
    function primeCameraPermission() {
        return navigator.mediaDevices
            .getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false })
            .then(function (stream) {
                stream.getTracks().forEach(function (track) { track.stop(); });
            });
    }

    function openCamera(btn, opts) {
        opts = opts || {};
        var onUnavailable = typeof opts.onUnavailable === "function"
            ? opts.onUnavailable : function () {};
        var onClose = typeof opts.onClose === "function" ? opts.onClose : function () {};
        var continuous = opts.continuous === true;

        if (!window.isSecureContext || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            var ctxDetail = "secureContext=" + (window.isSecureContext === true)
                + " mediaDevices=" + (!!navigator.mediaDevices)
                + " getUserMedia=" + (!!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia));
            onUnavailable("insecure-context", ctxDetail);
            return;
        }

        var useNative = ("BarcodeDetector" in window);

        window.BibliOfelia.scan.setBusy(btn, true,
            "⏳ " + t("opening", "Ouverture de la caméra…"));

        var state = {
            overlay: makeModal(),
            stopEngine: null,
            scannerActive: false,
            consumed: false,
            closed: false,
            continuous: continuous,
            // FEAT-052 : n'accepter le préfixe 977 (ISSN) que si le contrôleur de
            // page l'a explicitement demandé (catalogage). Défaut : refusé.
            allowIssn: opts.allowIssn === true,
            onCode: typeof opts.onCode === "function" ? opts.onCode : null,
            count: 0,
            cooldownUntil: 0,
            // Garde anti « ghost click » mobile : le tap qui ouvre le modal
            // plein écran peut être re-livré à l'overlay sous le doigt et le
            // fermer instantanément → on ignore toute fermeture trop précoce.
            openedAt: Date.now()
        };
        var DISMISS_GUARD_MS = 600;
        function tooEarlyToClose() {
            return (Date.now() - state.openedAt) < DISMISS_GUARD_MS;
        }
        function dismiss() {
            closeModal(state).then(function () {
                window.BibliOfelia.scan.setBusy(btn, false);
                onClose();
            });
        }
        state.onKey = function (ev) {
            if (ev.key === "Escape") {
                if (tooEarlyToClose()) return;
                dismiss();
            }
        };

        // En mode continu, l'action n'est pas « Annuler » mais « Terminer ».
        if (continuous) {
            var cancelBtn = state.overlay.querySelector(".scan-camera-cancel");
            if (cancelBtn) cancelBtn.textContent = t("done", "Terminer");
        }

        document.body.appendChild(state.overlay);
        document.body.classList.add("scan-camera-open");
        document.addEventListener("keydown", state.onKey);

        function userCancel() {
            if (tooEarlyToClose()) return;
            dismiss();
        }
        state.overlay.querySelector(".scan-camera-close").addEventListener("click", userCancel);
        state.overlay.querySelector(".scan-camera-cancel").addEventListener("click", userCancel);
        state.overlay.addEventListener("click", function (ev) {
            if (ev.target === state.overlay) userCancel();
        });

        var loader = useNative ? loadLib : loadQuagga;
        primeCameraPermission()
            .then(function () { return loader(); })
            .then(function () {
                if (useNative) startHtml5(state, btn, { onUnavailable: onUnavailable });
                else startQuagga(state, btn, { onUnavailable: onUnavailable });
            })
            .catch(function (err) {
                console.error("[scan-camera] prime/lib", err);
                var info = classifyMediaError(err);
                var isLibLoad = err && /load-failed|missing-after-load/.test(err.message || "");
                var reason = isLibLoad ? "lib-load-failed" : info.reason;
                closeModal(state).then(function () { onUnavailable(reason, info.detail); });
            });
    }

    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.scan = window.BibliOfelia.scan || {};
    window.BibliOfelia.scan.openCamera = openCamera;
    window.BibliOfelia.scan.continuousFeedback = continuousFeedback;
})();
