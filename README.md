# uzzu-guide

Converts Uzzu's JSON TV guide to XMLTV for TiviMate, every 3 hours, on GitHub Actions.

- Secret `UZZU_URL` = the M3U playlist URL (Settings → Secrets and variables → Actions). Never committed.
- Output: `https://raw.githubusercontent.com/<user>/uzzu-guide/guide/uzzu.xml.gz`, which holds only listings.
- Run by hand: Actions → Update guide → Run workflow. Local test: `UZZU_URL=... python3 make_guide.py out.xml.gz`
- GitHub pauses scheduled jobs in a repo with no activity for 60 days; it emails first. Re-enable from the Actions tab.
