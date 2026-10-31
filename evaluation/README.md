# Project outcome evaluation

These small projects exercise actual application behavior in addition to installer tests. They are
fixtures for maintaining this toolkit, not automatic starters or proof that every skill/model will
produce the same quality. Normal users need only the Python toolkit and their coding agent.

## What was evaluated

| Scenario | Origin | Actual checks |
|---|---|---|
| Funky HTML event directory | Independent agent using START-HERE and selected skills | Keyboard filters/reset, empty state, no-JS fallback, 1280/390/320px layouts, contrast |
| Business PHP member directory | Same independent forward-test | PHP lint, real HTTP search, no-JS form, input escaping, malformed/oversized input, layouts and contrast |
| Editorial Next.js session directory | Authored runtime fixture in an initialized project | Production build, browser filtering/empty state/keyboard reset, desktop/mobile rendering, browser errors |
| Funky WordPress shortcode | Authored plugin in an initialized project | Real WordPress activation, shortcode counts, escaped attribute output, browser rendering |

The independent test used sequential roles and self-review; it did not have access to the parent
chat's intended fixes. Its findings led to clearer task transitions, review handoff guidance,
correct catalog wording and useful recovery when search returns no matches.

Windows local runtime evidence: PHP 8.5.10, Next.js 16.4.3, React 19.3.1, WordPress 7.1.4,
SQLite integration 3.1.2 and Playwright 1.64.1/Chromium. Next/React and browser dependencies have
lockfiles. WordPress archives are pinned by version and SHA-256. Review versions before changing them.

## Reproduce

Run from the toolkit checkout. Install only the optional test dependencies:

```bash
cd evaluation
npm ci --ignore-scripts
npx playwright install chromium
cd fixtures/nextjs
npm ci --ignore-scripts
npm run build
cd ../../..
php -l evaluation/fixtures/member-directory/index.php
node evaluation/forward-checks.cjs
python evaluation/setup-wordpress.py --directory .local/wordpress-evaluation
node evaluation/browser-checks.mjs --next evaluation/fixtures/nextjs --wordpress .local/wordpress-evaluation/wordpress --output .local/browser-outcomes
```

PHP with PDO SQLite is needed for WordPress. If the extension is available but not loaded, the
setup helper loads it for its process and reports `phpSqliteFlagRequired: true`; add
`--php-sqlite load` to the browser command too. No global PHP configuration changes are made.
Linux may require Playwright's `install --with-deps chromium` for browser system libraries.
`PHP_BINARY` and `PLAYWRIGHT_MODULE` optionally select existing test tools for forward-checks.cjs.
Use `--php` / `--playwright` for browser-checks.mjs. Output directories and tool paths stay local.

The WordPress helper refuses nonempty/linked destinations. It downloads only the pinned official
archives, verifies their hashes, creates a disposable SQLite site, suppresses mail/external HTTP
and generates a local random administrator password that is never printed. Do not reuse this
fixture as production configuration. Browser servers bind loopback and stop when checks complete.
Ports 8766/8767 and 8851/8852 must be free. Logs/screenshots/results stay under ignored `.local/`.

CI repeats the helper tests on Windows and Ubuntu, and these application checks on Ubuntu.
A missing runtime is a failed/unavailable check, not a pass. The browser checks do not constitute
cross-browser, screen-reader, physical-device, complete accessibility or production security audits.
No real member data, external service, authentication flow or live deployment was used.

## Repeat a fresh AI evaluation

Give a fresh agent START-HERE.md and one scenario brief above, with an empty external destination.
Ask it to implement the useful minimal application, fill its design contract, test the behavior,
and write a short handoff note. Keep its scope isolated. Compare actual behavior and rendered output with
the brief; record instructions it could not follow. Do not provide prior findings as hints.

All fixture application code is original toolkit evaluation work. The WordPress plugin is
GPL-2.0-or-later (license included); other fixture code follows the repository's MIT license.
Downloaded WordPress/plugin runtime code is not bundled in the repository.
