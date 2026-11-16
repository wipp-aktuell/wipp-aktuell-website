import datetime
import json
import os
import pathlib
import subprocess
from zoneinfo import ZoneInfo


def git_output(*args):
    return subprocess.check_output(
        ["git", *args],
        text=True
    ).strip()


def main():
    before = os.environ["BEFORE_SHA"]
    after = os.environ["AFTER_SHA"]

    changed = git_output(
        "diff", "--name-only", before, after,
        "--", "content/companies"
    ).splitlines()

    # Zeitpunkt des ausloesenden PagesCMS-Commits
    commit_time = datetime.datetime.fromisoformat(
        git_output("show", "-s", "--format=%cI", after)
    ).astimezone(ZoneInfo("Europe/Berlin"))

    published_at = commit_time.strftime("%Y-%m-%dT%H:%M")

    for name in changed:
        path = pathlib.Path(name)

        if path.suffix != ".json" or not path.is_file():
            continue

        try:
            current = json.loads(path.read_text(encoding="utf-8"))

            try:
                previous = json.loads(
                    git_output("show", f"{before}:{name}")
                )
            except subprocess.CalledProcessError:
                previous = {}

            # Nur die erstmalige Veroeffentlichung erfassen.
            if (
                current.get("published") is True
                and previous.get("published") is not True
            ):
                current["date"] = published_at
                path.write_text(
                    json.dumps(
                        current, ensure_ascii=False, indent=2
                    ) + "\n",
                    encoding="utf-8"
                )
                print(f"Veroeffentlicht: {name} um {published_at}")

        except (ValueError, TypeError) as exc:
            print(f"Datei uebersprungen: {name}: {exc}")


if __name__ == "__main__":
    main()
