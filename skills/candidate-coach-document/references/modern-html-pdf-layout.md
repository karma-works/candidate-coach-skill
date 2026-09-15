# Restrained Modern HTML/PDF Layout

Use this contract when producing the default modern CV or an online PDF cover letter. The goal is a distinctive, calm document that remains highly scannable, selectable, printable, and ATS-friendly.

## Required deliverables

- Keep the evidence-grounded Markdown as the factual source.
- Create a self-contained `.modern.html` file with inline CSS and no network dependencies.
- Print that HTML to a `.modern.pdf` final artifact.
- Use A4 pages unless the destination market or user requests another size.
- Keep a senior CV to no more than two pages unless the user explicitly requests otherwise. When a displacement-market word budget applies under `SKILL.md`, that budget governs and page fit alone does not satisfy it. A cover letter must fit one page and the 300-word limit defined in `SKILL.md`; page fit does not establish compliance with the word limit.

## Visual system

- Use a neutral sans-serif stack such as `Inter, "Helvetica Neue", Arial, sans-serif`; do not fetch web fonts.
- Use near-black body text, a muted slate secondary color, one restrained blue or teal accent, and white paper. Ensure normal text and meaningful rules meet WCAG AA contrast.
- Use a clear scale: name `30–36pt`, role line `12–15pt`, section labels `9–10pt` uppercase with letter spacing, body `9.3–10.2pt`, metadata `8.4–9.2pt`, and line height around `1.35–1.5`.
- Use thin rules, spacing, weight, and alignment for hierarchy. Avoid skill bars, rating dots, excessive icons, large colored sidebars, background textures, and decorative charts. Include a headshot only when the photo rule in `SKILL.md` calls for one, and then follow «Optional CV photo» below.
- Set print colors explicitly with `print-color-adjust: exact` and `-webkit-print-color-adjust: exact`.

## Page and CSS contract

Start from these print-safe rules and tune within the ranges to fit the content rather than shrinking text indiscriminately:

```css
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  color: #17212b;
  background: #eef1f4;
  font-family: Inter, "Helvetica Neue", Arial, sans-serif;
  font-size: 9.8pt;
  line-height: 1.42;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto 8mm;
  padding: 15mm 16mm 14mm;
  background: #fff;
  position: relative;
}
@media print {
  body { background: #fff; }
  .page { margin: 0; break-after: page; }
  .page:last-child { break-after: auto; }
  a { color: inherit; text-decoration: none; }
}
.section, .entry { break-inside: avoid; }
```

Use explicit `.page` containers so page breaks are intentional and repeat only a compact continuation header on later CV pages. Do not allow a section heading to remain at the bottom of a page without content beneath it.

## CV composition

1. **Identity header:** Set the given and family names in one content-sized, no-wrap inline or flex container. Differentiate them with weight or accent color, separated by one normal word space. Never use fixed offsets or proportional columns between the names.
2. **Target role:** Place the exact role title or a truthful seniority-preserving title immediately below the name. Keep broader positioning in a short subtitle or profile.
3. **Contact row:** Use one compact wrapping row for supported location, email, phone, portfolio, LinkedIn, and GitHub details. Use text labels or restrained inline symbols; preserve clickable links in the PDF.
4. **Profile:** Use a concise two-to-four-line positioning statement. Give it breathing room, but do not turn it into a large hero block. Label any profile-highlight section «Stärken für diese Stelle», «Profil für diese Stelle», or a natural equivalent in the application language. Do not insert the target employer name into that heading or its highlight labels.
5. **Experience timeline:** Use a stable two-column structure with a narrow year/date column and a flexible content column. HTML tables are acceptable when conversion reliability matters. Keep employer/title prominent, metadata muted, and bullets compact.
6. **Technology and strengths:** Group evidence-backed items into short labeled rows rather than a keyword cloud.
7. **Lower sections:** Use two balanced columns for education, certifications, languages, selected projects, or interests when this improves page balance. Collapse to one column when content density or conversion reliability requires it.
8. **Continuation:** On page two, use a subtle name-and-role continuation header and preserve the same grid and margins.

## Optional CV photo

Use this section only when `SKILL.md`'s photo rule applies. A photo is an identity element, not decoration: it belongs in the header and must not compete with the name, the target role, or the first evidence.

- Place the photo in the identity header, aligned with the name block — right-aligned on the header row is the safest default; a left position is acceptable when the name block then remains the dominant element.
- Size it between `24mm` and `32mm` on the long edge. It must not push the profile or the first experience entry onto a later page, and it never appears on a continuation page.
- Use a portrait or square crop with the face in the upper third. Crop with `object-fit: cover` and a fixed `width`/`height` so aspect ratio never distorts.
- Keep the treatment restrained: square with a small radius, or a circle. Use at most a hairline neutral border. No drop shadows, coloured rings, badges, or background cut-outs.
- Embed the file as a base64 `data:` URI in the HTML so the source stays self-contained; do not link a local or remote path.
- Give the `<img>` a plain `alt` value such as the candidate's name. Keep the photo out of the text reading order so ATS text extraction is unaffected.
- Set `print-color-adjust: exact` on the image container as for other printed colour, and confirm in the rendered PDF that the photo prints at full quality, is not clipped by the page margin, and does not shift the header baseline.

## Cover-letter composition

- Reuse the CV font family, restrained accent, contact treatment and margins so the application reads as one system. Adapt the hierarchy to a letter rather than copying CV profile panels or achievement cards.
- Use a compact identity header and a clear role/company subject line, followed by salutation, a focused argument and a compact sign-off.
- Keep the opening in the same type size, alignment and background as the other body paragraphs. It is the candidate's own motivation, not a quote, epigraph, annotation or executive-summary card. Do not add a left accent bar, quotation marks, shaded box or oversized lead styling just to make it stand out. Let its position and wording do that work.
- Use comfortable paragraph spacing and deliberate white space. Do not add prose to fill the page, shrink text to fit an overlong letter, or spread a short letter into an artificial full-page block.
- For online applications, omit postal sender and recipient blocks unless required.

### Visual elements must have a reading purpose

Choose a visual treatment only when its meaning is clear to a reader without explanation. These are practical defaults, not a requirement to use every element:

| Element | Purpose | Appropriate use and boundary |
|---|---|---|
| Prominent name and compact contact row | Identify the applicant and make contact easy | Keep the name content-sized with a natural word space; make contact details readable but secondary. |
| Bold role/company subject | Establish immediately what the document is for | One primary subject; avoid promotional slogans competing with the role title. |
| White space and paragraph separation | Make the argument and transitions easy to follow | Default treatment for motivation, evidence and closing; no need for boxes or labels around normal prose. |
| Selective bold within prose | Help a scanning reader find the decisive evidence | At most one or two short phrases in the letter, such as a relevant outcome. Do not bold entire paragraphs, every metric or generic self-praise. Omit if unnecessary. |
| Thin horizontal rule | Separate identity/contact information from the letter | Use sparingly at a genuine structural boundary; never to rank ordinary paragraphs arbitrarily. |
| Restrained accent color | Reinforce consistent identity and navigation across the application | Limit it to the name, subject or structural rules. Preserve hierarchy in grayscale; color must not be the only cue. |
| Small, readable metadata row | Separate logistics from the persuasive argument | Suitable for confirmed availability and contact details; no substantive evidence or overflow prose hidden here. |
| Labeled section or aligned date/content columns in a CV | Support comparison of roles and chronology | Appropriate for structured CV data; do not impose a dashboard or card layout on a personal letter. |
| Indented quote or quote-style side rule | Identify words spoken or written by someone else | Reserve for a real, relevant quotation with visible attribution and evidence. Normally unnecessary in a cover letter; never apply to the candidate's own opening. |
| Shaded callout with an explicit label | Distinguish genuinely separate supplementary information | Rarely needed in application documents. If the information belongs in the argument, use normal prose instead; never use an unlabeled callout as decoration. |

During visual QA, inspect the reading order without reading every word: the reader should recognize who is applying, for which role, where the argument begins and how to respond. For each highlight ask what distinction it communicates. Remove it if it could be mistaken for a quotation, external endorsement or supplementary note, or if it serves no clear purpose. Ensure the text retains its meaning when styling is removed.

## Conversion and QA

1. Print the HTML with background graphics enabled and no browser-generated headers or footers.
2. Render the resulting PDF to images at a useful inspection resolution, such as 150 DPI or higher.
3. Inspect every page for alignment, clipping, awkward whitespace, orphan headings, unintended page breaks, repeated-header spacing, and conversion differences.
4. Extract text from the PDF. Confirm correct reading order and exact rendering of names, employers, dates, punctuation, links, and characters such as `&`, `<`, `>`, and accented letters.
5. Verify the applicable word count from the extracted visible text using the shortening reference — the 300-word cover-letter limit, and the reduced CV budget when one applies — and inspect visual emphasis against the purposes above. When the CV carries a photo, confirm in the rendered pages that it is sharp, correctly cropped, unclipped, and absent from continuation pages. Iterate on HTML/CSS until both the rendered pages and extracted text pass. Do not declare completion based only on successful file creation.
