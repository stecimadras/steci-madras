# St. Thomas Evangelical Church of India – Madras Parish website

## Publish on GitHub Pages (one-time setup)
1. Create a public GitHub repository named `st-thomas-madras-parish`.
2. Upload **all** files and folders from the ZIP to the repository root, including the hidden `.github/workflows/` folder and `scripts/` folder. In GitHub, use **Add file → Upload files** and ensure the folders are preserved. If the web upload omits the hidden `.github` folder, upload it using Git or GitHub's Create new file option.
3. In **Settings → Actions → General → Workflow permissions**, enable **Read and write permissions** for GitHub Actions, then Save. Some organizations prohibit this setting; ask the repository administrator if necessary.
4. In **Settings → Pages**, choose **Deploy from a branch**, `main`, `/(root)`.
5. The website will be at `https://YOUR-USERNAME.github.io/st-thomas-madras-parish/`.

## Update the bulletin for January–March 2027 and future quarters
1. Keep the PDF filename **exactly** `current-bulletin.pdf`.
2. In the GitHub repository, open `current-bulletin.pdf` and choose the replacement/upload workflow (or use Git to replace the file), then commit to `main`.
3. Open **Actions → Extract and publish bulletin data** and wait for a green successful run. The workflow reads the PDF and commits an updated `bulletin-data.json` and `bulletin-data.js`. GitHub Pages will then show the new period, birthdays, anniversaries, services, readings, and upcoming events. **No HTML editing is needed for supported layouts.**
4. **Check the website against the PDF**, especially every worship service and 31 December / quarter-end programme, after each new bulletin. PDF layout variations can change extraction behavior.
5. If the workflow shows **red / failed**, the new PDF format could not be reliably parsed. The previous data file remains unchanged; do not treat the website as updated. Open the workflow error, and have the extractor adapted to the new PDF layout before publishing it as current. The PDF itself will still have been replaced in the repository.
6. To preserve an old PDF, save a copy under `archives/YEAR/` before replacing it. The Archives list is regenerated automatically by the separate **Update archived newsletter list** GitHub Action whenever a PDF is added or removed under `archives/`. Check Actions for a successful run. Keep archived PDFs in `archives/YEAR/` and give them descriptive filenames such as `bulletin-jan-mar-2027.pdf`.

### Important limitations
- Automatic extraction has been **tested against the supplied November–December 2026 PDF**, not an unseen January–March 2027 PDF. The script expects a similar searchable-text layout and section labels. Scanned PDFs, redesigned bulletins, or unexpected formatting may fail and require a script update.
- The extractor does not invent missing fields. It fails when mandatory sections or readings cannot be found. Some optional fields might be omitted if the PDF format changes; human verification is still required.
- If you replace the PDF without enabling GitHub Actions, only the downloadable PDF changes; website programme data will **not** update.
- The website loads `bulletin-data.js`, so it also works when you double-click `index.html` locally. The extraction workflow generates both JSON and JS data files.

## Notifications
Edit `notifications.json` in GitHub and update `notifications-data.js` to match (or add an automation for notifications). Example:
```json
[{"date":"2027-01-01","title":"New Year greeting","message":"Wishing everyone a blessed new year."}]
```
The NEW badge blinks for seven days, then disappears while the announcement remains visible.

## Local extraction test
Install Python 3.12 and `pymupdf==1.26.5`, then run `python scripts/extract_bulletin.py` from the project folder. Check `bulletin-data.json` and compare it with the PDF.

## Date display
The site defaults to each visitor's local current date. Ordinal suffixes (1st, 2nd, 3rd, 11th, 12th, 13th, 21st, etc.) are generated automatically. The heading **Worship Service** and the site's visual theme are permanent.

## Offline preview and full worship schedule
Open `index.html` directly to preview the current bulletin: the generated bulletin data is embedded in the page. The full quarter's worship services are listed below the daily view. When you replace `current-bulletin.pdf` in GitHub, the workflow regenerates both the data files and the embedded HTML data. Check the Actions tab for success before assuming the site updated.

## Automatic archive listing
Upload old PDF newsletters to `archives/YEAR/` and commit the files to `main`. The **Update archived newsletter list** action updates the Archives section automatically without editing HTML. This also works when previewing `index.html` locally because the archive list is embedded. If it does not update, check GitHub Actions and ensure workflow write permissions are enabled.

### Year-wise Bulletin Archives
The Archives section shows clickable years (for example, 2026 and 2027). Select a year to expand its quarterly PDFs with Open PDF and Download PDF links. To add a year, upload a PDF to `archives/YYYY/` and commit; the Update archived newsletter list GitHub Action refreshes the archive index automatically. The year and PDF must exist in the archive before appearing on the website.
