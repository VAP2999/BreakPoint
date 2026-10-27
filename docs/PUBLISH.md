# Publish on GitHub

Suggested repository name: `breakpoint`.

Suggested description: Evidence-first browser testing with validated policy actions, independent replay, and executable regression tests.

Suggested topics: `python`, `playwright`, `ai-agents`, `testing`, `browser-automation`.

## GitHub CLI route

Run from the extracted `breakpoint` folder. Authenticate to your own account first with `gh auth login`. Check `gh auth status` before creating the repository.

```bash
git init -b main
git add .
git diff --cached --stat
git status --short
# Confirm .env, .openai, artifacts and live-run are absent from staged files.
git commit -m "Initial release: evidence-first browser testing"
gh repo create breakpoint --public --source=. --remote=origin --push
```

If `breakpoint` already exists, choose a different new name; do not overwrite an unrelated repository. Configure your Git author locally if Git requests it, using your GitHub name and preferred public or GitHub-provided no-reply email.

## Browser route

Create a new public repository named `breakpoint`. Upload the contents of this folder, preserving directories. The CLI route is preferable because browser uploads may omit dotfiles such as `.github/workflows/tests.yml`, `.gitignore`, and `.env.example`.

After publishing, wait for the Tests workflow to finish and address any failures before calling CI verified. Pin the repo on your profile. Add the Loom link near the top of README once recorded.

The existing ChatGPT-hosted preview is private; it is not a public recruiter demo. A public repository and Loom video can be shared independently. Making a GitHub repository public does not publish or change access to the hosted preview.

No source license is included yet. Choose one if you want to grant reuse rights; public visibility alone is not an open-source license.
