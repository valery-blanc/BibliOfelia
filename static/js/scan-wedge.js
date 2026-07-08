/* FEAT-054 — Support douchette USB (keyboard-wedge global).
 *
 * Une douchette USB est un clavier HID : elle « tape » les chiffres du code
 * très vite puis envoie un terminateur. Ce terminateur est le piège : la plupart
 * des douchettes envoient **CR + LF**, or en événements clavier
 *   CR = Ctrl+M  → interprété comme Entrée,
 *   LF = Ctrl+J  → interprété par le navigateur comme le raccourci « page des
 *                  téléchargements » (BUG-020) ;
 * certaines ajoutent un **Tab** (→ changement de champ/onglet). Un `<input>`
 * texte NE consomme PAS ces raccourcis : ils fuient même quand le focus est dans
 * un champ.
 *
 * Ce module écoute le clavier au niveau du document en **phase de capture**,
 * reconnaît la signature d'un scan (rafale de frappes ≤ MAX_INTERKEY_MS) et
 * **avale toute la salve** — chiffres ET terminateurs de contrôle (CR/LF/Tab) —
 * via preventDefault + stopImmediatePropagation, avec une fenêtre de garde après
 * dispatch pour absorber le LF traînant. Plus rien n'atteint les raccourcis du
 * navigateur. Puis on route le code (champ de scan primaire → remplir+submit,
 * sinon → core:search).
 *
 * Deux effets voulus (temp.txt Val 2026-07-08) :
 *   1. plus d'ouverture parasite de la page de téléchargement (BUG-020) ;
 *   2. plus besoin de cliquer dans un champ (écoute globale).
 *
 * Config JSON dans `#scan-wedge-config` : {searchUrl, maxInterKeyMs, minLen, guardMs}.
 */
(function () {
    "use strict";

    function readConfig() {
        var el = document.getElementById("scan-wedge-config");
        if (!el) return {};
        try { return JSON.parse(el.textContent) || {}; } catch (e) { return {}; }
    }
    var CFG = readConfig();

    // Douchette : < ~5 ms/char. Marge large (50 ms), bien en-deçà de la frappe
    // humaine la plus rapide (~120 ms entre deux touches).
    var MAX_INTERKEY_MS = CFG.maxInterKeyMs || 50;
    var MIN_LEN = CFG.minLen || 3;
    var GUARD_MS = CFG.guardMs || 300;
    var FLUSH_MS = Math.max(60, MAX_INTERKEY_MS + 20);
    var SEARCH_URL = CFG.searchUrl || "";

    var buffer = "";
    var lastTime = 0;
    var guardUntil = 0;
    var flushTimer = null;

    function cameraOpen() {
        return document.body.classList.contains("scan-camera-open");
    }

    function resetBuffer() {
        buffer = "";
        lastTime = 0;
        if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
    }

    function armFlush() {
        if (flushTimer) clearTimeout(flushTimer);
        flushTimer = setTimeout(function () {
            var code = buffer;
            resetBuffer();
            if (code.length >= MIN_LEN) {
                guardUntil = Date.now() + GUARD_MS;
                dispatchCode(code);
            }
        }, FLUSH_MS);
    }

    /* Champ de scan « primaire » de la page + son form.
     *   1. input `data-wedge-primary` (lend/return + catalogage douchette) ;
     *   2. champ désigné par un bouton `.js-scan-handoff[data-scan-target]`. */
    function findPrimaryTarget() {
        var input = document.querySelector("input[data-wedge-primary]");
        if (input && input.offsetParent !== null) {
            return { input: input, autosubmit: input.dataset.wedgeAutosubmit !== "false" };
        }
        var btn = document.querySelector(".js-scan-handoff[data-scan-target]");
        if (btn) {
            var form = btn.closest("form");
            var sel = btn.dataset.scanTarget;
            var t = form ? form.querySelector(sel) : document.querySelector(sel);
            if (t && t.offsetParent !== null) {
                return { input: t, autosubmit: btn.dataset.scanAutosubmit === "true" };
            }
        }
        return null;
    }

    function dispatchCode(code) {
        code = (code || "").trim();
        if (code.length < MIN_LEN) return;

        var target = findPrimaryTarget();
        if (target) {
            target.input.value = code;
            target.input.dispatchEvent(new Event("input", { bubbles: true }));
            var form = target.input.closest("form");
            if (target.autosubmit && form) {
                if (typeof form.requestSubmit === "function") form.requestSubmit();
                else form.submit();
            } else {
                target.input.focus();
            }
            return;
        }
        if (SEARCH_URL) {
            var u;
            try { u = new URL(SEARCH_URL, window.location.origin); }
            catch (e) { u = null; }
            if (u) {
                u.searchParams.set("q", code);
                window.location.href = u.toString();
            }
        }
    }

    function onKeydown(ev) {
        var now = Date.now();

        // 1. Fenêtre de garde : juste après un scan traité, on avale les touches
        //    résiduelles (LF=Ctrl+J après le CR, ou un suffixe) — AVANT tout autre
        //    test, sinon le Ctrl+J fuit vers la page de téléchargement (BUG-020).
        if (now < guardUntil) {
            ev.preventDefault();
            ev.stopImmediatePropagation();
            return;
        }

        // 2. Modal caméra ouvert → le wedge se retire.
        if (cameraOpen()) { resetBuffer(); return; }

        var dt = lastTime === 0 ? Infinity : (now - lastTime);
        var inBurst = buffer.length > 0 && dt <= MAX_INTERKEY_MS;

        var key = ev.key;
        var isEnter = key === "Enter";
        var isTab = key === "Tab";

        // 3. Terminateur (Entrée depuis le CR, ou Tab de suffixe).
        if (isEnter || isTab) {
            if (inBurst && buffer.length >= MIN_LEN) {
                ev.preventDefault();
                ev.stopImmediatePropagation();
                var code = buffer;
                resetBuffer();
                guardUntil = now + GUARD_MS;   // avale le LF/CR qui suit
                dispatchCode(code);
            } else {
                resetBuffer();   // Entrée/Tab humain → comportement natif
            }
            return;
        }

        var printable = key && key.length === 1 && !ev.ctrlKey && !ev.altKey && !ev.metaKey;

        // 4. En pleine rafale : on avale TOUT (y compris un Ctrl-combo que la
        //    douchette insérerait au milieu) pour ne rien laisser fuir.
        if (inBurst) {
            ev.preventDefault();
            ev.stopImmediatePropagation();
            if (printable) buffer += key;
            lastTime = now;
            armFlush();
            return;
        }

        // 5. Hors rafale : 1er caractère potentiel, ou frappe humaine. On ne
        //    prévient PAS (un seul chiffre isolé qui fuit est inoffensif ; et il
        //    ne faut pas bloquer la saisie clavier normale).
        if (printable) {
            buffer = key;
            lastTime = now;
            armFlush();
            return;
        }

        resetBuffer();
    }

    // Phase de CAPTURE : on passe avant les handlers de la page ET avant que le
    // navigateur ne traite ses raccourcis.
    document.addEventListener("keydown", onKeydown, true);

    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.wedge = { dispatchCode: dispatchCode };
})();
