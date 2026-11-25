# Architecture and maintenance

The previous root homepage was a single HTML file with embedded CSS, project data and runtime markup generation. It rendered only 22 of 31 records while shipping all 31 to the browser, guessed most launch destinations from repo names, and used common CSS illustrations regardless of the actual project. There was no build or test suite. The root custom domain and subprojects use GitHub Pages or separate external hosts.

## Structure

- projects.json contains the approved public inventory and explicit destinations. GitHub Pages, Cloudflare and custom-domain records have verified launch URLs. Only explicitly approved GitHub repositories have source links. Hosting is an editorial field.
- tools/build.py validates the closed schema and generates index.html from tools/index.template.html. It escapes all text and URLs. GitHub Pages serves the resulting HTML directly. First paint and launch work without a fetch or script.
- assets/site.css holds tokens, feature compositions, archive rows and responsive rules. assets/site.js filters the existing DOM, manages query parameters and handles image errors.
- assets/previews contains the reviewed WebPs. The local staging folder .devkit/artifacts is ignored. Pages exclusions keep development utilities and documentation outside the site.
- CNAME remains in place. Query filters and in-page anchors need no router, redirects, backend or interception of subproject paths. Existing public root, favicon and #grid remain addressable.

## Run locally

```powershell
python tools/build.py
python -m http.server 8080 --bind 127.0.0.1
```

Open http://localhost:8080/. For local validation, use `python tools/build.py --check` and `node --check assets/site.js`. For browser checks, install Playwright in your Python environment, then use `python tools/browser-check.py --channel msedge` with the preview server running. On machines without that channel use `python -m playwright install chromium` and omit the channel option. Evidence is local.

## Add a project

1. Approve the project for public listing. Open the final public HTTPS destination in a clean browser. Confirm the actual app, demo or website is the one that launches. Confirm that any optional source repo is public and approved. Use `"launch": null` for approved archive entries without a public destination and omit their feature placement.
2. Add one record to projects.json with a unique kebab-case ID, concise title and description, an existing category, reusable topics, launch and hosting type. Omit source, update and state when there is no evidence or approval. Keep any nonpublic information out of the file entirely.
3. For selected work, set a positive unique `featured` order. The lowest order gets the wide feature. For source update browsing, add an ISO date and permanent link to the corresponding verified commit on the approved repository.
4. Run the build, check the generated HTML and open the new row in a local browser. Review catalogue changes, generated HTML and any new preview together.

## Regenerate previews

With Python Playwright and Pillow installed, run the capture tool against an approved destination using a fresh browser. Stage output under .devkit/artifacts and inspect it at full size. Choose the canvas, artwork or meaningful task state and keep account pages, private data and internal content outside the capture. Use selector, scroll or crop options when needed. Crop coordinates are left, top, right and bottom in captured pixels. For views requiring interaction, prepare the view in the browser and export the capture at equivalent dimensions.

```powershell
python tools/capture-preview.py 'https://example.org/' .devkit/artifacts/project-id.webp --channel msedge --scroll 200
```

After checking the image and confirming permission to display it, copy it to assets/previews/project-id.webp. Set preview.path, width, height and concise alt in the catalogue, then rebuild and check responsive crops. Omit preview for typographic fallback. Use the review copy and browser evidence locally.
