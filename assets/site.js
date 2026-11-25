"use strict";

const form = document.querySelector("#filters");
const list = document.querySelector("#grid");
const resultCount = document.querySelector("#result-count");
const empty = document.querySelector("#empty");
const search = form.elements.namedItem("q");
const category = form.elements.namedItem("category");
const topic = form.elements.namedItem("topic");
const view = form.elements.namedItem("view");
const controls = [search, category, topic, view];

function normalize(text) {
  return text.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase();
}

for (const image of document.querySelectorAll(".feature-media img")) {
  image.addEventListener("error", () => { image.hidden = true; });
  if (image.complete && !image.naturalWidth) image.hidden = true;
}

const projects = [...list.children].map((row) => {
  const tags = [...row.querySelectorAll("[data-topic]")];
  for (const tag of tags) tag.hidden = false;
  return {
    row,
    category: row.dataset.category,
    featured: Number(row.dataset.featured),
    updated: row.querySelector("time")?.dateTime ?? "",
    tags,
    searchText: normalize(
      row.querySelector(".row-title").textContent + " " + row.querySelector(".row-description").textContent
        + " " + tags.map((tag) => tag.dataset.topic).join(" ")
    ),
  };
});

const orders = {
  "": projects,
  featured: [...projects].sort((a, b) => a.featured - b.featured),
  recent: [...projects].sort((a, b) => b.updated.localeCompare(a.updated)),
};

function readAddress() {
  const params = new URLSearchParams(location.search);
  for (const control of controls) {
    control.value = params.get(control.name) ?? "";
    if (control instanceof HTMLSelectElement && control.selectedIndex === -1) control.value = "";
  }
}

function writeAddress() {
  const url = new URL(location.href);
  for (const control of controls) {
    if (control.value.trim()) url.searchParams.set(control.name, control.value.trim());
    else url.searchParams.delete(control.name);
  }
  if (url.href !== location.href) history.replaceState(null, "", url);
}

function filterProjects() {
  const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
  if (list.dataset.view !== view.value) {
    for (const project of orders[view.value]) list.append(project.row);
    list.dataset.view = view.value;
  }

  let matches = 0;
  for (const project of projects) {
    const show = (!category.value || project.category === category.value)
      && (!topic.value || project.tags.some((tag) => tag.dataset.topic === topic.value))
      && (view.value !== "featured" || project.featured > 0)
      && (view.value !== "recent" || project.updated)
      && terms.every((term) => project.searchText.includes(term));

    project.row.hidden = !show;
    if (show) matches++;
    for (const tag of project.tags) tag.setAttribute("aria-pressed", tag.dataset.topic === topic.value);
  }

  const count = matches === projects.length
    ? `${matches} projects`
    : `${matches} of ${projects.length} projects`;
  if (resultCount.textContent !== count) resultCount.textContent = count;
  empty.hidden = matches > 0;
  list.hidden = matches === 0;
}

function applyFilters() {
  filterProjects();
  writeAddress();
}

search.addEventListener("input", applyFilters);
for (const control of [category, topic, view]) control.addEventListener("change", applyFilters);

form.addEventListener("submit", (event) => {
  event.preventDefault();
  applyFilters();
});
form.addEventListener("reset", (event) => {
  event.preventDefault();
  for (const control of controls) control.value = "";
  applyFilters();
  search.focus();
});

list.addEventListener("click", (event) => {
  const tag = event.target.closest("button[data-topic]");
  if (!tag) return;
  topic.value = topic.value === tag.dataset.topic ? "" : tag.dataset.topic;
  topic.focus();
  applyFilters();
});

window.addEventListener("popstate", () => {
  readAddress();
  filterProjects();
});

readAddress();
filterProjects();
form.hidden = false;
