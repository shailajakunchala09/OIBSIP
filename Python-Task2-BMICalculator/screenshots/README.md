# Screenshots

This folder is where the actual screenshots go before the project is
submitted or pushed to GitHub. They need to be captured from the running
application - none are included here yet.

Suggested set (matches the images referenced in the main README):

1. `01-dashboard.png` - the dashboard with a user selected, empty form
2. `02-bmi-result.png` - a calculated BMI with the category badge and scale
3. `03-history.png` - the history page with a few saved records
4. `04-analytics.png` - the analytics page with the BMI/weight trend charts
5. `05-mobile-view.png` - the web dashboard at a narrow (mobile) width

How to capture them:

- **Desktop app**: run `python desktop_app.py`, add a user, calculate a
  BMI, then use your OS screenshot tool (Win+Shift+S on Windows,
  Cmd+Shift+4 on macOS) on the Dashboard, History and Analytics tabs.
- **Web app**: run `python app.py`, open `http://localhost:5000` in a
  browser, and screenshot the Dashboard, History and Analytics pages.
  For the mobile shot, use the browser's device toolbar (F12 → toggle
  device toolbar in Chrome) set to a phone width, or resize the window.

Keep the image dimensions reasonably consistent (e.g. crop to just the
browser/app window, not the full screen) so they look tidy side by side
in the README.
