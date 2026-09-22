/* learners.ai - directory filtering, search and sorting.
 *
 * Zero dependencies, no fetch, no framework. Every card is already in the HTML
 * (so the directory works with JavaScript disabled and crawlers see the full
 * list); this script only shows and hides what is already there, and keeps the
 * URL in sync so a filtered view can be shared or bookmarked.
 *
 * Facet counts are recomputed on every change, counting each option against the
 * *other* active filters - the behaviour people expect from faceted search.
 */
(function () {
  "use strict";

  var CARD_SELECTOR = "[data-tool]";
  var GROUP_ATTR = {
    category: "category",
    pricing: "pricing",
    role: "roles",
    platform: "platforms"
  };

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
    });
  }

  function init(root) {
    var results = root.querySelector("[data-results]");
    if (!results) return;

    var cards = Array.prototype.slice.call(results.querySelectorAll(CARD_SELECTOR));
    var searchInput = root.querySelector("[data-search]");
    var sortSelect = root.querySelector("[data-sort]");
    var countEl = root.querySelector("[data-results-count]");
    var emptyEl = root.querySelector("[data-empty]");
    var activeList = root.querySelector("[data-active-filters]");
    var clearButton = root.querySelector("[data-clear]");
    var inputs = Array.prototype.slice.call(root.querySelectorAll("[data-filter-input]"));

    var state = { q: "", sort: "relevant", category: [], pricing: [], role: [], platform: [] };

    /* ---------------------------------------------------------------- state */
    function readUrl() {
      var params = new URLSearchParams(window.location.search);
      state.q = (params.get("q") || "").trim();
      var sort = params.get("sort");
      if (sort) state.sort = sort;
      Object.keys(GROUP_ATTR).forEach(function (group) {
        var raw = params.get(group);
        state[group] = raw ? raw.split(",").filter(Boolean) : [];
      });
    }

    function writeUrl() {
      var params = new URLSearchParams();
      if (state.q) params.set("q", state.q);
      if (state.sort && state.sort !== "relevant") params.set("sort", state.sort);
      Object.keys(GROUP_ATTR).forEach(function (group) {
        // Category pages lock the category on, so it is not part of shareable state.
        var values = state[group].filter(function (value) {
          return !isLocked(group, value);
        });
        if (values.length) params.set(group, values.join(","));
      });
      var query = params.toString();
      var url = window.location.pathname + (query ? "?" + query : "") + window.location.hash;
      window.history.replaceState(null, "", url);
    }

    function isLocked(group, value) {
      return inputs.some(function (input) {
        return (
          input.hasAttribute("data-locked") &&
          input.getAttribute("data-filter-input") === group &&
          input.value === value
        );
      });
    }

    function applyToControls() {
      if (searchInput) searchInput.value = state.q;
      if (sortSelect) sortSelect.value = state.sort;
      inputs.forEach(function (input) {
        var group = input.getAttribute("data-filter-input");
        var on = state[group].indexOf(input.value) !== -1;
        // Category pages pre-filter by their category: keep that constraint on.
        if (input.hasAttribute("data-locked")) {
          on = true;
          if (state[group].indexOf(input.value) === -1) state[group].push(input.value);
        }
        input.checked = on;
      });
    }

    /* ------------------------------------------------------------- matching */
    function matches(card, overrides) {
      var overridesMap = overrides || {};
      var terms = state.q.toLowerCase().split(/\s+/).filter(Boolean);
      var haystack =
        " " +
        (card.getAttribute("data-search") || "") +
        " " +
        (card.getAttribute("data-keywords") || "") +
        " " +
        (card.getAttribute("data-maker") || "");
      for (var t = 0; t < terms.length; t++) {
        if (haystack.indexOf(terms[t]) === -1) return false;
      }
      for (var group in GROUP_ATTR) {
        if (!Object.prototype.hasOwnProperty.call(GROUP_ATTR, group)) continue;
        var wanted = overridesMap[group] || state[group];
        if (!wanted.length) continue;
        var actual = (card.getAttribute("data-" + GROUP_ATTR[group]) || "").split("|");
        var hit = wanted.some(function (value) {
          return actual.indexOf(value) !== -1;
        });
        if (!hit) return false;
      }
      return true;
    }

    /* --------------------------------------------------------------- render */
    function sortCards(visible) {
      var sorted = visible.slice();
      if (state.sort === "az") {
        sorted.sort(function (a, b) {
          return a.getAttribute("data-name").localeCompare(b.getAttribute("data-name"));
        });
      } else if (state.sort === "newest") {
        sorted.sort(function (a, b) {
          var diff = (b.getAttribute("data-launched") || "").localeCompare(a.getAttribute("data-launched") || "");
          return diff !== 0 ? diff : a.getAttribute("data-name").localeCompare(b.getAttribute("data-name"));
        });
      } else {
        sorted.sort(function (a, b) {
          var featured =
            (b.getAttribute("data-featured") === "true" ? 1 : 0) -
            (a.getAttribute("data-featured") === "true" ? 1 : 0);
          return featured !== 0 ? featured : a.getAttribute("data-name").localeCompare(b.getAttribute("data-name"));
        });
      }
      sorted.forEach(function (card) {
        results.appendChild(card);
      });
    }

    function updateFacetCounts() {
      inputs.forEach(function (input) {
        var group = input.getAttribute("data-filter-input");
        var overrides = {};
        overrides[group] = [input.value];
        var total = cards.filter(function (card) {
          return matches(card, overrides);
        }).length;
        var holder = input.parentNode.querySelector("[data-count-for='" + input.value + "']");
        if (holder) holder.textContent = total;
        input.parentNode.setAttribute("data-empty", total === 0 ? "true" : "false");
      });
    }

    function renderActiveFilters() {
      if (!activeList) return;
      activeList.innerHTML = "";
      var chips = [];
      if (state.q) chips.push({ group: "q", value: state.q, label: '"' + state.q + '"' });
      Object.keys(GROUP_ATTR).forEach(function (group) {
        state[group].forEach(function (value) {
          if (isLocked(group, value)) return;
          var match = inputs.filter(function (input) {
            return input.getAttribute("data-filter-input") === group && input.value === value;
          })[0];
          chips.push({
            group: group,
            value: value,
            label: match ? match.getAttribute("data-label") || value : value
          });
        });
      });
      chips.forEach(function (chip) {
        var li = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.className = "badge badge--soft";
        button.innerHTML =
          "<span>" +
          escapeHtml(chip.label) +
          "</span>" +
          '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.4"' +
          ' stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
        button.setAttribute("aria-label", "Remove filter: " + chip.label);
        button.addEventListener("click", function () {
          if (chip.group === "q") {
            state.q = "";
            if (searchInput) searchInput.value = "";
          } else {
            state[chip.group] = state[chip.group].filter(function (value) {
              return value !== chip.value;
            });
          }
          applyToControls();
          update();
        });
        li.appendChild(button);
        activeList.appendChild(li);
      });
    }

    function update(options) {
      var settings = options || {};
      var visible = [];
      cards.forEach(function (card) {
        var show = matches(card);
        card.hidden = !show;
        if (show) visible.push(card);
      });
      if (settings.resort) sortCards(visible);
      if (countEl) countEl.innerHTML = "<strong>" + visible.length + "</strong> of " + cards.length + " tools";
      if (emptyEl) emptyEl.hidden = visible.length !== 0;
      renderActiveFilters();
      updateFacetCounts();
      if (settings.syncUrl !== false) writeUrl();
    }

    /* ---------------------------------------------------------------- events */
    inputs.forEach(function (input) {
      input.addEventListener("change", function () {
        var group = input.getAttribute("data-filter-input");
        if (input.checked) {
          if (state[group].indexOf(input.value) === -1) state[group].push(input.value);
        } else {
          state[group] = state[group].filter(function (value) {
            return value !== input.value;
          });
        }
        update();
      });
    });

    if (searchInput) {
      var debounce;
      searchInput.addEventListener("input", function () {
        window.clearTimeout(debounce);
        debounce = window.setTimeout(function () {
          state.q = searchInput.value.trim();
          update();
        }, 120);
      });
      searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          searchInput.value = "";
          state.q = "";
          update();
        }
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener("change", function () {
        state.sort = sortSelect.value;
        update({ resort: true });
      });
    }

    if (clearButton) {
      clearButton.addEventListener("click", function () {
        state.q = "";
        state.category = [];
        state.pricing = [];
        state.role = [];
        state.platform = [];
        state.sort = "relevant";
        if (searchInput) searchInput.value = "";
        applyToControls(); // re-applies any locked (category page) constraints
        update({ resort: true });
        if (searchInput) searchInput.focus();
      });
    }

    readUrl();
    applyToControls();
    update({ resort: true, syncUrl: false });
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-directory]"), init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();


