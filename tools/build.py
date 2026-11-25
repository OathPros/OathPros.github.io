"""Validate the approved public catalogue and render the static homepage."""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {
    "apps": "Applications & platforms",
    "artist": "Artist websites",
    "tools": "Tools",
    "institutional": "Institutional prototypes",
    "presentations": "Interactive presentations",
    "experiments": "Experiments",
}
HOSTS = {"github-pages", "cloudflare", "custom", "standalone"}
REQUIRED = {"id", "title", "description", "category", "topics", "launch", "hosting"}
OPTIONAL = {"source", "featured", "preview", "update", "state"}
STATES = {"Prototype", "Archived"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def is_text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def is_https(value):
    if not is_text(value) or re.search(r"[\s\\]", value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and url.username is None and url.password is None
                and url.port in (None, 443) and url.hostname is not None
                and bool(re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z0-9-]+", url.hostname)))
    except ValueError:
        return False


def validate(projects):
    check(isinstance(projects, list) and projects, "Expected a non-empty project list")
    ids, slots, topic_names = set(), set(), {}
    for item in projects:
        check(isinstance(item, dict), "Each project must be an object")
        id = item.get("id")
        check(REQUIRED <= item.keys() <= REQUIRED | OPTIONAL, f"{id}: invalid fields")
        check(isinstance(id, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", id)
              and id not in ids, f"{id}: invalid or duplicate identifier")
        ids.add(id)
        check(all(is_text(item[key]) for key in ("title", "description")), f"{id}: missing text")
        check(item["category"] in CATEGORIES, f"{id}: invalid category")
        check(item["hosting"] in HOSTS, f"{id}: invalid hosting type")
        launch = item["launch"]
        check(launch is None or is_https(launch), f"{id}: invalid launch URL")
        check(launch is None or urlsplit(launch).hostname != "github.com",
              f"{id}: use a project experience for launch and a separate source URL")
        if "source" in item:
            source = item["source"]
            check(is_https(source) and re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+/?", source),
                  f"{id}: source must be an approved GitHub repository URL")
        topics = item["topics"]
        check(isinstance(topics, list) and topics and all(is_text(t) for t in topics),
              f"{id}: invalid topics")
        check(len({t.casefold() for t in topics}) == len(topics), f"{id}: duplicate topic")
        for topic in topics:
            check(topic == topic_names.setdefault(topic.casefold(), topic),
                  f"{id}: inconsistent topic spelling")
        if "state" in item:
            check(item["state"] in STATES, f"{id}: invalid development state")
        if "featured" in item:
            rank = item["featured"]
            check(launch and type(rank) is int and rank > 0 and rank not in slots,
                  f"{id}: invalid or duplicate feature order, or missing launch")
            slots.add(rank)
        if "preview" in item:
            preview = item["preview"]
            check(isinstance(preview, dict) and set(preview) == {"path", "width", "height", "alt"},
                  f"{id}: invalid preview")
            path = preview["path"]
            check(path == f"assets/previews/{id}.webp" and (ROOT / path).is_file(),
                  f"{id}: missing or invalid preview path")
            check(is_text(preview["alt"]) and all(type(preview[k]) is int and preview[k] > 0
                  for k in ("width", "height")), f"{id}: missing alt text or dimensions")
        if "update" in item:
            update = item["update"]
            check(isinstance(update, dict) and set(update) == {"date", "evidence"},
                  f"{id}: invalid update object")
            stamp, evidence = update["date"], update["evidence"]
            check(is_text(stamp) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp)
                  and date.fromisoformat(stamp) <= date.today(), f"{id}: invalid update date")
            source = item.get("source", "").rstrip("/")
            check(source and is_https(evidence)
                  and re.fullmatch(re.escape(source) + r"/commit/[0-9a-f]{40}", evidence),
                  f"{id}: link a verified commit on the approved source repository")


def launch_link(project, class_name):
    title = escape(project["title"])
    if not project["launch"]:
        return title
    return (f'<a class="{class_name} hit" href="{escape(project["launch"])}">'
            f'{title}</a>')


def feature(project, layout):
    preview = project.get("preview")
    image = ""
    if preview:
        priority = 'fetchpriority="high"' if layout == "lead" else 'loading="lazy"'
        image = (f'<img {priority} width="{preview["width"]}" height="{preview["height"]}" '
                 f'src="./{escape(preview["path"])}" alt="{escape(preview["alt"])}">')
    category = escape(CATEGORIES[project["category"]])
    treatment = "" if preview else " text-feature"
    return f"""        <article class="feature {layout}{treatment}" data-project="{project['id']}">
          <div class="feature-media">
            <span class="preview-type" aria-hidden="true">{escape(project["title"])}</span>{image}
          </div>
          <div class="feature-copy">
            <p class="category-label">{category}</p>
            <h3>{launch_link(project, 'feature-link')}</h3>
            <p class="summary">{escape(project["description"])}</p>
          </div>
        </article>"""


def more_features(projects):
    if not projects:
        return ""
    content = "\n".join(feature(project, "extra") for project in projects)
    return f'      <div class="work-more">\n{content}\n      </div>'


def row(project):
    title = escape(project["title"])
    category = escape(CATEGORIES[project["category"]])
    topics = "".join(f'<button type="button" data-topic="{escape(topic)}" hidden><span aria-hidden="true" class="topic-prefix">#</span>{escape(topic)}</button>'
                     for topic in project["topics"])
    source = (f'<a class="source" href="{escape(project["source"])}" '
              f'aria-label="Source for {title}">Source</a>'
              if "source" in project else "")
    update = project.get("update")
    updated = (f'<a class="update" href="{escape(update["evidence"])}" '
               f'aria-label="Source update for {title} on {update["date"]}">'
               f'<time datetime="{update["date"]}">{update["date"]}</time></a>' if update else "")
    state = " · " + escape(project["state"]) if "state" in project else ""
    availability = "" if project["launch"] else '<span class="unavailable">No public launch</span>'
    return f"""        <li class="project" data-category="{project['category']}" data-featured="{project.get('featured', '')}">
          <div class="row-title"><h3>{launch_link(project, 'row-link')}</h3><span class="category-label">{category}{state}</span></div>
          <div class="row-description"><p>{escape(project["description"])}</p><div class="row-topics">{topics}</div></div>
          <div class="secondary">{updated}{source}{availability}</div>
        </li>"""


def options(values):
    return "\n".join(f'            <option value="{escape(key)}">{escape(label)}</option>'
                     for key, label in values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate and check index.html is up to date")
    args = parser.parse_args()
    projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    try:
        validate(projects)
    except (ValueError, TypeError) as error:
        parser.exit(1, f"Catalogue error: {error}\n")
    featured = sorted((p for p in projects if "featured" in p), key=lambda p: p["featured"])
    projects.sort(key=lambda p: p["title"].casefold())
    topics = sorted({tag for p in projects for tag in p["topics"]}, key=str.casefold)
    template = Template((ROOT / "tools/index.template.html").read_text(encoding="utf-8-sig"))
    output = template.substitute(
        count=len(projects),
        features="\n".join(feature(p, "lead" if i == 0 else "side") for i, p in enumerate(featured[:3])),
        more_features=more_features(featured[3:]),
        categories=options((k, v) for k, v in CATEGORIES.items() if any(p["category"] == k for p in projects)),
        topics=options((topic, topic) for topic in topics),
        rows="\n".join(map(row, projects)),
    )
    output = "<!-- Generated by tools/build.py. Edit the template or catalogue. -->\n" + output
    index = ROOT / "index.html"
    if args.check:
        check(index.read_text(encoding="utf-8") == output, "index.html is stale. Run python tools/build.py")
    else:
        index.write_text(output, encoding="utf-8", newline="\n")
    print(f"{len(projects)} valid public projects, {len(featured)} featured.")


if __name__ == "__main__":
    main()
