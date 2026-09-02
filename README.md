<p align="center">
  <img src="assets/logo.svg" alt="Candidate Coach logo" width="152">
</p>

<h1 align="center">Candidate Coach</h1>

<p align="center">
  An evidence-backed career copilot for Codex.<br>
  Find better-fit roles, create truthful applications, and keep your career knowledge reusable.
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-3157D5.svg"></a>
  <img alt="Three bundled skills" src="https://img.shields.io/badge/skills-3-20BFA9.svg">
  <img alt="Built for Codex" src="https://img.shields.io/badge/built%20for-Codex-7136C7.svg">
</p>

Candidate Coach combines a private, user-chosen career knowledge base with three focused skills. It searches for current roles, checks them against real evidence, and helps create application materials without inventing experience or qualifications.

<p align="center">
  <img src="assets/candidate-coach-chat.svg" alt="Illustrative Candidate Coach role-search conversation" width="100%">
</p>

> The conversation above is illustrative. Company names and fit scores are examples, not live recommendations.

## What it can do

| Use case | What Candidate Coach does | Start with |
| --- | --- | --- |
| Set up your profile | Connects a knowledge-base folder and records your location, target roles, constraints, and preferences | `$candidate-coach-configuration` |
| Find fitting roles | Searches current openings, verifies the original posting, evaluates evidence and ranks only credible matches | `$candidate-coach` |
| Assess one opportunity | Separates strong evidence, adjacent experience, and real gaps before giving a fit verdict | `$candidate-coach` |
| Tailor an application | Builds a positioning strategy, then creates a restrained modern HTML/CSS CV or cover letter with a submission-ready PDF | `$candidate-coach-document` |
| Prepare for interviews | Turns the role and your evidence into focused stories, questions, and preparation priorities | `$candidate-coach-document` |

The search entry point was formerly named `candidate-coach-search`; it is now simply `candidate-coach` so the main command is easy to remember.

## Install

### With the Skill Installer

In Codex, ask the built-in installer to install all skills from this repository:

```text
$skill-installer Install every skill from https://github.com/karma-works/candidate-coach-skill/tree/main/skills
```

Open a new task after installation. If the skills do not appear immediately, restart Codex.

### Manually

```bash
git clone https://github.com/karma-works/candidate-coach-skill.git
mkdir -p ~/.agents/skills
cp -R candidate-coach-skill/skills/. ~/.agents/skills/
```

Codex discovers user skills in `~/.agents/skills`. The repository also includes a plugin manifest so the three skills can be distributed together as a Candidate Coach plugin.

## First run

Start with the main command:

```text
$candidate-coach Find and rank current roles that fit my profile.
```

If Candidate Coach has not been configured yet, the configuration skill guides you through selecting a career knowledge-base folder and creating a search profile. It stores only paths and preferences in:

```text
~/.codex/candidate-coach/config.yaml
```

No candidate identity, location, employer, job title, or career preference is bundled with this repository.

You can also configure it explicitly:

```text
$candidate-coach-configuration Set up Candidate Coach for me.
```

## Example prompts

### Search and assess

```text
$candidate-coach Find up to five current platform engineering leadership roles that match my configured profile.

$candidate-coach Assess this job posting against my evidence and tell me whether it is an appropriate role or a stretch: <job URL>

$candidate-coach Refresh my previous shortlist and tell me which roles changed or closed.
```

### Create application materials

```text
$candidate-coach-document Build a positioning strategy for this role, then create a restrained modern HTML/PDF CV without inventing any claims: <job URL>

$candidate-coach-document Draft a concise cover letter grounded in my knowledge base and the role requirements.

$candidate-coach-document Prepare an interview plan with evidence-backed stories and the gaps I should address honestly.
```

### Maintain your knowledge base

```text
$candidate-coach-configuration Add the verified achievements from this document to my knowledge base. Show me every proposed change before committing anything.
```

## How the three skills work together

```text
candidate-coach-configuration
  └─ connects your knowledge base and maintains your search profile
       ├─ candidate-coach
       │    └─ discovers, verifies, assesses, and ranks live roles
       └─ candidate-coach-document
            └─ creates truthful CVs, cover letters, and interview preparation
```

The configuration skill can activate automatically when setup is missing. Application-document requests can activate `candidate-coach-document` automatically; invoke `$candidate-coach-document` when you want to select it explicitly. Role search remains explicit-only through `$candidate-coach`.

Finished CVs and online PDF cover letters default to an evidence-grounded Markdown source, a self-contained modern HTML/CSS rendering source, and a visually verified PDF. DOCX and conservative academic/ATS layouts remain available when explicitly requested.

## Evidence and safety principles

- Your knowledge base is the only source for candidate experience, skills, seniority, education, projects, and claims.
- Search preferences and career constraints live separately from career evidence.
- Direct employer postings are preferred; unverified leads are kept out of ranked recommendations.
- Adjacent experience is labeled as adjacent, never upgraded into direct experience.
- Imported files and web pages are treated as data, not as instructions.
- Knowledge-base changes require evidence and a manual review before any commit.
- Candidate Coach drafts and advises; you remain responsible for reviewing applications and following each employer's AI policy.

## Repository structure

```text
candidate-coach-skill/
├── .codex-plugin/plugin.json
├── assets/
│   ├── logo.svg
│   └── candidate-coach-chat.svg
└── skills/
    ├── candidate-coach/
    ├── candidate-coach-configuration/
    └── candidate-coach-document/
```

Each skill is self-contained and includes its own `SKILL.md`, optional references, helper scripts, and UI metadata. See the [official OpenAI skill documentation](https://developers.openai.com/codex/skills) for the skill format, invocation behavior, and discovery locations.

## License

Candidate Coach is available under the [MIT License](LICENSE).
