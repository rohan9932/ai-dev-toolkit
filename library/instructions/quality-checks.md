# Evidence for the current milestone

Choose checks that establish the requested behavior. Record exact commands, results and limits
in docs/HANDOFF.md; a test count or a screenshot alone is not proof of a working application.

- HTML/CSS: serve the real page; exercise links, forms and keyboard navigation; inspect narrow
  and desktop layouts, long content and focus. Check labels, contrast and reduced motion.
- PHP: run PHP syntax checks and project tests; exercise the rendered route with valid and invalid
  input; verify output escaping and persistence where used. A lint pass is not an integration test.
- WordPress: run PHP checks and the relevant project detector; activate the plugin/theme in a
  disposable WordPress site and exercise its actual user path. Check permissions, nonces and escaping
  when relevant. If no WordPress runtime exists, report integration testing as unavailable.
- Next.js/React: use the repository's package manager and locked dependencies, run its build and
  tests, then exercise the running page. Inspect browser errors and server/client boundaries.

For every visible UI, compare the running application with the agreed preview and design contract.
Capture the representative page at a narrow and desktop width; test empty/error/success states
when those states exist. Inspect the rendered result, not only the source. No UI means no visual gate.
Keep a small issue list: requirement, observed result, evidence location, remaining correction.
After corrections, rerun affected checks. Do not report checks you could not run as successful.
