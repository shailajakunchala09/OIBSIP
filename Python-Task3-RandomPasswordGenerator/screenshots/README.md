# Screenshots

This folder is where the real, working-application screenshots referenced
in the main `README.md` should be placed before you push to GitHub.

The development sandbox used to build this project has no display server
and no `tkinter` binary available, so screenshots could not be captured
automatically here — and no placeholder or stock images have been added
in their place.

## How to capture them yourself

1. Install dependencies: `pip install -r ../requirements.txt`
2. Run the app: `python ../app.py`
3. Capture each of the following (Windows: `Win+Shift+S`, macOS: `Cmd+Shift+4`,
   Linux: your screenshot tool or `gnome-screenshot`):

| File | What to capture |
|---|---|
| `01-dashboard.png` | The full dashboard right after launch, default (Strong) preset |
| `02-strong-password.png` | A freshly generated password with the strength meter showing "Strong" or "Very Strong" |
| `03-custom-options.png` | Custom preset with a few character-type toggles switched off |
| `04-strength-analysis.png` | The right-hand Security Analysis panel with entropy/category data visible |
| `05-password-history.png` | The bottom history panel with a few masked entries |
| `06-ambiguous-character-option.png` | The "Exclude ambiguous characters" toggle switched on, with its tooltip visible |
| `07-light-theme.png` | The full dashboard with the theme switch set to Light |
| `08-validation-state.png` | The error dialog/status triggered by an invalid state (e.g. only one character type selected) |

4. Save each PNG directly in this folder using the exact file names above —
   the main `README.md` already links to them by these names.

Keep any history passwords in your screenshots masked (the default state)
unless you intentionally reveal a throwaway demo password.
