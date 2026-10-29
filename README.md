# Field Notes

**Live:** https://lokis-space.github.io/field-notes/

A personal collection of guides, checklists and notes, hosted on GitHub Pages.

| Entry | Path |
|---|---|
| [Kingdom Come: Deliverance — Chronological Role-Play Quest Guide](https://lokis-space.github.io/field-notes/kcd1/) | `kcd1/` |

## Layout

```
index.html            home page (generated from src/guides.json)
kcd1/                 built KCD1 guide (installable, works offline)
src/
  guides.json         entries listed on the home page
  build_hub.py        builds the home page
  make_icons.py       draws the app icons
  fonts/              shared fonts (SIL OFL)
  kcd1/               KCD1 guide sources: data, analysis, build script, PWA files
build.sh              rebuilds everything
```

## Adding a new entry

1. Put its sources in `src/<slug>/` and build the output into `<slug>/` (any static `index.html` works).
2. Add an icon at `<slug>/icon-192.png`.
3. Add it to `src/guides.json`.
4. Run `./build.sh`, then commit.

## Rebuilding

```sh
python3 -m venv .venv && .venv/bin/pip install beautifulsoup4 pillow
./build.sh
```

## Credits

- The KCD1 quest order follows a community role-play timeline from r/kingdomcome. Quest links point to the [KCD Wiki](https://kingdomcomedeliverance.wiki.gg/). Guide text is original.
- Fonts: Bellefair, Alegreya and UnifrakturMaguntia, all under the SIL Open Font License 1.1.
- Kingdom Come: Deliverance is a trademark of Warhorse Studios. This is an unofficial fan guide.
