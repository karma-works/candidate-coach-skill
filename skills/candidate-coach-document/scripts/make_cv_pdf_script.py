#!/usr/bin/env python3
"""Create a project-local Pandoc CV-to-PDF script."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shlex


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv-md", required=True, help="Path to the CV Markdown file")
    parser.add_argument("--script", default="convert-cv.sh", help="Script path to write")
    parser.add_argument("--title", required=True, help="Evidence-backed candidate name for Pandoc title metadata")
    parser.add_argument("--subtitle", default="", help="Optional Pandoc subtitle metadata")
    parser.add_argument(
        "--allow-body-name-heading",
        action="store_true",
        help="Allow a Markdown body that starts with a duplicate candidate-name heading/contact line",
    )
    args = parser.parse_args()

    cv_path = Path(args.cv_md).expanduser().resolve()
    script_path = Path(args.script).expanduser()
    if not script_path.is_absolute():
        script_path = Path.cwd() / script_path
    script_path = script_path.resolve()

    if args.title and not args.allow_body_name_heading:
        first_content_line = next(
            (line.strip() for line in cv_path.read_text(encoding="utf-8").splitlines() if line.strip()),
            "",
        )
        normalized_title = re.sub(r"\s+", " ", args.title.strip())
        duplicate_name_pattern = re.compile(
            rf"^(?:#+\s*)?{re.escape(normalized_title)}(?:\s|$)", re.IGNORECASE
        )
        if normalized_title and duplicate_name_pattern.match(first_content_line):
            raise SystemExit(
                "Refusing to create a duplicate-name CV script: the PDF helper already "
                "renders the centered Pandoc title. Remove the leading Markdown/body "
                "candidate name line, or pass --allow-body-name-heading intentionally."
            )

    default_pdf = cv_path.with_suffix(".pdf")
    if script_path.parent == cv_path.parent:
        input_assignment = f'input_file="${{script_dir}}/{cv_path.name}"'
    else:
        input_assignment = f"input_file={shlex.quote(str(cv_path))}"

    metadata_lines = ""
    if args.title:
        metadata_lines += f"  --metadata title={shlex.quote(args.title)} \\\n"
    if args.subtitle:
        metadata_lines += f"  --metadata subtitle={shlex.quote(args.subtitle)} \\\n"

    content = f"""#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
{input_assignment}
output_file="${{1:-{default_pdf}}}"

# Homebrew BasicTeX installs TeX engines here, but new shells do not always
# pick it up until the PATH helper has been refreshed.
for tex_path in /Library/TeX/texbin /usr/local/texlive/*/bin/universal-darwin; do
  if [[ -d "$tex_path" ]]; then
    PATH="$tex_path:$PATH"
  fi
done

if ! command -v pandoc >/dev/null 2>&1; then
  echo "Error: pandoc is not installed or is not on PATH." >&2
  echo "Install it with: brew install pandoc basictex" >&2
  exit 1
fi

pdf_engine=""
for engine in xelatex lualatex pdflatex tectonic wkhtmltopdf; do
  if command -v "$engine" >/dev/null 2>&1; then
    pdf_engine="$engine"
    break
  fi
done

if [[ -z "$pdf_engine" ]]; then
  echo "Error: no Pandoc PDF engine found." >&2
  echo "Install one with: brew install basictex" >&2
  exit 1
fi

pandoc "$input_file" \\
  --from markdown \\
  --to pdf \\
  --pdf-engine "$pdf_engine" \\
{metadata_lines}  --variable geometry:margin=0.75in \\
  --variable fontsize=10pt \\
  --variable colorlinks=true \\
  --output "$output_file"

echo "Created $output_file"
"""

    script_path.write_text(content, encoding="utf-8")
    script_path.chmod(0o755)
    print(script_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
