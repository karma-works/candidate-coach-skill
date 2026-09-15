# CV and Cover Letter Shortening Guidelines

Shortening should make the candidate's evidence clearer and more targeted, not merely smaller.

## CVs

1. Prioritize material that supports the application strategy and target role.
2. Compress older or less relevant roles into concise entries when detail no longer improves fit proof. Do not use a fixed year cutoff; derive it from the candidate's career stage and target.
3. Keep recent-role bullets selective, usually five or six at most. Prefer outcomes, decisions, scope, and evidence over routine duties.
4. Select projects aggressively. Keep only those that demonstrate target-role capability, business value, judgment, leadership, or another winning theme.
5. Remove implementation trivia that belongs in an interview. Retain technologies that establish credibility, but avoid keyword lists.
6. Place education according to career stage: usually later for experienced candidates and earlier for recent graduates when it is a main qualification.
7. Preserve career progression and avoid creating unexplained timeline gaps.
8. Unless local expectations or the user specify otherwise, target one page for early-career candidates and no more than two pages for experienced candidates.

### Word budget in a displacement market

When `SKILL.md` classifies the target as a displacement market, the page limit is not enough: set a measured word budget at **20 percent below the candidate's most recent full-length CV**, measured with the counting rule below, and treat it as a hard cap.

Apply the cover-letter discipline of focus before compression to the CV:

1. Name the two or three winning themes the CV must prove. Everything that does not serve them is a candidate for removal.
2. Remove whole items before shortening surviving ones: secondary projects, older or off-target roles, duplicated evidence across sections, technology inventories, and interests that add nothing to the case.
3. Only when every remaining item earns its place, compress within items: drop the weakest bullet of a role, cut qualifiers, incidental counts, tool lists, and explanatory detours. Preserve the evidence, the candidate's actual contribution, and the exact qualification of any metric.
4. Never buy space typographically. Reducing font size, line height, or margins, or moving prose into headers and captions, does not satisfy the budget.
5. Count the Markdown source and the rendered PDF separately after the final edit. Report the baseline, the cap, and both counts outside the document.

Preserve chronology, progression, and material gaps at every step. If the budget cannot be met without hiding a gap or dropping a required qualification, keep the truthful version, report the measured overshoot, and say what would have to go.

## Cover letters

### Focus before compression

The complete visible letter must contain **no more than 300 words**. A shorter, complete argument is preferable to filling that allowance. Plan around 220–260 body words to leave room for the subject, contact details and closing; this is a drafting aid, not an additional minimum or an exception to the total limit.

1. State the central reason to invite this candidate in one sentence in the working strategy. Select the employer-specific motivation and the one or two strongest pieces of evidence that support it.
2. Give each paragraph a distinct job: motivation and fit, evidence of relevant impact or judgment, and a concise closing. Usually three short paragraphs suffice; use a fourth only if it adds a distinct, necessary point.
3. When over the limit, remove an entire secondary theme, redundant example or CV recap first. Cut technology inventories, project background, routine responsibilities and generic enthusiasm that do not change the hiring case. Move useful detail to the CV or interview notes, not elsewhere in the letter.
4. If every paragraph remains essential, shorten within them: remove sentences that repeat a claim, incidental dates and counts, qualifiers, explanatory detours and introductory phrases. Replace abstract wording with concrete verbs. Preserve the evidence, the candidate's actual contribution and material qualifications of metrics; do not shorten an estimate into a measured fact.
5. Re-read for a coherent, natural argument, employer-specific motivation and consistent language. Do not produce telegraphic fragments or stack unrelated facts into long sentences to save words. Never invent enthusiasm or a reason for leaving.
6. Count again after the final wording and after rendering. Keep revising until both versions meet the cap; do not ask the user to waive it merely because all paragraphs seem valuable. Report the final total in the handoff, outside the application itself.

## Counting rule

This rule applies to any measured document limit in this skill: the cover-letter limit and the displacement-market CV budget. For a CV, count all visible text in the document — header, contact details, section headings, dates, employers, bullets, skills rows and footers.

Count all visible text in a single letter: name/contact header, date/address if present, subject, salutation, body, sign-off, availability and footer. Count the email subject too when supplied separately. Count each whitespace-separated token containing at least one letter or digit as one word; a hyphenated term, email address or URL without spaces is one token. Ignore punctuation-only tokens. Count link labels as displayed, not hidden Markdown/HTML link targets; do not count formatting markup. Normalize PDF line wrapping and join words split only by a line-end hyphen before counting. Do not count the source and PDF together: each must independently stay within the applicable limit. Do not manipulate spacing or hyphenation to reduce the count.

Use a programmatic count of plain visible text rather than estimating by eye. For example, after extracting and normalizing visible text in Python: `sum(any(c.isalnum() for c in token) for token in text.split())`.

A request for review alone does not authorize rewriting: flag a letter over 300 words as `must-fix`, identify the theme to remove first, and report its measured count.

## Final check

- The strongest relevant evidence appears before older or weaker evidence.
- No unsupported claim, metric, technology, motivation, or trait was introduced while rewriting.
- The document still explains progression, material gaps, and role fit.
- The language remains natural and consistent with the original application language.
- Any generated document has been rendered and visually checked.
