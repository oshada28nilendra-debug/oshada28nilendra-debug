# Automatic GitHub analytics

The profile card refreshes daily around **05:17 Sri Lanka time**. GitHub may delay scheduled jobs. New public repositories and activity appear after the next successful run, rather than immediately.

The updater refreshes the public repository count, followers, following, past-year contributions and heatmap, primary-language distribution, and featured-project stars and forks. Featured projects remain curated. Languages are counts of non-fork repositories, not lines of code. Private repository names and code are never included.

For an immediate refresh, open **Actions → Update profile analytics → Run workflow** on `main`.

The workflow uses GitHub's temporary built-in token. No personal access token, API key, or extra Python package is required. It writes only `analytics.svg`, and commits only when the card changes. A failed data fetch leaves the previous card intact.

Run locally with Python 3.9 or later:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_analytics.py
```

If GitHub disables the schedule after prolonged repository inactivity, re-enable it in Actions. Check failed runs there if the displayed update date stops advancing.
