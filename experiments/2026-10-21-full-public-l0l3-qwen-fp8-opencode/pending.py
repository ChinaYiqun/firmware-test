"""Print the number of tasks that a frozen run would still execute."""

from pathlib import Path
import json
import sqlite3
import sys


run = Path(sys.argv[1]).resolve()
config = json.loads((run / "config.json").read_text(encoding="utf-8"))
planned = {f"opencode__{case['id']}__{repeat}"
           for repeat in range(1, config["repetitions"] + 1)
           for case in config["subset"]["cases"]}
complete = set()
database = run / "results.sqlite"
if database.is_file():
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        for task_id, payload in db.execute("SELECT task_id, payload FROM attempts"):
            if json.loads(payload)["status"] in {"scored_pass", "scored_fail", "no_submission", "timeout"}:
                complete.add(task_id)
print(len(planned - complete))
