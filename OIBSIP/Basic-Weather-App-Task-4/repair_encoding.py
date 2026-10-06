from pathlib import Path

files = [
    Path("templates/index.html"),
    Path("static/app.js"),
    Path("static/style.css"),
    Path("web_app.py"),
]

bad_markers = (
    "Ã", "Â", "â", "ð", "�"
)

def repair(text):
    for _ in range(4):
        before = sum(text.count(x) for x in bad_markers)

        try:
            candidate = text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break

        after = sum(candidate.count(x) for x in bad_markers)

        if after < before:
            text = candidate
        else:
            break

    return text

for path in files:
    if not path.exists():
        continue

    text = path.read_text(encoding="utf-8")
    fixed = repair(text)

    if fixed != text:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        print("REPAIRED:", path)
    else:
        print("NO CHANGE:", path)

print("")
print("MOJIBAKE REPAIR FINISHED")
