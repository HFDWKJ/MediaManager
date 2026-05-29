Media Manager — portable data folder (dev / portal edition)
============================================================

When `portable.marker` exists beside the app, files are stored here:

- config.json — settings and library roots
- catalog.db — catalog database
- logs/ — application logs

These files are **not** committed to Git (see `.gitignore`).
Use Tools → Export database for backups.
