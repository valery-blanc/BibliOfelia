/* L'icône OFELIA quitte le guide vers l'application. Le texte
   « Guide BiblOFELIA » reste l'accueil du guide (le lien que Material
   mettait sur l'icône).

   Le même HTML est servi sous /docs/, sous /bibliofelia/docs/ et à la
   racine de docs.bibliofelia.org. L'adresse de l'application se déduit
   donc du chemin. Contrat : docs/user-guide/header_home.py. */
(function (root) {
    "use strict";

    var LANGS = { en: true, es: true, mg: true };
    var PUBLIC_HOME = "https://bibliofelia.org/";

    function appHref(pathname) {
        var parts = String(pathname || "").split("/");
        var docsAt = parts.indexOf("docs");
        var prefix;
        var rest;
        var lang;
        var head;
        if (docsAt < 0) return PUBLIC_HOME;
        prefix = parts.slice(1, docsAt).filter(function (part) { return part; });
        rest = parts.slice(docsAt + 1).filter(function (part) { return part; });
        lang = rest.length && LANGS[rest[0]] ? rest[0] : "fr";
        head = prefix.length ? "/" + prefix.join("/") : "";
        return head + "/" + lang + "/";
    }

    function linkifyElement(el, href) {
        var link;
        if (!el || el.querySelector("a.bo-guide-home")) return;
        link = document.createElement("a");
        link.className = "bo-guide-home";
        link.href = href;
        while (el.firstChild) link.appendChild(el.firstChild);
        el.appendChild(link);
    }

    function linkifyNavTitle(label, href) {
        var textNodes = [];
        var node;
        var link;
        if (!label || label.querySelector("a.bo-guide-home")) return;
        for (node = label.firstChild; node; node = node.nextSibling) {
            if (node.nodeType === 3 && node.textContent.trim()) textNodes.push(node);
        }
        if (!textNodes.length) return;
        link = document.createElement("a");
        link.className = "bo-guide-home";
        link.href = href;
        label.insertBefore(link, textNodes[0]);
        textNodes.forEach(function (textNode) { link.appendChild(textNode); });
    }

    function wire() {
        var headerLogo = document.querySelector(".md-header a.md-logo");
        var navLogo = document.querySelector(".md-nav__title a.md-logo");
        var source = headerLogo || navLogo;
        var guideHref;
        var app;
        var topic;
        if (!source || source.getAttribute("data-bo-app") === "1") return;
        guideHref = source.href;
        app = appHref(window.location.pathname);
        [headerLogo, navLogo].forEach(function (logo) {
            if (!logo) return;
            logo.setAttribute("data-bo-app", "1");
            logo.href = app;
            logo.title = "BiblOFELIA";
            logo.setAttribute("aria-label", "BiblOFELIA");
        });
        topic = document.querySelector(
            ".md-header__title .md-header__topic:not([data-md-component='header-topic']) .md-ellipsis"
        );
        linkifyElement(topic, guideHref);
        linkifyNavTitle(
            document.querySelector(".md-nav--primary > .md-nav__title"),
            guideHref
        );
    }

    if (typeof document !== "undefined") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", wire);
        } else {
            wire();
        }
    }

    if (typeof module !== "undefined" && module.exports) {
        module.exports = { appHref: appHref };
    } else {
        root.BibliofeliaGuide = { appHref: appHref };
    }
})(typeof window !== "undefined" ? window : this);
