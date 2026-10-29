# Kingdom Come: Deliverance — Chronological Role-Play Quest Guide

**Live guide:** https://lokis-space.github.io/kcd1-quest-guide/

A single-page checklist for *Kingdom Come: Deliverance* (2018) with all four story DLCs, built on a Reddit role-play route. It has 114 location visits and 134 quests, each with steps, key choices, role-play notes and an Outcome / Tip / Immersion analysis.

- Your ticks are saved in the browser. **Filters → Export / Import** backs them up or moves them between devices.
- **Next** jumps to the next unticked quest, and the guide offers to resume where you left off.
- You can install it as an app (Add to Home Screen, or the install button in the address bar), and it works offline.
- A Markdown version is in [`KCD1_Quest_Guide.md`](KCD1_Quest_Guide.md).

## Rebuilding

```sh
python3 -m venv .venv && .venv/bin/pip install beautifulsoup4
.venv/bin/python src/build.py .
```

The guide content lives in `src/data.json`, `src/analysis.json`, `src/immersion.json` and `src/appendix.html`.

## Credits

- Quest order follows a community role-play timeline from r/kingdomcome.
- Quest links point to the [Kingdom Come: Deliverance Wiki](https://kingdomcomedeliverance.wiki.gg/). Guide text is original.
- Fonts: Bellefair, Alegreya and UnifrakturMaguntia, all under the SIL Open Font License 1.1.
- Kingdom Come: Deliverance is a trademark of Warhorse Studios. This is an unofficial fan guide.
