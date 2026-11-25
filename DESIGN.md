# Design direction

The software laboratory pairs an editorial showcase with a working archive. Ink and deep purple anchor the collection. Orange identifies sections, links and focus. The projects supply their own color and texture.

## References and exploration

The live homepage and local baseline were rendered in Edge, along with Linear, Teenage Engineering, Vercel and Are.na. Linear's quiet controls and interface-led imagery, Teenage Engineering's close views of real objects, Vercel's disciplined typography and proportions, and Are.na's emphasis on collection and discovery informed the composition. Captures are local in .devkit/artifacts.

Three concepts used the same real project content at 1440 and 390 pixels. The archive made entries easy to scan but the previews read as tiny thumbnails. The search-first explorer had the fastest desktop path to filters, while the mobile flow pushed media below the first group of results. The editorial split gave the map a legible scale and let artist photography and a software canvas sit side by side. The final design uses that split above the archive's flat list and includes a direct index link in the masthead.

## System

- Consolas and monospace fallbacks across the experience, with a tighter display setting on large headings and relaxed body leading.
- Square edges and a full-width feature stage. Use spacing and subtle changes in surface color to group content. Violet and warm plum lighting give the page depth without visible dividers. The index uses fixed alignment for titles, descriptions and secondary links.
- The wide layout uses a lead spread, two companion entries and a smaller follow-on row. The tablet places the lead above companions. The phone returns companions to horizontal image-and-copy rows and puts search on its own line.
- Project titles are anchors with full-entry hit areas. Topic buttons and source links have their own focus and pointer targets. Filter changes update the result status and the shareable URL. A skipped-to index or main section receives normal browser focus.
- Short transitions reinforce hover and focus, with motion disabled per preference. Image dimensions and the stage ratio hold space for a typographic fallback.

## Interface copy and icons

- Omit sentence-ending punctuation from homepage headings, labels, summaries, descriptions and status messages
- Use clear text labels for navigation, project launches and source links without decorative arrow icons
- Keep punctuation within names and phrases where it carries meaning

## Review

The independent review identified cramped 768px companions and inconsistent index alignment for entries that omit a source link. The revised breakpoint and fixed source track address both. Mobile controls use 16px text to reduce focus zoom in iOS Safari. Compare the final screenshots to before-1440.png and before-390.png in the local evidence folder.
