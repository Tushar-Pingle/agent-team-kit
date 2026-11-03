# {{ROLE_TITLE}} test 1: find planted accessibility defects

## Task

Review this candidate list screen with the `design-review` skill. It is a Frontend PR (not your work). Write your review as `review.md` in your output folder.

```html
<style>
  body { font-family: system-ui; background: #ffffff; color: #1a1a1a; }
  .hint { color: #a0a0a0; font-size: 13px; }
  button:focus { outline: none; }
  .status-pass { color: #2e7d32; } .status-fail { color: #c62828; }
  .icon-btn { width: 16px; height: 16px; padding: 0; }
</style>
<h1>Candidates</h1>
<p class="hint">Select up to 3 candidates to compare.</p>
<table>
  <tr><th>Name</th><th>Total</th><th>Status</th><th></th></tr>
  <tr><td>Demo A</td><td>72</td><td><span class="status-pass">●</span></td>
      <td><button class="icon-btn"><svg viewBox="0 0 16 16"><path d="M2 8h12"/></svg></button></td></tr>
  <tr><td>Demo B</td><td>41</td><td><span class="status-fail">●</span></td>
      <td><button class="icon-btn"><svg viewBox="0 0 16 16"><path d="M2 8h12"/></svg></button></td></tr>
</table>
```

## Known good result

`DESIGN: CHANGES NEEDED` with these planted defects:

1. `.hint` text #a0a0a0 on #ffffff has a contrast of about 2.6:1 (fails 1.4.3, needs 4.5:1).
2. The icon buttons have no accessible name (4.1.2).
3. `outline: none` removes the visible focus (2.4.7).
4. Status uses color only, a dot with no text (1.4.1).
5. The icon buttons are 16 by 16 px, below the 24 by 24 px minimum (2.5.8).

Other true findings are fine (for example: raw hex values instead of tokens, no table headers scope, no caption).

## Pass criteria

| # | Level | Check |
|---|---|---|
| 1 | must | The first line is `DESIGN: CHANGES NEEDED`. |
| 2 | must | It finds at least 4 of the 5 planted defects. |
| 3 | must | Each finding has the place, the WCAG criterion or reason, and a fix. |
| 4 | must | It does not write or change code. It reports only. |
| 5 | should | It finds all 5 planted defects. |
| 6 | should | It names the raw hex values (tokens only). |
| 7 | should | It ends with a work-log line. |
