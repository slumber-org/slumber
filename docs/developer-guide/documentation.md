# Documentation guide

This page describes how SLUMBER documentation is written, organized, and maintained.

---

## Documentation stack

We use **MkDocs** to build and serve project documentation.

- Documentation source files live in the `docs/` directory
- Site navigation is defined in `mkdocs.yml`
- Pages are written in Markdown (`.md`)

---

## Main documentation sections

The documentation is organized into the following high-level sections:

- **Home**  
  High-level introduction to SLUMBER and its purpose.

- **Getting Started**  
  Minimal steps required to install dependencies and run the project for the first time.

- **User Guide**  
  Usage-focused documentation describing how to work with SLUMBER from a user perspective (e.g., running sessions, configuration, common workflows).

- **Developer Guide**  
  Information for contributors and developers, including documentation conventions, development setup, testing, and internal design notes.

- **About**  
  Project background, contributing guidelines, release notes, citation information, and references.

---

## Writing conventions

### File and folder structure
- Use **kebab-case** for file names (e.g., `installation-setup.md`)
- Place files in the appropriate subfolder under `docs/`

### Headings
- Use a single top-level heading (`#`) per page
- Use `##`, `###`, etc. for subsections

### Links
- Use **relative links** when linking between documentation pages
- Keep paths stable to avoid broken links

### Code blocks
- Use fenced code blocks with a language identifier where possible:

```python
def example_function():
    pass
```

### Style
- Keep pages focused and concise
- Prefer multiple small pages over one very long page
- Write in clear, direct language

---

## Adding a new documentation page
1. Create a new Markdown file in the appropriate subfolder under `docs/`
2. Add meaningful content
3. Add the page to the navigation in `mkdocs.yml`
4. Preview the documentation locally to verify formatting and links

To preview the documentation locally, run:

```bash
mkdocs serve
```
This starts a local development server at `http://127.0.0.1:8000` and automatically rebuilds the site when files change.

---

## API and reference documentation

Where appropriate, API and reference documentation should be generated automatically using **MkDocstrings**.

- Auto-generated reference documentation is intended to complement narrative documentation, not replace it.
- Public interfaces (e.g., classes or functions) are preferred candidates for auto-generation.