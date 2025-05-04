import os
import json
import difflib
from pathlib import Path
from github import Github

LOCALIZATION_PATH = Path("assets/base/assets/localization")
MAINTAINERS_FILE = Path("localization_maintainers.json")

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def compare_dicts(base, other):
    changes = []
    for key in base:
        if key not in other:
            changes.append(f"🆕 Key '{key}' added with text: \"{base[key]}\"")
        elif base[key] != other[key]:
            changes.append(f"✏️ Key '{key}' changed from \"{other[key]}\" to \"{base[key]}\"")
    return changes

def main():
    en_path = LOCALIZATION_PATH / "en.json"
    if not en_path.exists():
        print("No en.json found, exiting.")
        return

    changed_files = os.popen("git diff --name-only HEAD^ HEAD").read().splitlines()
    if "assets/base/assets/localization/en.json" not in changed_files:
        print("en.json not changed, exiting.")
        return

    en_data = load_json(en_path)
    maintainers = load_json(MAINTAINERS_FILE) if MAINTAINERS_FILE.exists() else {}

    changes_summary = []
    mentions = set()

    for file in LOCALIZATION_PATH.glob("*.json"):
        if file.name == "en.json":
            continue
        other_data = load_json(file)
        changes = compare_dicts(en_data, other_data)
        if changes:
            summary = f"### `{file.name}`\n" + "\n".join(changes)
            changes_summary.append(summary)
            mentions.update(maintainers.get(file.name, []))

    if not changes_summary:
        print("No relevant changes found in localized files.")
        return

    # Create issue
    issue_title = "🔤 Localization needs update"
    issue_body = (
        f"The base localization file `en.json` was updated. Please review the changes below:\n\n"
        + "\n\n".join(changes_summary)
        + "\n\n"
        + "CC: " + " ".join(mentions)
    )

    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPOSITORY")
    gh = Github(token)
    repo = gh.get_repo(repo_name)

    issue = repo.create_issue(
        title=issue_title,
        body=issue_body,
        assignees=[m.lstrip("@") for m in mentions if m.startswith("@")]
    )

    print(f"Issue created: {issue.html_url}")

if __name__ == "__main__":
    main()
