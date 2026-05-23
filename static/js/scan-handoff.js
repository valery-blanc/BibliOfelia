/* FEAT-023/024 — Click handler des boutons `.js-scan-handoff`.
 *
 * Stratégie (révision Val 2026-05-23) :
 *   1. Si la caméra du navigateur est disponible (HTTPS + getUserMedia + lib),
 *      on ouvre la caméra interne (modal in-page, on ne sort pas du site).
 *   2. Sinon, fallback automatique sur le handoff OfeliaScan, avec dans la
 *      flashMessage la raison technique exacte (utile pour diagnostiquer).
 *
 * Attributs déclaratifs (FEAT-023) :
 *   data-scan-target       : sélecteur CSS du <input> à pré-remplir
 *   data-scan-kind         : auto | book | card
 *   data-scan-autosubmit   : "true" pour soumettre le form
 *   data-scan-dispatch-url : URL de redirection (?q= ajouté)
 *
 * Helpers exposés via `window.BibliOfelia.scan` (consommés par scan-camera.js).
 */
(function () {
    "use strict";

    var POLL_INTERVAL_MS = 700;
    var TIMEOUT_MS = 120 * 1000;
    var activeHandoffs = new WeakMap(); // btn → { intervalId, cancelEl }

    function getConfig() {
        var el = document.getElementById("scan-handoff-config");
        if (!el) return null;
        try { return JSON.parse(el.textContent); } catch (e) { return null; }
    }

    function jsonHeaders() {
        var cfg = getConfig() || {};
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
            removeCancelLink(btn);
        }
    }

    function addCancelLink(btn) {
        removeCancelLink(btn);
        var link = document.createElement("button");
        link.type = "button";
        link.className = "scan-handoff-cancel";
        link.textContent = "Annuler";
        link.style.cssText = "display:block;margin-top:6px;background:none;border:none;color:var(--burgundy);text-decoration:underline;cursor:pointer;font-size:13px;padding:4px;";
        link.addEventListener("click", function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            cancelHandoff(btn);
        });
        btn.parentNode.appendChild(link);
        var state = activeHandoffs.get(btn) || {};
        state.cancelEl = link;
        activeHandoffs.set(btn, state);
    }

    function removeCancelLink(btn) {
        var state = activeHandoffs.get(btn);
        if (state && state.cancelEl && state.cancelEl.parentNode) {
            state.cancelEl.parentNode.removeChild(state.cancelEl);
            state.cancelEl = null;
        }
    }

    function cancelHandoff(btn) {
        var state = activeHandoffs.get(btn);
        if (state && state.intervalId) {
            clearInterval(state.intervalId);
        }
        activeHandoffs.delete(btn);
        setBusy(btn, false);
        flashMessage(btn, "Scan annulé.");
    }

    function flashMessage(btn, text) {
        var anchor = btn.parentNode;
        var note = anchor.querySelector(":scope > .scan-handoff-note");
        if (!note) {
            note = document.createElement("div");
            note.className = "scan-handoff-note muted text-sm";
            note.style.cssText = "margin-top:8px;font-size:13px;color:var(--grey);";
            anchor.appendChild(note);
        }
        note.textContent = text;
        setTimeout(function () { if (note && note.parentNode) note.parentNode.removeChild(note); }, 6000);
    }

    function chooseDeepLinkUrl(handoff) {
        // Sur Chrome / Samsung Browser / Edge Android, on cible l'intent:// qui
        // contourne le blocage silencieux du scheme custom. On ajoute
        // `S.browser_fallback_url=<page courante>` pour empêcher Chrome de
        // rediriger vers le Play Store si OfeliaScan n'est pas installé.
        var ua = navigator.userAgent || "";
        var isChromeLikeAndroid = /Android/i.test(ua) && /(Chrome|SamsungBrowser|EdgA)/i.test(ua);
        if (isChromeLikeAndroid && handoff.android_intent_url) {
            var fallback = encodeURIComponent(window.location.href);
            return handoff.android_intent_url.replace(
                /;end$/,
                ";S.browser_fallback_url=" + fallback + ";end"
            );
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

    function startHandoff(btn) {
        var targetKind = btn.dataset.scanKind || "auto";
        setBusy(btn, true, "⏳ " + (btn.dataset.busyLabelHandoff || "En attente d’OfeliaScan…"));
        addCancelLink(btn);

        createHandoff(targetKind).then(function (handoff) {
            openDeepLink(chooseDeepLinkUrl(handoff));

            var started = Date.now();
            var intervalId = setInterval(function () {
                // Si l'utilisateur a annulé via le lien, on n'est plus dans la map.
                if (!activeHandoffs.has(btn)) {
                    clearInterval(intervalId);
                    return;
                }
                if (Date.now() - started > TIMEOUT_MS) {
                    clearInterval(intervalId);
                    activeHandoffs.delete(btn);
                    setBusy(btn, false);
                    flashMessage(btn, "Délai d’attente OfeliaScan dépassé (2 min). Tapez la valeur à la main si l’app n’est pas installée.");
                    return;
                }
                pollHandoff(handoff.token).then(function (res) {
                    if (!res || res.state === "pending") return;
                    clearInterval(intervalId);
                    activeHandoffs.delete(btn);
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
            activeHandoffs.set(btn, { intervalId: intervalId, cancelEl: (activeHandoffs.get(btn) || {}).cancelEl });
        }).catch(function (err) {
            activeHandoffs.delete(btn);
            setBusy(btn, false);
            flashMessage(btn, "Erreur création handoff (" + (err && err.message ? err.message : "?") + ").");
        });
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

    function explainCameraFailure(info) {
        if (!info.isSecureContext) return "HTTPS requis (URL en " + info.protocol + ")";
        if (!info.hasMediaDevices) return "navigateur sans navigator.mediaDevices";
        if (!info.hasGetUserMedia) return "navigateur sans getUserMedia";
        if (!info.hasModule) return "module scan-camera.js non chargé";
        return "raison inconnue";
    }

    window.BibliOfelia = window.BibliOfelia || {};
    window.BibliOfelia.scan = {
        applyResult: applyResult,
        flashMessage: flashMessage,
        setBusy: setBusy,
        startHandoff: startHandoff,
        cameraSupported: cameraSupported,
        cameraSupportInfo: cameraSupportInfo
    };

    document.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".js-scan-handoff");
        if (!btn) return;
        if (btn.disabled || btn.classList.contains("is-busy")) {
            ev.preventDefault();
            return;
        }
        ev.preventDefault();

        var info = cameraSupportInfo();
        console.log("[scan] camera support:", info);

        if (info.ok) {
            window.BibliOfelia.scan.openCamera(btn, {
                onUnavailable: function (reason) {
                    console.warn("[scan] caméra indisponible (" + reason + "), fallback OfeliaScan.");
                    flashMessage(btn, "Caméra indisponible (" + reason + ") — ouverture d’OfeliaScan.");
                    startHandoff(btn);
                }
            });
            return;
        }

        flashMessage(btn, "Caméra interne indisponible : " + explainCameraFailure(info) + ". OfeliaScan utilisé en secours.");
        startHandoff(btn);
    });
})();
