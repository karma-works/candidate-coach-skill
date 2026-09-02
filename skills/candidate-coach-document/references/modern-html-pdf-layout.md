# Restrained Modern HTML/PDF Layout

Use this contract when producing the default modern CV or an online PDF cover letter. The goal is a distinctive, calm document that remains highly scannable, selectable, printable, and ATS-friendly.

## Required deliverables

- Keep the evidence-grounded Markdown as the factual source.
- Create a self-contained `.modern.html` file with inline CSS and no network dependencies.
- Print that HTML to a `.modern.pdf` final artifact.
- Use A4 pages unless the destination market or user requests another size.
- Keep a senior CV to no more than two pages and a cover letter to one page unless the user explicitly requests otherwise.

## Visual system

- Use a neutral sans-serif stack such as `Inter, "Helvetica Neue", Arial, sans-serif`; do not fetch web fonts.
- Use near-black body text, a muted slate secondary color, one restrained blue or teal accent, and white paper. Ensure normal text and meaningful rules meet WCAG AA contrast.
- Use a clear scale: name `30–36pt`, role line `12–15pt`, section labels `9–10pt` uppercase with letter spacing, body `9.3–10.2pt`, metadata `8.4–9.2pt`, and line height around `1.35–1.5`.
- Use thin rules, spacing, weight, and alignment for hierarchy. Avoid skill bars, headshots, rating dots, excessive icons, large colored sidebars, background textures, and decorative charts.
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
4. **Profile:** Use a concise two-to-four-line positioning statement. Give it breathing room, but do not turn it into a large hero block.
5. **Experience timeline:** Use a stable two-column structure with a narrow year/date column and a flexible content column. HTML tables are acceptable when conversion reliability matters. Keep employer/title prominent, metadata muted, and bullets compact.
6. **Technology and strengths:** Group evidence-backed items into short labeled rows rather than a keyword cloud.
7. **Lower sections:** Use two balanced columns for education, certifications, languages, selected projects, or interests when this improves page balance. Collapse to one column when content density or conversion reliability requires it.
8. **Continuation:** On page two, use a subtle name-and-role continuation header and preserve the same grid and margins.

## Cover-letter composition

- Reuse the CV typography, accent color, contact row, rules, and margins so the application reads as one system.
- Use a compact identity header rather than a large CV hero header.
- Follow it with the role/company subject line, salutation, three or four short evidence-led paragraphs, and a compact sign-off.
- For online applications, omit postal sender and recipient blocks unless required. Use the available page height deliberately; adjust spacing and line height before adding prose or reducing font size.

## Conversion and QA

1. Print the HTML with background graphics enabled and no browser-generated headers or footers.
2. Render the resulting PDF to images at a useful inspection resolution, such as 150 DPI or higher.
3. Inspect every page for alignment, clipping, awkward whitespace, orphan headings, unintended page breaks, repeated-header spacing, and conversion differences.
4. Extract text from the PDF. Confirm correct reading order and exact rendering of names, employers, dates, punctuation, links, and characters such as `&`, `<`, `>`, and accented letters.
5. Iterate on HTML/CSS until both the rendered pages and extracted text pass. Do not declare completion based only on successful file creation.
