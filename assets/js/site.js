/* learners.ai - small progressive enhancements shared by every page.
 *
 * Three jobs only: mobile navigation, copy-to-clipboard for the example
 * snippets, and the `/` keyboard shortcut for the search field. Everything the
 * site does critically useful works without this file.
 */
(function () {
  "use strict";

  function initNav() {
    var toggle = document.querySelector("[data-nav-toggle]");
    var nav = document.querySelector("[data-nav]");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", function () {
      var open = nav.getAttribute("data-open") === "true";
      nav.setAttribute("data-open", open ? "false" : "true");
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
    });
    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A" && window.innerWidth <= 760) {
        nav.setAttribute("data-open", "false");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (error) {
      ok = false;
    }
    document.body.removeChild(area);
    return ok;
  }

  function initCopy() {
    document.addEventListener("click", function (event) {
      var button = event.target.closest("[data-copy-target]");
      if (!button) return;
      var target = document.getElementById(button.getAttribute("data-copy-target"));
      if (!target) return;
      var text = target.innerText || target.textContent || "";
      var done = function (ok) {
        if (!ok) return;
        button.setAttribute("data-copied", "true");
        var label = button.querySelector("[data-copy-label]");
        var original = label ? label.textContent : "";
        if (label) label.textContent = "Copied";
        window.setTimeout(function () {
          button.removeAttribute("data-copied");
          if (label) label.textContent = original;
        }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(
          function () {
            done(true);
          },
          function () {
            done(legacyCopy(text));
          }
        );
      } else {
        done(legacyCopy(text));
      }
    });
  }

  function initShortcuts() {
    document.addEventListener("keydown", function (event) {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
      var tag = (event.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select" || event.target.isContentEditable) return;
      var field = document.querySelector("[data-search]") || document.querySelector('input[name="q"]');
      if (!field) return;
      event.preventDefault();
      field.focus();
      field.select();
    });
  }

  function boot() {
    initNav();
    initCopy();
    initShortcuts();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
