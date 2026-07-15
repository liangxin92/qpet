# Usage Remaining as Pet HP

## Current decision

Do not enable a live Usage HP bar in the marketplace Skills-only release.

The current Codex app-server exposes `account/rateLimits/read` and `account/rateLimits/updated`, so a first-party or local client can read quota windows. The official Pet surface, however, exposes no plugin-controlled HUD, text, progress bar, custom state binding, or dynamic overlay slot. Its package metadata contains only pet identity, description, sprite version, and spritesheet path.

Skills run for a request and do not own a persistent UI or background process. Rewriting an installed atlas repeatedly would not be a reliable live display and could corrupt or stale-cache the pet. Patching ChatGPT, scraping logs, reading auth files, or injecting into the native overlay is forbidden.

`account/usage/read` reports historical token activity, not quota remaining, and must not be presented as HP.

## Future standalone companion mapping

If the user separately authorizes a local desktop companion application, derive HP from rate-limit windows only:

```text
remaining(window) = clamp(100 - usedPercent, 0, 100)
HP = minimum remaining value across active primary and secondary windows
```

Show the limiting window and its reset time. Use `--` when the data is unavailable. Label the value as approximate remaining quota, not money, tokens, or a guaranteed request count.

The companion must remain separate from the marketplace pet plugin and must:

- ask for explicit opt-in before reading rate limits
- start the documented local app-server itself or connect through a documented host channel
- call only `account/rateLimits/read` and subscribe only to `account/rateLimits/updated`
- keep raw responses in memory and never read `auth.json`, databases, logs, cookies, or tokens
- never send rate-limit or plan data to a remote server
- draw its own clearly labeled transparent window rather than claim to modify the official Pet HUD
- stop cleanly and remove its overlay when the user exits

Building that companion is a separate product decision because it adds a persistent process and account-related data handling outside the scope of this plugin.
