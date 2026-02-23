document.addEventListener("DOMContentLoaded", function () {
  // Collect all known tag names and counts for exact-match tag filtering
  const knownTags = new Set();
  const tagCounts = {};
  document.querySelectorAll(".tag-btn").forEach((el) => {
    const tag = el.textContent.trim().toLowerCase();
    knownTags.add(tag);
    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
  });

  // Append counts to filter buttons
  document.querySelectorAll(".tag-filter-btn").forEach((btn) => {
    const tag = btn.textContent.trim().toLowerCase();
    const count = tagCounts[tag] || 0;
    btn.textContent = btn.textContent.trim() + " (" + count + ")";
  });

  const filterItems = (searchTerm) => {
    searchTerm = searchTerm.toLowerCase();
    document.querySelectorAll(".bibliography, .unloaded").forEach((element) => element.classList.remove("unloaded"));

    const isTagFilter = knownTags.has(searchTerm);

    document.querySelectorAll(".bibliography > li").forEach((element) => {
      let match;
      if (isTagFilter) {
        // Exact tag match: only check rendered tag elements
        const tags = element.querySelectorAll(".tag-btn");
        match = Array.from(tags).some((t) => t.textContent.trim().toLowerCase() === searchTerm);
      } else {
        // Full-text search
        match = element.innerText.toLowerCase().indexOf(searchTerm) !== -1;
      }
      if (!match) {
        element.classList.add("unloaded");
      }
    });

    document.querySelectorAll("h2.bibliography").forEach(function (element) {
      let iterator = element.nextElementSibling;
      let hideFirstGroupingElement = true;
      while (iterator && iterator.tagName !== "H2") {
        if (iterator.tagName === "OL") {
          const ol = iterator;
          const unloadedSiblings = ol.querySelectorAll(":scope > li.unloaded");
          const totalSiblings = ol.querySelectorAll(":scope > li");

          if (unloadedSiblings.length === totalSiblings.length) {
            ol.previousElementSibling.classList.add("unloaded");
            ol.classList.add("unloaded");
          } else {
            hideFirstGroupingElement = false;
          }
        }
        iterator = iterator.nextElementSibling;
      }
      if (hideFirstGroupingElement) {
        element.classList.add("unloaded");
      }
    });
  };

  const updateInputField = () => {
    const hashValue = decodeURIComponent(window.location.hash.substring(1));
    document.getElementById("bibsearch").value = hashValue;
    filterItems(hashValue);
  };

  let timeoutId;
  document.getElementById("bibsearch").addEventListener("input", function () {
    clearTimeout(timeoutId);
    const searchTerm = this.value.toLowerCase();
    timeoutId = setTimeout(filterItems(searchTerm), 300);
  });

  window.addEventListener("hashchange", updateInputField);

  updateInputField();
});
