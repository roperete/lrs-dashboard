# UI/UX review 2, 2026-09-26 (v2.9.20, rechecked on v2.9.21)

Scope: the live staging build at https://roperete.github.io/lrs-dashboard/staging/, checked against the 25 findings of [the first review](ui-ux-review-2026-09-25.md). I used headless Chrome 153 with software WebGL at 1440×900, 1280×800 and 390×844 (touch emulation), plus a second Chrome with WebGL disabled. Screenshots are in [`ui-review-2-2026-09-26/`](ui-review-2-2026-09-26/).

v2.9.21 went live during the review (one tooltip per hover, a Sources column in the Moon table, clearer References cells, three more lunar samples checked). I rechecked every new problem below on v2.9.21. They are all still there.

The repo's crash scenarios (`scripts/crash/*.json`) all pass against the live build, with no page errors. They don't catch the problems below, because they check that the page doesn't crash, not what it shows.

Priority and effort use the same scale as the first review: P0 = broken, P1 = core flow, P2 = navigation and structure, P3 = quality floor; S = hours, M = a day or two, L = more.

## Summary

**Scorecard:** 12 fixed, 11 partly fixed, 1 not fixed, 1 made worse.

**Top new problems**

1. The 2D Earth map shows no pins at its default zoom, or after Reset View. You have to zoom in once to see any (N1).
2. When the suggested lunar sample has no values to show, the pane and the lunar comparison show a column of dashes, while the selector says "No reference comparison" (N2).
3. The Figures of Merit table cuts off its Score column at every width (N3).
4. The lunar comparison cites the lunar values but not the simulant values. The phone list shows values with no citation marks (N4).
5. Citation popovers run off the screen near the right edge. On a phone, a tap jumps to the reference list, so you never see the page or the quote (N6).
6. The compare tray overlaps the Find pane. On a phone it squashes into a four-line block (N8).
7. The table's sticky Name column lets the cells scrolling under it show through, and with both panes open the table shows no number columns at all (N9, N10).
8. In Table view, keyboard users reach the filters only after tabbing through all 148 rows. The closed Find pane stays focusable off screen (N14).

---

## Scorecard

| # | Finding | Status | Evidence |
|---|---|---|---|
| 1 | Search, Country sort and Reference filter blank the app | Fixed | Searched "JSC", `(*[?\`, "zzzz" and sorted every column. No errors. An error boundary shows a message instead of a blank page ([29](ui-review-2-2026-09-26/29-no-webgl-1440.jpg)). |
| 2 | Comparison: "+" on every Δ, missing shown as 0.00 | Fixed | Δ is labelled "A − B", signed with a real minus, and "—" when either side is missing. The note says "—" is not zero ([19](ui-review-2-2026-09-26/19-comparison-two-signed-delta-1440.jpg)). |
| 3 | Right panel covers the view switch, Go to and Export | Fixed | A fixed 56 px top bar holds every control. The panes start below it ([05](ui-review-2-2026-09-26/05-pane-clear-of-top-bar-1440.jpg)). |
| 4 | Table: pane wins, no row expansion | Fixed | Row click, Enter and ↑/↓ open the pane and update the URL. Chem, Miner and Refs cells open the pane at that section. The checkbox only adds to the tray. The table narrows for the pane. New problems in N9 and N10. |
| 5 | Left pane becomes "Find" | Partly | See below. |
| 6 | One compare tray | Fixed | Pane button, table checkbox and list checkbox all feed one tray of 2 to 4. It is kept across views and in `cmp=`. The hidden compare mode is gone. New problems in N8. |
| 7 | Comparisons drop citations | Partly | See below. |
| 8 | Lunar reference carries over | Fixed | JSC-1A suggests Apollo 14. LHS-1, opened next, suggests none. The note says the suggestion comes from the producer. New edge case in N2. |
| 9 | Pane is 7 screens and opens on the wrong part | Partly | See below. |
| 10 | Citations hard to follow and hover-only | Partly | See below. |
| 11 | Uppercase corrupts units and names | Fixed | µm, g/cm³ and kPa render correctly, and names appear as written. "<1mm" no longer gets "µm" appended. |
| 12 | DOIs with brackets break | Fixed | `10.1061/(ASCE)GT.1943-5606.0000068` links in full. One leftover in the small-things list (ALRS-1 ref 1). |
| 13 | No shareable links | Fixed | `planet`, `view`, `sim`, `cmp`, `f` and `site` are in the query string. A reload restores the pane, the tray, the chips and the ranges ([28](ui-review-2-2026-09-26/28-shared-link-restored-1440.jpg)). Back steps through selections, and filter changes don't add history entries. Leftovers in the small-things list. |
| 14 | Header and map chrome | Partly | See below. |
| 15 | Maps: pin meaning, selection | **Worse** | The legend now explains pins and types, rotation is off, and the attribution is right. But the 2D Earth map shows no pins at the default zoom (N1). That came with the Equal Earth map in v2.9.19, after the first review. |
| 16 | Table layout | Partly | See below. |
| 17 | Export drops provenance | Fixed | A long-format CSV: each value with its reference number, reference, DOI or URL, location and quote, plus reference rows and Figures of Merit ([26](ui-review-2-2026-09-26/26-export-menu-1440.jpg)). In a 71-simulant export, every oxide, mineral, property and FoM row has a reference, as do 146 of 413 identity rows. Export is hidden on the Moon. |
| 18 | The Moon is an island | Partly | See below. |
| 19 | Pin button does nothing | Fixed | Removed. |
| 20 | Contrast | Partly | See below. |
| 21 | Keyboard and screen readers | Partly | See below. |
| 22 | Information only on hover | Not fixed | Column definitions, property definitions and FoM explanations are still hover/focus tooltips (`Tooltip.tsx` says "pure CSS"). Phones have no "i" button and no inline text. |
| 23 | Phone | Partly | See below. |
| 24 | Loading, error and empty states | Fixed | No forced splash (the top bar is drawn after about 1.8 s). Views that are still loading show "Loading the view…" in place. The error boundary offers Try again and Reload. Empty states offer "Clear filters", and Help lives in the top bar ([27](ui-review-2-2026-09-26/27-help-1440.jpg)). |
| 25 | Consistency | Partly | See below. |

### What is still open in the partly fixed findings

- **#5 Find pane.** Done: open by default at 1280 px and wider, a drawer on phones ([35](ui-review-2-2026-09-26/35-phone-find-drawer-390.jpg)), and a chip under the bar when the pane is closed ("2 filters · 3 of 148 · Clear", [04](ui-review-2-2026-09-26/04-closed-pane-filter-chip-1440.jpg)). Chips show counts, and there are four ranges and a one-line list. Table view has no list, and the Moon has Missions with programme chips ([22](ui-review-2-2026-09-26/22-moon-globe-missions-1440.jpg)). Open: two scroll areas stacked in one pane, with the count and "Clear all" out of view (N11). "More filters" is the old control set (N12). Chips reorder and vanish as you type (N13). There is no collapsed rail in Table view, and hovering a list row doesn't highlight its marker.
- **#7 Comparisons.** Done: every value in the tray comparison is cited. There is a classification note, the physical properties are included, and the comparison opens on Table ([18](ui-review-2-2026-09-26/18-comparison-three-1440.jpg)). The lunar comparison uses the detailed minerals and drops the partial Total. Open: the simulant side of the lunar comparison has no marks (N4). Clicking a mark in a comparison does nothing. One mineral splits into two rows by capital letter (N5).
- **#9 Pane.** Done: sticky jump links (the current one is bold), the recommended section order, a compact About list with empty fields hidden, Type as the subtitle, and references behind "Show all 17". JSC-1A is now 4,308 px tall, down from 6,308. Open: the FoM table cuts off the scores (N3), and there is no overall score and no "Show all 14".
- **#10 Citations.** Done: each [n] is a button whose label names the document. Hover and focus show the document, the location and the quote. Click jumps to the reference and highlights it ([09](ui-review-2-2026-09-26/09-citation-click-jumps-1440.jpg)). About says "Values without a mark are not yet traced to a document" ([06](ui-review-2-2026-09-26/06-pane-about-1440.jpg)). Moon values are cited. Open: the popover leaves the screen near the right edge. A tap on a phone never shows the quote. There is no way back to the value, and marks inside comparisons do nothing (N6). Citations are still amber, the same colour as the lunar box, the [L n] marks and negative Δ in the lunar comparison.
- **#14 Header.** Done: the bar has a solid backdrop, so the title reads on the Moon map ([25](ui-review-2-2026-09-26/25-moon-map-1440.jpg)), and switching planet keeps the view. Home shows the whole globe, the view switch reads "Globe | Map | Table", Earth has its own icon, and "Go to a place" is in the map toolbar. Open: the phone bar has no product name and the logo sits under the planet toggle (N16, [33](ui-review-2-2026-09-26/33-phone-landing-390.jpg)). The control groups jump about 120 px sideways when you switch Earth ↔ Moon, because Export disappears on the Moon (compare [01](ui-review-2-2026-09-26/01-landing-find-pane-1440.jpg) and [22](ui-review-2-2026-09-26/22-moon-globe-missions-1440.jpg)).
- **#16 Table.** Done: Name is sticky, sorting uses buttons with `aria-sort`, the pane toggle is in the bar, and the selection bar is gone. Open: the sticky column lets cells show through (N9). There are still 16 data columns over 1,936 px. The first screen shows only identity columns, Name to Year, with no numbers ([10](ui-review-2-2026-09-26/10-table-identity-columns-first-1440.jpg)). There is no column picker or grouping, and "Lunar ref." still mostly repeats Type.
- **#18 Moon.** Done: "Simulants that replicate this site" (Apollo 11 lists MLS-1, MLS-1P and MLS-1A; clicking one opens it on Earth, [43](ui-review-2-2026-09-26/43-phone-moon-site-390.jpg)). Samples sort as numbers, the coordinates take one small line, "Chang'e" is spelled one way, and values are cited ([23](ui-review-2-2026-09-26/23-moon-site-panel-1440.jpg)). Open: the site panel has no returned-sample chemistry and no "compare a simulant with this site's sample". The Moon table can't be sorted or opened by keyboard, and on phones it stays a 1,160 px sideways table (N17).
- **#20 Contrast.** Small text now passes almost everywhere I measured. The exception is the inactive "Groups" toggle, at 3.07:1 and 10 px. But 218 text elements in the table-and-pane view are still 10 px (badges, marks, toggles), and tracked uppercase labels remain.
- **#21 Keyboard.** Done: rows take focus and open with Enter, ↑/↓ move the selection, sort buttons work, icon buttons have `aria-label`s, Escape closes the pane and Help, and the list no longer nests a button in a button. Open: see N14 and N15.
- **#23 Phone.** Done: the Earth table is a list ([39](ui-review-2-2026-09-26/39-phone-table-list-uncited-390.jpg)), Export no longer floats over rows, and the sheet has jump links and drag-to-close ([36](ui-review-2-2026-09-26/36-phone-sheet-390.jpg)). Open: the list's values have no citation marks (N4). The header, the tray and the comparison sheet all overflow (N8, N16). Touch targets are still small (N15).
- **#25 Consistency.** Done: one empty mark ("—"), Table first everywhere, and "Compare with a lunar sample" in the pane and Help. Open: role colours still differ between views. The simulant is blue in the lunar comparison but emerald as "A" in the tray comparison, and Δ is amber/blue in one and blue/green in the other ([15](ui-review-2-2026-09-26/15-lunar-comparison-simulant-uncited-1440.jpg), [19](ui-review-2-2026-09-26/19-comparison-two-signed-delta-1440.jpg)). The `--color-*` tokens in `index.css` are still unused. There are four names for clearing filters ("Clear", "Clear all", "Clear All Filters", "Clear filters"). Moon dates mix formats ("July 20, 1969" and "1 June 2024, 22:23:16 UTC").

---

## New problems

### Broken or misleading

**N1. The 2D Earth map shows no pins (P0, S–M).** Open Map. The marker layer is empty at the default zoom: 0 elements, and still 0 with a two-simulant filter. One zoom-in shows 28 markers and clusters, and Reset View empties the map again ([20](ui-review-2-2026-09-26/20-earth-map-no-pins-1440.jpg), [21](ui-review-2-2026-09-26/21-earth-map-pins-after-zoom-in-1440.jpg)). The Moon map is fine (19 markers). Map is the view the no-WebGL message sends people to, so without WebGL you get an empty map. The likely place to look is the cluster group with the Equal Earth CRS at zoom ≤ 2 (`LeafletMap.tsx:140`). Add a scenario that counts `.leaflet-marker-pane` children.

**N2. A suggested sample with no values gives empty comparisons (P1, S).** BH-1's producer names Apollo 16, but Apollo 16 is not among the selector's options, so the selector reads "No reference comparison". The chemistry table still has an "Apollo 16" column of dashes. The note still says "Suggested from the lunar sample the producer says…". The Mineral section shows "verified against source" over an empty table. "Full comparison" opens BH-1 against Apollo 16 (60501), with every lunar value and every Δ "—" ([13](ui-review-2-2026-09-26/13-bh1-empty-apollo16-column-1440.jpg), [14](ui-review-2-2026-09-26/14-bh1-lunar-comparison-all-dashes-1440.jpg)). Suggest only samples that have values to show, drive the selector, the table and the button from one state, and hide the "verified" note when there is nothing to verify.

**N3. The FoM table cuts off its scores (P1, S).** The table is 445 px wide inside a 384 to 399 px box with `overflow: hidden`, so the Score header and the scores ("0.35 (scale not stat…", "84 / 1…") are clipped at 1440, 1280 and 390 px ([07](ui-review-2-2026-09-26/07-pane-fom-score-clipped-1440.jpg), [38](ui-review-2-2026-09-26/38-phone-fom-clipped-390.jpg)). Put "Against" under the property name, or let the table scroll.

**N4. Values shown without citations (P1, S).** In the lunar comparison, JSC-1A's 46.67, 15.79 and the rest carry no [n], while the lunar side carries [L2] ([15](ui-review-2-2026-09-26/15-lunar-comparison-simulant-uncited-1440.jpg)). The phone list prints "ρ 1.295 g/cm³ · φ 37.67 °" with no marks, and a space before the degree sign ([39](ui-review-2-2026-09-26/39-phone-table-list-uncited-390.jpg)). Both break the per-value provenance rule, and the changelog says every compared value is cited.

**N5. One mineral, two rows (P1, S).** The tray comparison lists "Glass-rich basalt" (JSC-1A) and "Glass-rich Basalt" (LHS-1) as different components ([19](ui-review-2-2026-09-26/19-comparison-two-signed-delta-1440.jpg)). Match names without regard to case.

**N6. Citation popover: off screen, and unreachable on touch (P1, M).** Hovering [13] in the pane at 1440 px draws the popover to x = 1551 in a 1440 px window ([08](ui-review-2-2026-09-26/08-citation-hover-off-screen-1440.jpg)). `Tooltip.tsx` positions with CSS only. On a phone, a tap jumps straight to reference 13. The popover opens where the mark was, now 4,600 px up, so the page and quote are never seen ([37](ui-review-2-2026-09-26/37-phone-citation-tap-jumps-390.jpg)). After the jump, focus stays on the off-screen mark, and nothing leads back to the value. Replace the tooltip with a popover that opens on click or tap, stays inside the window, and holds the document, the location, the quote, the link and "Go to reference n".

**N7. Mixed sources on one card (P2, S).** JSC-1A's "Composition data source" card names the Characterization Summary [11], but the minerals below cite Coker et al. 2026 [17]. Reference 1 carries the badge "composition source" too. Either name each table's source, or drop the card.

### Layout and overlap

**N8. The compare tray covers the Find pane (P2, S).** The tray is centred on the window and moves only for the right pane (`CompareTray.tsx:28`), so it sits over the Find pane at 1440 and 1280 px ([17](ui-review-2-2026-09-26/17-tray-over-find-pane-1440.jpg), [31](ui-review-2-2026-09-26/31-table-pane-tray-1280.jpg)). On a phone, `left: 50%` halves its width, and it wraps into a 195 px, four-line block over the list ([40](ui-review-2-2026-09-26/40-phone-tray-390.jpg)). Centre it in the content area, and make it a full-width bar on phones.

**N9. The sticky Name column shows what scrolls under it (P2, S).** Scroll the table sideways and fragments of other cells appear in the gaps beside Name ("le", "to", "are", "nar ref.") ([11](ui-review-2-2026-09-26/11-table-sticky-name-bleed-1440.jpg), [45](ui-review-2-2026-09-26/45-table-scrolled-right-1440.jpg)). Give the sticky cells an opaque background and close the gap between the checkbox and Name.

**N10. With both panes open, the table shows no numbers (P2, M).** It is 621 px wide at 1440 and 476 px at 1280, which fits Name, Type and Country ([12](ui-review-2-2026-09-26/12-table-with-both-panes-1440.jpg), [31](ui-review-2-2026-09-26/31-table-pane-tray-1280.jpg)). Put the value columns right after Name, or add the column picker from #16.

**N11. The Find pane scrolls in two places (P2, S).** At 1440×900 the filters get 506 px and the list 304 px, each with its own scrollbar. The "148 of 148" count and "Clear all" sit at the end of the filter area, out of view, and "More filters" is cut in half at the boundary ([01](ui-review-2-2026-09-26/01-landing-find-pane-1440.jpg)). Use one scroll, and put the count and Clear at the top of the list.

**N12. "More filters" is the old panel (P2, S–M).** Its menu repeats the chips (type, availability, has chemistry, the four ranges) and shows system words ("CATEGORICAL", "BOOLEAN", "RANGE", "TEXT"). It opens clipped inside the filter area. An empty filter counts as one ("More filters (1)"), and it adds a big orange "Clear All Filters" button ([02](ui-review-2-2026-09-26/02-more-filters-menu-clipped-1440.jpg), [30](ui-review-2-2026-09-26/30-more-filters-old-controls-1440.jpg)). Keep only what the chips lack (country, institution, mineral, oxide, lunar sample, reference, year), in the same style as the chips.

**N13. Chips move while you filter (P3, S).** Typing a minimum bulk density moved Mare from first to second place, and the chips with zero counts vanished ([03](ui-review-2-2026-09-26/03-chips-reorder-count-hidden-1440.jpg)). Keep a fixed order, and show 0 in a muted style instead of removing the chip.

**Also:** the comparison sheets are fixed at 80 vh (`ComparisonPanel.tsx:114`, `CrossComparisonPanel.tsx:64`). The table and pane headers stay visible and clickable above them, with no backdrop, and each table inside has its own scrollbar ([18](ui-review-2-2026-09-26/18-comparison-three-1440.jpg)). Make the sheet a full-height dialog under the top bar. At 1280 px with both panes open, the map toolbar and the legend cover about 40 % of the 510 px map ([32](ui-review-2-2026-09-26/32-globe-both-panes-1280.jpg)).

### Accessibility

**N14. Tab order and hidden focus (P2, S).** In Table view, the search box is tab stop 743 of 768, after every row. There is no skip link and no `main` landmark. When the Find pane is closed, its 322 controls stay focusable off screen at x = −320. Mark the closed pane `inert`, put the Find pane before the table in the DOM, and add a skip link.

**N15. Dialogs, headers and targets (P2, M).**
- Help is `aria-modal`, but focus stays on the Help button, Tab moves behind the dialog, and closing it sends focus to the page body.
- The comparison sheets are not dialogs at all.
- Each column header is two tab stops (the tooltip span and the sort button).
- Touch targets are small: citation marks are about 20 × 10 px, Find list checkboxes 13 px, chips 26 px high, header buttons 40 × 36.
- Nothing honours `prefers-reduced-motion`: the cluster rings still pulse and the panes spring.

### Phone

**N16. The phone header and comparison overflow (P2, S).** The "LRS Database" title is squeezed to 0 px, the logo sits under the planet toggle, and the Find button shrinks to 20 px ([34](ui-review-2-2026-09-26/34-phone-header-overlap-390.jpg)). In the comparison, the close button sits half off screen (x 369–409 of 390), the sheet scrolls sideways, and "Δ A − B" wraps onto four lines ([41](ui-review-2-2026-09-26/41-phone-comparison-close-cut-390.jpg)).

**N17. The Moon table on phone and keyboard (P2, M).** Site, Mission and Program say nearly the same thing across three columns, and the site name wraps to three lines ([24](ui-review-2-2026-09-26/24-moon-table-1440.jpg)). The headers are not buttons and the rows can't take focus. On a phone it stays a 1,160 px sideways table ([42](ui-review-2-2026-09-26/42-phone-moon-table-390.jpg)).

### Selection, state and fallbacks

**N18. Nothing shows the selected simulant on the globe or map (P2, S–M).** Neither view receives the selected id (`App.tsx:314-333`). After you pick JSC-1A, the globe shows nothing different at its site ([05](ui-review-2-2026-09-26/05-pane-clear-of-top-bar-1440.jpg)).

**N19. The no-WebGL fallback is a dead end (P2, S).** The message is honest, but it says "Something on this page failed", keeps the globe toolbar, and gives no "Open the map" button ([29](ui-review-2-2026-09-26/29-no-webgl-1440.jpg)). The map it points to has no pins (N1). Check for WebGL before loading the globe, and start on Map when it is missing.

### Performance (P3, M)

- The landing page loads about 1.5 MB of app and data: three.js 500 KB, `countries.geojson` 282 KB, the CNES logo PNG 249 KB, `data.json` 164 KB.
- On top of that come about 2 MB of Earth textures from unpkg. The Moon adds a 4.6 MB texture hot-linked from raw.githubusercontent.com, which the GPU resizes from 11469×5734 to 8192×4095.
- Table view still downloads the countries file and the chart library.
- On a phone, the hidden desktop table stays in the page next to the list: 5,185 DOM nodes and 170 tooltips.
- Fix: self-host and shrink the textures, load the geojson only for Map, and render one table layout per breakpoint.

### Small things (P3, S each)

- The URL keeps `site=A15` after you switch to Earth. Malformed values (`sim=NOPE`, `bulk_density:a..b`) stay in the address with no message, and `?sim=S999` silently opens nothing.
- The page title never changes, so bookmarks and history entries all read "Lunar Regolith Simulant Database". Each ↑/↓ in the table adds a history entry.
- The export's file name (`lrs_filtered_2026-09-25.csv`) doesn't record which filters produced it. Reference rows reuse `value_as_stated` for "names this simulant".
- ALRS-1 reference 1 links to a DOI that its stored text cuts short (`…5525.000042`). The stored `doi` is `…0000428`, which the export uses. The pane should prefer the stored field.
- A fifth tray checkbox stays enabled and silently does nothing.
- The lunar comparison chart cuts off mineral labels ("gglutinates", "-magnetite", [16](ui-review-2-2026-09-26/16-lunar-comparison-chart-labels-cut-1440.jpg)).
- Scrollbars are drawn light on the dark UI, because `color-scheme` is not set to dark ([10](ui-review-2-2026-09-26/10-table-identity-columns-first-1440.jpg)).
- Help says "Every value carries a mark" (About fields don't) and that Export downloads "the current simulant" (that is the pane's download icon).
- On the splash, the CNES logo is dark blue on near-black ([44](ui-review-2-2026-09-26/44-loading-splash-1440.jpg)).
- Unconfirmed: in headless Chrome the numbers on globe cluster badges sit off-centre in their rings ([01](ui-review-2-2026-09-26/01-landing-find-pane-1440.jpg)). Check in a normal browser.

---

## Design notes

- The citation mark should be the one thing this product is known for. Today it is a 10 px amber bracket that shares its colour with the Moon, the lunar box and negative Δ. Give it its own colour, a 24 px tap target, and a real popover (N6).
- Tracked uppercase labels ("PHYSICAL PROPERTIES", "SOURCES FOR APOLLO 14 14163", "COMPOSITION DATA SOURCE", "DATA SHEET") and the one green word in the title ("Database") are stock template touches. Sentence-case headings would match the rest of the interface.
- Numbers use a monospace face. Tabular figures in the interface font would align just as well and read better.
- Many cards hold a single number (Specific Gravity, D50, PSD). A two-column definition list would show the same values in less height, which matters most in a 450 px pane.

## What to do next

1. **Map pins (N1).** Fix the empty 2D map and add a scenario that counts pins at the default zoom and after Reset View. S–M.
2. **Lunar suggestion (N2).** Suggest only samples with values, and use one state for the selector, the table and the button. S.
3. **Provenance gaps (N4, N5, N7).** Cite the simulant side of the lunar comparison and the phone list values, merge rows that differ only in case, and fix the composition-source card. S.
4. **Citation popover (N6, #10).** A click or tap opens a popover that stays in view, with the document, the location, the quote, the link and "Go to reference n". Larger target, its own colour. M.
5. **FoM table (N3).** Fit it in the pane at every width. S.
6. **Overlaps (N8, N9, N16, comparison sheet).** Move the tray, fix the sticky Name column, fix the phone header and the comparison close button, and make the comparison a full-height dialog. S each, about a day in all.
7. **Keyboard (N14, N15, N17).** Tab order and skip link, `inert` on the closed pane, one tab stop per header, focus in dialogs, and a keyboard-usable Moon table. M.
8. **Find pane (N11–N13).** One scroll, the count and Clear on top, More filters reduced to the missing filters, and a stable chip order. M.
9. **Table (N10, #16).** Put the value columns first or add a column picker, and give the Moon table a phone list. M.
10. **Globe and map (N18, N19, #15).** Selection ring, reduced motion, and a WebGL check that starts on Map. S–M.
11. **Consistency (#25).** Colour tokens per role, one name for clearing filters, one date format, and `color-scheme: dark`. S–M.
12. **Performance.** Self-hosted, smaller textures, the geojson loaded only for Map, one table layout on phones. M.

Add a check to the crash suite for each fix in items 1–6, so the scenarios test what the page shows and not only that it survives. For example: count the pins, require a mark on every compared value, check that the FoM table fits its box, and check that the tray doesn't overlap either pane.
