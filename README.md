# Aegean Frescoes Atlas

Interactive map of Bronze Age Aegean frescoes (Minoan, Mycenaean, Cycladic), built with Leaflet.

## Project structure

```
aegean-frescoes-map/
├── index.html          # entry point
├── manifest.json        # PWA manifest (installable app metadata)
├── service-worker.js    # offline caching (app shell + viewed fresco images)
├── assets/
│   ├── css/style.css
│   ├── icons/           # app icons for install/home-screen use
│   └── js/
│       ├── data.js     # generated -- do not hand-edit, see Data pipeline below
│       └── app.js       # map logic: filters, clustering, popups
└── README.md
```

## Data pipeline

`data.js` is **generated**, not hand-written. The source of truth is a CSV spreadsheet, matching the schema documented in `frescoes-template.csv`.

1. Fill in / update `frescoes.csv` (one row per fresco)
2. Convert: `python3 csv_to_data.py frescoes.csv assets/js/`
   → writes `assets/js/data.js` and `assets/js/data.geojson`
3. Validate: `python3 validate_dataset.py assets/js/data.geojson`
   → checks for duplicate IDs, missing fields, out-of-range coordinates, missing image URLs/attribution
4. Fix anything flagged, re-run steps 2–3 until clean
5. Commit the updated `data.js` alongside your CSV changes

Never edit `assets/js/data.js` directly — regenerate it from the CSV instead, or your changes will be overwritten on the next conversion run.

## Local preview

No build step needed. Either:
- Open `index.html` directly in a browser, or
- Run a local server from the project root (needed in some browsers due to `file://` script restrictions):
  ```
  python3 -m http.server
  ```
  then visit `http://localhost:8000`

## Deployment (GitHub Pages, free)

1. Create a free account at [GitHub.com](https://github.com) if you don't have one
2. Create a new public repository (e.g. `aegean-frescoes-map`)
3. Push this project's files into the repository
4. In the repository, go to **Settings → Pages**
5. Under **Build and deployment → Branch**, select `main` and click **Save**
6. Within a minute or two, GitHub publishes the site at `https://<username>.github.io/aegean-frescoes-map/`

## Current status

- **12 of ~100 target frescoes** entered and validated (Minoan × 8, Mycenaean × 1, Cycladic × 3)
- **All 12** have confirmed real images (Wikimedia `Special:FilePath` redirect)
- Marker clustering, a legend that doubles as the culture filter, mobile-safe zoom control position, a fullscreen toggle, a search box with a results list, a timeline slider (filters by `dateStart`/`dateEnd` overlap, dual-thumb, 25-year steps), shareable permalinks (`#fresco-id` in the URL, updated on popup open, read on page load), offline support via a service worker and web app manifest (see below), an accessibility/mobile pass (see below), and an image lightbox (click or Enter/Space on a popup thumbnail to enlarge, requests a larger 1200px rendition from Wikimedia Commons where possible, closes on Escape/backdrop click/close button, returns focus to the thumbnail) are all live
- Not yet done: expanding toward the full dataset (12 of ~100 target frescoes so far)

## Recent usefulness improvements

- **Search now matches theme, culture, and description**, not just title/site/region -- searching "griffin" or "ritual" finds frescoes the old title-only search would've missed.
- **"Clear all filters"** button next to the frescoes count resets the culture filter, search, and the timeline range in one click; it's disabled (greyed out) whenever nothing is actually filtered.
- **Culture filter dropdown removed** -- the legend was doing the same job as a bigger, always-visible, tap-friendly control, so it's now the only way to filter by culture (still fully keyboard-operable). The unused theme dropdown was dropped too; theme is still searchable via the search box.
- **"Made by @philopalaia"** credit replaces the old "About this data" pipeline note in the sidebar.

## Offline support

- The app is an installable **PWA** (`manifest.json` + `service-worker.js`): browsers that support it will offer an "Install" / "Add to Home Screen" prompt, and the map keeps working with no network connection after the first visit.
- The service worker precaches the full app shell on first load -- `index.html`, `style.css`, `app.js`, `data.js`, and the Leaflet/MarkerCluster/Fullscreen libraries pulled from unpkg -- so the map, filters, and clustering all work offline immediately.
- Fresco **photos** (hosted on Wikimedia Commons) are cached opportunistically as you view them rather than precached up front, since there could eventually be ~100 of them. Anything you've opened once stays viewable offline afterwards; frescoes you haven't looked at yet will show a broken image until you're back online.
- Requires being served over `http://` or `https://` (e.g. `python3 -m http.server`, or a real deployment like GitHub Pages) -- service workers don't run against a plain `file://` page.

## Accessibility & mobile

- **Skip link** at the very top of the page jumps keyboard users past the sidebar straight to the map (which is itself keyboard-pannable via arrow keys and +/-, since Leaflet's keyboard handler is on by default).
- **Legend doubles as the culture filter**: each culture swatch is a real button (44px min tap target) that toggles that culture on/off, with a visible `aria-pressed` state.
- **"List all visible frescoes" toggle** in the search panel renders every currently-filtered fresco as a button list, independent of typing a search term -- the main way for keyboard/screen-reader users to reach a specific fresco, since individual map markers aren't natively keyboard-focusable.
- **Keyboard navigation in the results list**: Arrow Up/Down move between fresco buttons (wrapping at the ends), Home/End jump to first/last, Escape returns focus to the search box, and Down from the search box jumps straight into the first result.
- **Visible focus states** everywhere interactive: search input, timeline slider thumbs, legend buttons, result rows, all get a clear terracotta outline on keyboard focus (`:focus-visible`, not on mouse click).
- **`prefers-reduced-motion` respected**: Leaflet's own pan/zoom/marker animations are disabled and `goToFresco` jumps instead of animating for anyone with that OS/browser setting.
- **Timeline slider announces real years** to screen readers (`aria-valuetext`, e.g. "1450 BCE") instead of the raw negative integer.
- **Larger touch targets**: the search input and result rows are all a minimum 44px tall per WCAG guidance.
