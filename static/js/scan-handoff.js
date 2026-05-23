/* FEAT-023/024 — Scan handoff single-scan (BibliOfelia web ↔ OfeliaScan)
 * + chemin caméra navigateur (`scan-camera.js`).
 *
 * Boutons marqués `.js-scan-handoff` :
 *   data-scan-target      : sélecteur CSS d'un <input> à pré-remplir
 *   data-scan-kind        : auto | book | card  (indication UI pour OfeliaScan)
 *   data-scan-autosubmit  : "true" pour soumettre le form après remplissage
 *   data-scan-dispatch-url: URL vers laquelle rediriger après scan (ex. /search/),
 *                           le JS ajoute ?q=<valeur> automatiquement
 *
 * Modes :
 *   - `ofeliascan` (défaut) : ouvre OfeliaScan via `ofeliascan://scan-one?token=...`,
 *     puis poll `/api/v1/scan-handoff/{token}` (TTL serveur 5 min, timeout client 120 s).
 *   - `camera`              : géré par `scan-camera.js` (cf. FEAT-024). Le mode est
 *     lu depuis `localStorage['bibliofelia.scan-mode']`. Quand actif, ce module
 *     délègue à `BibliOfelia.scan.openCamera(btn)` et ne fait pas de handoff.
 *
 * Helpers partagés exposés via `window.BibliOfelia.scan` (utilisés par
 * `scan-camera.js`).
 */
(function () {
    "use strict";

    var POLL_INTERVAL_MS = 700;
    var TIMEOUT_MS = 120 * 1000;
    var STORAGE_KEY = "bibliofelia.scan-mode";

    function getConfig() {
        var el = document.getElementById("scan-handoff-config");
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (e) { return null; }
    }

    function jsonHeaders() {
        var cfg = getConfig() || {};
        // `csrftoken` cookie est HttpOnly (CSRF_COOKIE_HTTPONLY=True) → on lit
        // le token rendu par le template `{% csrf_token %}` (même approche que
        // `hx-headers` sur <body> pour HTMX).
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRFToken": cfg.csrfToken || ""
        };
    }

    function createHandoff(targetKind) {
        var cfg = getConfig();
        if (!cfg || !cfg.createUrl) {
            console.error("[scan-handoff] config introuvable dans #scan-handoff-config");
            return Promise.reject(new Error("config"));
        }
        return fetch(cfg.createUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: jsonHeaders(),
            body: JSON.stringify({ target_kind: targetKind || "auto" })
        }).then(function (resp) {
            if (!resp.ok) {
                return resp.text().then(function (body) {
                    console.error("[scan-handoff] POST", cfg.createUrl, "→", resp.status, body);
                    throw new Error("create-failed-" + resp.status);
                });
            }
            return resp.json();
        });
    }

    function pollHandoff(token) {
        var cfg = getConfig();
        var url = cfg.createUrl + "/" + token;
        return fetch(url, {
            credentials: "same-origin",
            headers: { "Accept": "application/json" }
        }).then(function (resp) {
            if (!resp.ok) return { state: "error", status: resp.status };
            return resp.json();
        });
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
                btn.innerHTML = "⏳ " + (btn.dataset.busyLabel || "En attente…");
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

    function flashMessage(btn, text) {
        // Cherche un point d'ancrage stable : .scan-split d'abord, sinon le parent direct.
        var anchor = btn.closest(".scan-split") || btn.parentNode;
        var note = anchor.querySelector(":scope > .scan-handoff-note");
        if (!note) {
            note = document.createElement("div");
            note.className = "scan-handoff-note muted text-sm";
            note.style.marginTop = "8px";
            anchor.appendChild(note);
        }
        note.textContent = text;
        setTimeout(function () { if (note.parentNode) note.parentNode.removeChild(note); }, 4500);
    }

    function chooseDeepLinkUrl(handoff) {
        // Sur Chrome / Samsung Browser Android, le scheme custom
        // `ofeliascan://…` est de plus en plus souvent ignoré silencieusement
        // (politique anti-deeplink-spam). L'URL `intent://…#Intent;package=…;end`
        // contourne la restriction en ciblant explicitement l'app installée.
        var ua = navigator.userAgent || "";
        var isChromeLikeAndroid = /Android/i.test(ua) && /(Chrome|SamsungBrowser|EdgA)/i.test(ua);
        if (isChromeLikeAndroid && handoff.android_intent_url) {
            return handoff.android_intent_url;
        }
        return handoff.deep_link;
    }

    function openDeepLink(url) {
        console.log("[scan-handoff] ouverture deep-link:", url);
        try { window.location.href = url; } catch (e) { console.warn("[scan-handoff]", e); }
    }

    function applyResult(btn, res) {
        var targetSel = btn.dataset.scanTarget || "";
        var autoSubmit = btn.dataset.scanAutosubmit === "true";
        var dispatchUrl = btn.dataset.scanDispatchUrl || "";

        if (dispatchUrl) {
            var u;
            try {
                u = new URL(dispatchUrl, window.location.origin);
            } catch (e) {
                u = null;
            }
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
                    if (typeof form.requestSubmit === "function") {
                        form.requestSubmit();
                    } else {
                        form.submit();
                    }
                    return true;
                }
            }
        }
        return false;
    }

    function readMode() {
        try {
            var v = window.localStorage && window.localStorage.getItem(STORAGE_KEY);
            return v === "camera" ? "camera" : "ofeliascan";
        } catch (e) {
            return "ofeliascan";
        }
    }

    function handleHandoff(btn) {
        var targetKind = btn.dataset.scanKind || "auto";
        setBusy(btn, true, "⏳ " + (btn.dataset.busyLabelHandoff || "En attente d’OfeliaScan…"));

        createHandoff(targetKind).then(function (handoff) {
            openDeepLink(chooseDeepLinkUrl(handoff));

            var started = Date.now();
            var interval = setInterval(function () {
                if (Date.now() - started > TIMEOUT_MS) {
                    clearInterval(interval);
                    setBusy(btn, false);
                    flashMessage(btn, "Scan abandonné (délai dépassé). Tapez la valeur à la main si OfeliaScan n’est pas installé.");
                    return;
                }
                pollHandoff(handoff.token).then(function (res) {
                    if (!res || res.state === "pending") return;
                    clearInterval(interval);
                    if (res.state === "completed") {
                        var consumed = applyResult(btn, res);
                        if (!consumed) {
                            setBusy(btn, false);
                            flashMessage(btn, "Valeur scannée : " + res.value);
                        }
                    } else if (res.state === "cancelled") {
                        setBusy(btn, false);
                        flashMessage(btn, "Scan annulé dans OfeliaScan.");
                    } else if (res.state === "expired" || res.state === "error") {
                        setBusy(btn, false);
                        flashMessage(btn, "Le handoff a expiré. Recommencez.");
                    }
                });
            }, POLL_INTERVAL_MS);
        }).catch(function (err) {
            setBusy(btn, false);
            flashMessage(btn, "Erreur à la création du handoff (" + (err && err.message ? err.message : "?") + "). Ouvre la console pour le détail.");
        });
    }

    // Namespace partagé (consommé par `scan-camera.js`, `scan-mode-toggle.js`).
    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.scan = {
        STORAGE_KEY: STORAGE_KEY,
        applyResult: applyResult,
        flashMessage: flashMessage,
        setBusy: setBusy,
        readMode: readMode
    };

    document.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".js-scan-handoff");
        if (!btn) return;
        if (btn.disabled || btn.classList.contains("is-busy")) {
            ev.preventDefault();
            return;
        }
        ev.preventDefault();

        var mode = readMode();
        if (mode === "camera"
                && window.BibliOfelia.scan.openCamera
                && window.isSecureContext) {
            window.BibliOfelia.scan.openCamera(btn);
            return;
        }
        // Fallback gracieux : mode caméra demandé mais HTTPS absent ou module
        // non chargé → on retombe sur le handoff OfeliaScan.
        if (mode === "camera" && !window.isSecureContext) {
            flashMessage(btn, "HTTPS requis pour la caméra. Bascule sur OfeliaScan.");
        }
        handleHandoff(btn);
    });
})();
