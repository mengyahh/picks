(function () {
  "use strict";

  var state = {
    items: [],
    types: [],
    categories: [],
    tags: [],
    axis: "category", // "category" | "type"
    activeGroup: null,
    activeTag: null,
    query: "",
    currentId: null,
  };

  var el = {
    navList: document.getElementById("navList"),
    tagCloud: document.getElementById("tagCloud"),
    searchInput: document.getElementById("searchInput"),
    reader: document.getElementById("reader"),
    emptyState: document.getElementById("emptyState"),
    itemView: document.getElementById("itemView"),
    itemType: document.getElementById("itemType"),
    itemCategory: document.getElementById("itemCategory"),
    itemTitle: document.getElementById("itemTitle"),
    itemSource: document.getElementById("itemSource"),
    itemTags: document.getElementById("itemTags"),
    itemImageWrap: document.getElementById("itemImageWrap"),
    lightbox: document.getElementById("lightbox"),
    lightboxImg: document.getElementById("lightboxImg"),
    itemBody: document.getElementById("itemBody"),
    sidebar: document.getElementById("sidebar"),
    navToggle: document.getElementById("navToggle"),
  };

  var TYPE_LABELS = {
    concept: "概念",
    case: "案例",
    quote: "語錄",
    visual: "視覺參考",
    note: "摘錄筆記",
    wishlist: "願望清單",
  };

  function typeLabel(t) {
    return TYPE_LABELS[t] || t;
  }

  fetch("data/index.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      state.items = data.items || [];
      state.types = data.types || [];
      state.categories = data.categories || [];
      state.tags = data.tags || [];
      renderTagCloud();
      renderNav();
      handleRoute();
    })
    .catch(function (err) {
      el.navList.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:8px;">資料載入失敗：' + err + "</p>";
    });

  function filteredItems() {
    var q = state.query.trim().toLowerCase();
    return state.items.filter(function (item) {
      if (state.activeTag && (item.tags || []).indexOf(state.activeTag) === -1) return false;
      if (!q) return true;
      var hay = [item.title, item.summary, item.source, item.category, item.type]
        .concat(item.tags || [])
        .join(" ")
        .toLowerCase();
      return hay.indexOf(q) !== -1;
    });
  }

  function groupKey(item) {
    return state.axis === "category" ? item.category : item.type;
  }

  function groupLabel(key) {
    return state.axis === "category" ? key : typeLabel(key);
  }

  function renderNav() {
    var groups = state.axis === "category" ? state.categories : state.types;
    var items = filteredItems();
    var byGroup = {};
    items.forEach(function (item) {
      var k = groupKey(item);
      if (!byGroup[k]) byGroup[k] = [];
      byGroup[k].push(item);
    });

    var html = "";
    if (state.query.trim()) {
      html += '<div class="results-count">搜尋結果：' + items.length + " 則</div>";
    }

    groups.forEach(function (g) {
      var groupItems = byGroup[g] || [];
      if (state.query.trim() && groupItems.length === 0) return;
      var isOpen = state.activeGroup === g || (state.query.trim() && groupItems.length > 0);
      html +=
        '<div class="nav-group' + (isOpen ? " open" : "") + '" data-group="' + escapeAttr(g) + '">' +
        '<button class="nav-group-title" data-group-toggle="' + escapeAttr(g) + '">' +
        '<span><span class="chevron">▶</span>' + escapeHtml(groupLabel(g)) + "</span>" +
        '<span class="nav-group-count">' + groupItems.length + "</span>" +
        "</button>" +
        '<div class="nav-items">' +
        groupItems
          .map(function (item) {
            return (
              '<button class="nav-item' + (item.id === state.currentId ? " active" : "") + '" data-id="' +
              escapeAttr(item.id) + '">' + escapeHtml(item.title) + "</button>"
            );
          })
          .join("") +
        "</div></div>";
    });

    if (!html) {
      html = '<p style="color:var(--text-muted);font-size:13px;padding:8px;">沒有符合的內容。</p>';
    }

    el.navList.innerHTML = html;

    el.navList.querySelectorAll("[data-group-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var g = btn.getAttribute("data-group-toggle");
        state.activeGroup = state.activeGroup === g ? null : g;
        renderNav();
      });
    });
    el.navList.querySelectorAll("[data-id]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        navigateTo(btn.getAttribute("data-id"));
        closeSidebarOnMobile();
      });
    });
  }

  function renderTagCloud() {
    el.tagCloud.innerHTML = state.tags
      .map(function (t) {
        return (
          '<button class="tag-chip' + (state.activeTag === t ? " active" : "") + '" data-tag="' +
          escapeAttr(t) + '">' + escapeHtml(t) + "</button>"
        );
      })
      .join("");
    el.tagCloud.querySelectorAll("[data-tag]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var t = btn.getAttribute("data-tag");
        state.activeTag = state.activeTag === t ? null : t;
        renderTagCloud();
        renderNav();
      });
    });
  }

  document.querySelectorAll(".axis-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".axis-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      state.axis = btn.getAttribute("data-axis");
      state.activeGroup = null;
      renderNav();
    });
  });

  var searchDebounce;
  el.searchInput.addEventListener("input", function () {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(function () {
      state.query = el.searchInput.value;
      renderNav();
    }, 120);
  });

  el.navToggle.addEventListener("click", function () {
    el.sidebar.classList.toggle("open");
  });
  function closeSidebarOnMobile() {
    if (window.innerWidth <= 860) el.sidebar.classList.remove("open");
  }

  function navigateTo(id) {
    window.location.hash = "#" + id;
  }

  window.addEventListener("hashchange", handleRoute);

  function handleRoute() {
    var id = window.location.hash.replace(/^#/, "");
    if (!id) {
      state.currentId = null;
      el.emptyState.hidden = false;
      el.itemView.hidden = true;
      renderNav();
      return;
    }
    var item = state.items.find(function (i) { return i.id === id; });
    if (!item) return;
    state.currentId = id;
    renderNav();
    loadItem(item);
  }

  function loadItem(item) {
    el.emptyState.hidden = true;
    el.itemView.hidden = false;
    el.itemType.textContent = typeLabel(item.type);
    el.itemCategory.textContent = item.category;
    el.itemTitle.textContent = item.title;
    el.itemSource.textContent = item.source ? "來源：" + item.source : "";
    el.itemTags.innerHTML = (item.tags || [])
      .map(function (t) { return '<span class="tag-chip">' + escapeHtml(t) + "</span>"; })
      .join("");

    renderImages(item);

    el.itemBody.innerHTML = '<p style="color:var(--text-muted)">載入內容中…</p>';
    fetch(item.file, { cache: "no-store" })
      .then(function (r) { return r.text(); })
      .then(function (text) {
        var body = text.replace(/^---[\s\S]*?---\s*/, "").trim();
        el.itemBody.innerHTML = window.marked ? window.marked.parse(body) : escapeHtml(body);
      })
      .catch(function () {
        el.itemBody.innerHTML = '<p style="color:var(--text-muted)">內容載入失敗。</p>';
      });

    el.reader.scrollTop = 0;
  }

  function renderImages(item) {
    el.itemImageWrap.innerHTML = "";
    var images = (item.images && item.images.length) ? item.images : (item.image ? [item.image] : []);
    if (!images.length) {
      el.itemImageWrap.hidden = true;
      return;
    }
    el.itemImageWrap.hidden = false;
    el.itemImageWrap.classList.toggle("gallery", images.length > 1);
    images.forEach(function (src) {
      var img = document.createElement("img");
      img.src = "assets/" + src;
      img.alt = item.title;
      img.loading = "lazy";
      img.addEventListener("click", function () { openLightbox(img.src, item.title); });
      el.itemImageWrap.appendChild(img);
    });
  }

  function openLightbox(src, alt) {
    el.lightboxImg.src = src;
    el.lightboxImg.alt = alt || "";
    el.lightbox.classList.add("open");
  }
  function closeLightbox() {
    el.lightbox.classList.remove("open");
    el.lightboxImg.src = "";
  }
  el.lightbox.addEventListener("click", closeLightbox);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeLightbox();
  });

  function escapeHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function escapeAttr(s) {
    return escapeHtml(s);
  }
})();
