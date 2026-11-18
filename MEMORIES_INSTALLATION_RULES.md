# MEMORIES — PERMANENT INSTALLATION RULES

**User-approved mandatory rule — 18 November 2026**

## Updates do not work

- **NEVER send a Memories APK/link that requires updating an existing installation.**
- Never tell the user to tap **Update / Mettre à jour**.
- Every test or replacement APK must be clearly identified as a **new, separate installation** with a distinct Android `applicationId`, and must not overwrite any installed Memories app.
- **NEVER ask the user to uninstall Memories V3, clear its storage, or erase experiences or photos.**
- Before sharing any APK, inspect its `applicationId`, verify it does not collide with any known installed Memories version, and confirm that the build succeeded.
- When a package has been installed already, **do not distribute another APK with the same package ID as a purported update**, even if the version number increases. Use a distinct package ID for the next test build unless a reliable, explicitly approved upgrade path is established.
- Keep backups and existing installations intact. A new installation has separate private data and does **not** automatically migrate experiences or photos; never claim otherwise.
- Do not send workflow links or APK download links before confirming that the APK is meant for a new installation rather than an update.
- Clearly distinguish compilation success from testing on the user's Android tablet.
- This rule applies to **today and all future Memories work**.

## Current known package identities

- V3 test: `com.sofiamagalhaes.memories.v3test`
- First V4 test: `com.sofiamagalhaes.memories.v4`
- For a subsequent V4 test, choose a **new** `applicationId` rather than attempting to update `com.sofiamagalhaes.memories.v4`.

**Before shipping: check this file and explicitly confirm the package is a fresh installation.**
