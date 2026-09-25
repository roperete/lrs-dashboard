# UI/UX review, 2026-09-25 (v2.9.17)

Scope: the staging build (v2.9.17) and the source at HEAD `1903359`. Line numbers refer to HEAD. I did not review the uncommitted work on the Moon panel and table, the 2D map, or drag-to-close; where it overlaps a finding, I say so. Screenshots are in [`ui-review-2026-09-25/`](ui-review-2026-09-25/). I took them in headless Chrome at 1440×900, 1280×800 and 390×844.

Each finding gives a priority (P0 = broken, P1 = core flow, P2 = navigation and structure, P3 = quality floor) and an effort (S = hours, M = a day or two, L = more).

## Top of the list

1. Typing in the search box, sorting the table by Country, or using the Reference filter turns the whole app into a blank screen (#1).
2. The comparison tables print "+" on every difference and show missing values as 0.00 (#2).
3. An open simulant or site panel covers the view switch, "Go to" and Export (#3).
4. Table: the right pane should win, and the row expansion should go (#4).
5. Left pane: turn it into a "Find" pane whose content changes with the view (#5).
6. Comparing two simulants from the pane is a dead end (#6), and the comparison views drop every citation (#7).
7. Citations can't be clicked, don't work on touch, and are missing from the identity fields (#10).
8. CSS uppercase turns "µm" into "ΜM" and "kPa" into "KPA" (#11).

---

## P0: broken

### 1. Search, Country sort and Reference filter blank the app (P0, S)

- **Where:** `src/utils/filterSimulants.ts:26-27` and `:121`; `src/components/table/SimulantTable.tsx:124`; `src/hooks/useFilters.ts:62`. Nothing wraps `App` in an error boundary (`src/main.tsx`).
- **What:** Lunar90, Lunar250 and Lunar2000 (added in v2.9.17) have no `type`, `country_code` or `availability`. Type "Apollo" or "J" in the search and the code calls `.toLowerCase()` on null. React unmounts and the screen goes black with no message ([19](ui-review-2026-09-25/19-search-crash-blank.jpg)). The same happens when you sort the table by Country (`getCountryDisplay(null)`) or type in the Reference filter (61 references have no `reference_text`). The Type filter also offers an empty option. None of the three simulants has a site, so they never appear on the globe or the 2D map.
- **Why it hurts:** search is the first thing a researcher tries. When the page dies, reloading is the only way back.
- **Do:** make the comparisons null-safe (`s.type ?? ''`, `getCountryDisplay(code ?? '')`, `r.reference_text ?? ''`). Add an error boundary that says what failed and offers a reload. Add a test that runs search, every sort, and every filter over the real `data.json`. Leave empty values out of the filter options.

### 2. Comparison: wrong signs, missing values shown as zero (P0, S)

- **Where:** `src/components/panels/ComparisonPanel.tsx:208` (Δ built from `'+'` and `Math.abs`), `:26`, `:35`, `:54` (`|| 0`); `CrossComparisonPanel.tsx:217` (same `'+'`, which the working tree fixes for this panel only).
- **What:** every Δ is printed with "+", and only the colour (green or blue) shows the direction. JSC-1A SiO2 46.67 against LHS-1 49.12 shows "+2.45" ([13](ui-review-2026-09-25/13-compare-delta-and-zeros.jpg)). A component the source does not report shows as "0.00" and is charted as a zero bar: Anorthosite 0.00 for JSC-1A, Fe2O3 0.00 for LHS-1.
- **Why it hurts:** a reader takes "+" to mean "higher", and colour-blind readers get no direction at all. "0.00" claims a measurement that doesn't exist, which breaks the "empty over wrong" rule.
- **Do:** print a signed Δ with a real minus ("−2.45") and label the column "A − B". Show "—" for a missing value, keep it out of the chart, and leave Δ empty whenever either side is missing.

### 3. The right panel covers the view switch, "Go to" and Export (P0, M)

- **Where:** `src/components/ui/PanelShell.tsx:33` (fixed, full height, `z-[1000]`); `src/components/layout/AppHeader.tsx:24-39` (absolute header, controls on the right); `src/App.tsx:433` (Export at the bottom right).
- **What:** whenever a simulant or site is open, the panel sits on top of the right half of the header. On Earth at 1440 px it covers 2D, Table and "Go to" ([02](ui-review-2026-09-25/02-panel-covers-header.jpg), [09](ui-review-2026-09-25/09-table-row-opens-pane.jpg)). On the Moon it covers all five header buttons ([20](ui-review-2026-09-25/20-moon-panel-covers-header.jpg)). At 1280 px with the left pane open, 2D and Table are covered ([17](ui-review-2026-09-25/17-1280-sidebar-and-panel.jpg)). Export sits under the panel at both widths.
- **Why it hurts:** the moment you look at a simulant is the moment you want to switch view ("show me this in the table"). Today you have to close the panel, switch, and select the simulant again.
- **Do:** make the header a fixed, full-width bar (about 56 px) and start both side panes below it. Move Export and Help into that bar. The header and the panes can then never overlap.

---

## P1: core flows

### 4. Table: two ways to see a simulant (owner question 1) (P1, M)

- **Where:** `SimulantTable.tsx:245-257` (row click opens the pane), `:276-306` (the Chem ✓, Miner ✓ and Reference cells expand the row), `:308-351` (the expanded row); `App.tsx:197` (the table's padding ignores the pane).
- **What is wrong with the expanded row:**
  - It repeats the pane with less in it: compositions without superscripts, unnumbered references, and a different number format (49.3% here, 49.30 in the pane) ([11](ui-review-2026-09-25/11-table-expanded-row.jpg)).
  - It spans the full 2,376 px table, so the chemistry values and the references land off-screen.
  - Its triggers (Chem, Miner, Reference) are the right-most columns, which sit under the pane whenever the pane is open ([09](ui-review-2026-09-25/09-table-row-opens-pane.jpg)).
  - Clicking a row and clicking a cell in that row do different things, and nothing shows it.
- **Answer:** the right pane wins. It is the only view that shows every value with its citation, plus the Figures of Merit, purchase details and references. Remove the inline expansion. The other controls change like this:

```
Row click, or Enter on a focused row  → select the row, open the pane
↑ / ↓                                 → move the selection; the pane follows
Checkbox                              → add to the compare/export tray only
Chem ✓ / Miner ✓                      → open the pane at Composition
Refs cell ("17 refs · 16 name it")    → open the pane at References
Opening the pane narrows the table (right padding = pane width), so the selected row stays visible.
Name column is sticky.

┌ Find ──┐┌ Name ▸ │ Type │ ρ bulk │ D50 │ φ  │ c  │ Data │ Refs ┐┌ JSC-1A ─────── × ┐
│ facets ││ JSC-1A │ Mare │   —    │129.1│ —  │ —  │ C M  │  17  ││ Props·Comp·FoM·  │
│        ││ JSC-2A │ Mare │  1.44  │  —  │ —  │ —  │ C M  │   6  ││ Buy·Refs         │
│        ││ LHS-1  │ High.│   …                                  ││ …                │
└────────┘└────────────────────────────────────────────────────────┘└──────────────────┘
```

### 5. Left pane: one job per view (owner question 2) (P1, M–L)

- **Where:** `src/components/sidebar/Sidebar.tsx:39-205`; `SimulantList.tsx`; `App.tsx:52` (starts closed) and `:286-342`.
- **What it holds today:** a second copy of the title with the version, the search box, "Add filter", a "Compare selected" button that only sometimes appears, a list of 148 cards (about 80 px each, each with a compare icon), a count, Feedback and Help, and a CNES badge. It starts closed, so most visitors never see the filters ([18](ui-review-2026-09-25/18-filter-and-header-wrap.jpg)).
- **What it does in each view today:**
  - Globe and 2D: the list is the only way to find a simulant without the map. That is useful, but the cards are large and each filter takes three clicks.
  - Table: the list repeats the table row for row. Only the filters matter here.
  - Moon: there are no filters, the list repeats the 19 markers and the table, and the search box does nothing (it also crashes, #1).
- **Proposal:** call it "Find" and make filtering its job.
  - Open by default at 1280 px and wider; a drawer on phones. When it is closed, show a chip at the top of the map or table ("3 filters · 23 of 148 · Clear") so active filters are never hidden.
  - Always show quick facets as chips with counts: Type, Availability, and data available (chemistry, mineralogy, geotechnical). Add range filters for bulk density, D50, friction angle and cohesion; today the only range filter is Year (`useFilters.ts:5-17`). Put country, institution, mineral, oxide, lunar sample and reference under "More filters".
  - Globe and 2D: a results list under the filters, one line per simulant (name, type, country). Hovering a row highlights its marker; clicking it opens the pane. Drop the compare icon on each row in favour of the checkbox and the tray (#6).
  - Table: no results list, because the table is the list. The pane holds only filters and can collapse to a 48 px rail with a filter-count badge.
  - Moon: the pane becomes "Missions". Programme chips with counts (Apollo, Luna, Chang'e, Other) filter the markers and the table and replace the static legend. The list is grouped by programme.
  - Move out of the pane: the repeated title, the CNES badge (to Help/About and the splash), the version (a small footer line), and "Compare selected" (to the tray).

```
Globe / 2D                      Table                     Moon
┌ Find simulants ─────────┐     ┌ Filters ───────┐ ┌──┐    ┌ Missions ────────────┐
│ [Search name, lab     ] │     │ same facets    │ │3 │    │ [Apollo 6] [Luna 6]  │
│ Type  [Mare 71][High 47]│     │ and ranges,    │ │▾ │    │ [Chang'e 4][Other 3] │
│ Avail [Avail 40][Res 18]│     │ no list        │ │  │    │ Apollo               │
│ Data  [Chem][Min][Geo]  │     │                │ │  │    │  Apollo 11  1969     │
│ Bulk ρ [   ]–[   ] g/cm³│     │                │ │  │    │  Apollo 12  1969     │
│ D50    [   ]–[   ] µm   │     │                │ │  │    │ Luna                 │
│ More filters ▾          │     │                │ │  │    │  …                   │
│ 23 of 148 · Clear       │     │ 23 of 148      │ │  │    │                      │
│ ☐ JSC-1A  Mare · USA    │     │                │ │  │    │                      │
│ ☐ LHS-1   High. · USA   │     │                │ │  │    │                      │
│ …                       │     │                │ │  │    │                      │
│ Help · Feedback · 2.9.17│     └────────────────┘ └──┘    └──────────────────────┘
└─────────────────────────┘                        rail when collapsed
```

### 6. Comparing two simulants: three entry points, one dead end (P1, M)

- **Where:** `src/hooks/usePanelState.ts:39-52`; `PanelShell.tsx:53-60`; `SimulantList.tsx:44-49`; `Sidebar.tsx:85-90`; `SimulantTable.tsx:182-192`.
- **What:** the compare icon in the pane turns on a hidden mode. The next simulant you pick goes into a "panel 2" that is never drawn, and nothing on screen changes ([14](ui-review-2026-09-25/14-panel-compare-armed.jpg), [15](ui-review-2026-09-25/15-panel-compare-second-picked.jpg)). The only way forward is "Compare selected" in the left pane, which you can't see if the pane is closed. The compare icon on each list row and the table checkboxes are two more mechanisms, each with its own rules (the table accepts exactly two).
- **Why it hurts:** a user clicks compare, picks a second simulant, sees nothing happen, and concludes the feature is broken.
- **Do:** use one compare tray. An "Add to compare" button in the pane, and a checkbox in the table and in the list, each add a chip to a tray at the bottom of the screen ("JSC-1A × LHS-1 × [Compare]"). Allow 2 to 4 simulants. Keep the tray across views and in the URL (#13). Remove the compare mode from `usePanelState`.

### 7. Comparison views drop citations and some data (P1, M)

- **Where:** `ComparisonPanel.tsx:22-58` and `:102-167`; `CrossComparisonPanel.tsx:40-53`; `CompositionTable.tsx:32`.
- **What:**
  - Neither comparison view shows a single superscript.
  - The mineral side of the lunar comparison uses only NASA mineral groups, which most simulants no longer have after the audit. JSC-1A shows "—" for every mineral, while its pane lists Glass 49.3, Plagioclase 37.1 and Olivine 9 ([16](ui-review-2026-09-25/16-cross-comparison-minerals-missing.jpg)).
  - The two-simulant comparison puts different vocabularies side by side (Anorthosite and Glass-rich basalt against Glass and Plagioclase) with no warning.
  - Physical properties appear only in Table mode.
  - In the pane, the lunar column's Total adds up only the rows the simulant has, so Apollo 14's mineral "total" reads 49.00 ([05](ui-review-2026-09-25/05-panel-composition-lunar-ref.jpg)).
- **Why it hurts:** a researcher makes the choice in the comparison view, and that view is the one least traceable to sources.
- **Do:** show superscripts in comparison cells (the working tree already does this for the lunar side as [L1]). Fall back to the detailed composition when there are no groups. When the two component lists barely overlap, add a note: "The two sources use different classifications." Show physical properties in both modes, open on Table (the mode with citations), and drop the partial lunar Total.

### 8. The lunar reference carries over from the previous simulant (P1, S)

- **Where:** `SimulantPanel.tsx:81-86` (a `setTimeout` inside render); `usePanelState.ts:12`.
- **What:** the reference is guessed once, from the first simulant you open, and then kept. After JSC-1A (Apollo 14), the highland simulant LHS-1 is still overlaid with Apollo 14, and "Full comparison view" compares it against the wrong sample.
- **Do:** guess again for each simulant unless the user picked a reference. Label a guess "Suggested from the producer's stated lunar sample", and move the guessing out of render.

### 9. The right pane is 7 screens long and opens on the least useful part (P1, M)

- **Where:** `SimulantPanel.tsx:101-166`; `SimulantProperties.tsx:17-66`; `FigureOfMeritSection.tsx:55-70`; `ReferencesSection.tsx:170-208`.
- **What:** JSC-1A scrolls for 6,308 px.
  - The first screen is 10 identity cards and a notes box, none with a citation. The subtitle "GENERAL PURPOSE" repeats Classification while Type says Mare, and Availability appears twice (as a card and under Purchase). Empty cards say "N/A" ([02](ui-review-2026-09-25/02-panel-covers-header.jpg)).
  - The Figures of Merit table has 14 rows over 1,350 px and mixes 0–1 and 0–100 scores in one column ([04](ui-review-2026-09-25/04-panel-figures-of-merit.jpg)).
  - References are 17 cards over 2,700 px, each with Source, Scholar, Cited by, a type badge and a check date ([06](ui-review-2026-09-25/06-panel-references.jpg)).
- **Why it hurts:** the researcher wants to know whether this simulant fits their need, which is answered by the physical properties and the composition. Both are below the fold, and the references are far away.
- **Do:**
  - Give the pane a sticky header with jump links: Properties · Composition · FoM · Purchase · References.
  - Order the sections: key numbers, composition (with the lunar reference selector), FoM, purchase, identity ("About"), references.
  - Show identity as a compact two-column list, hide empty fields, drop the duplicates, and use Type as the subtitle.
  - FoM: print the scale on each row ("88 / 100", "0.35 / 1"), show the overall score and one row per property, and put the rest behind "Show all 14".
  - References: show the first 5 behind "Show all 17". Drop "Cited by" and "Ask AI" (both are Google searches) and keep the DOI or Source link.

### 10. Citations are hard to follow and hover-only (P1, M)

- **Where:** `src/components/ui/RefSup.tsx:22-33`; `src/components/ui/Tooltip.tsx:13-37`; `SimulantProperties.tsx:53-64`; `SimulantTable.tsx:264-270`.
- **What:**
  - [13] isn't a link, and reference 13 is about 3,000 px further down. Hovering shows the page and the quote but not the document's name ([03](ui-review-2026-09-25/03-citation-hover.jpg)).
  - Tooltips open on mouse hover or keyboard focus only. Tapping [2] on a phone shows nothing.
  - The identity values (Type, Origin, Institution, Release date, Production, Feedstock, Availability) and the table's Year, Availability and Lunar Ref have no superscript, which breaks the per-value provenance rule. The Moon values have none either (the working tree adds them).
  - Amber means three things: citation marks, lunar reference values, and the "does not name this simulant" warning.
- **Why it hurts:** the product's promise is that every value traces to a document, and checking one currently takes a hunt.
- **Do:** make [n] a button. Clicking or tapping it opens a popover with the short title, the location, the quote, the DOI or Source link, and "Go to reference n", which scrolls to the reference and highlights it. Either cite the identity fields or mark them "not yet sourced". Give citations a neutral colour of their own and keep amber for the Moon.

### 11. Uppercase styling corrupts units and names (P1, S)

- **Where:** `SimulantTable.tsx:163` (`uppercase` on the headers) and `:219-222`; `ComparisonPanel.tsx:192-193`; `CrossComparisonPanel.tsx:201-202`; `PanelShell.tsx:39`; `PhysicalPropertiesSection.tsx:55`.
- **What:** "D50 (µm)" renders as "D50 (ΜM)", a Greek capital mu that reads as "mm" ([10](ui-review-2026-09-25/10-table-scrolled-units-uppercased.jpg)). "g/cm³" becomes "G/CM³" and "kPa" becomes "KPA". The comparison headers uppercase simulant names ("CLDS-i" becomes "CLDS-I"), although the Name column's help says names appear "as the producer writes it". Particle size distribution reads "<1mm µm" because the unit is appended to a text value that already has one ([02](ui-review-2026-09-25/02-panel-covers-header.jpg)).
- **Why it hurts:** a wrong unit in a materials database is a data error, not a style issue.
- **Do:** remove `uppercase` from any element that holds a unit or a name, and use sentence-case headers. Don't append a unit when the stored value already includes one.

### 12. Reference links break on DOIs with brackets (P1, S)

- **Where:** `ReferencesSection.tsx:13-25`.
- **What:** the URL and DOI patterns stop at ")". Six references, such as `10.1061/(ASCE)GT.1943-5606.0000068`, display "2009 )GT.1943-5606.0000068" and link to a cut-off DOI ([06](ui-review-2026-09-25/06-panel-references.jpg)).
- **Do:** match the DOI up to the next whitespace, trim trailing punctuation, and prefer the stored `doi` field when there is one.

---

## P2: navigation and structure

### 13. No link to a simulant, view or filter (P2, M)

- **Where:** `src/hooks/useMapState.ts`, `usePanelState.ts` and `useFilters.ts` keep all state in memory.
- **What:** the URL never changes. Reloading loses the selection, Back leaves the site, and there is no way to send someone "JSC-1A against LHS-1".
- **Why it hurts:** researchers cite and share. A database built on citations needs URLs that can be cited.
- **Do:** mirror the state in the query string, e.g. `?planet=earth&view=table&sim=S028&cmp=S051&f=type:Mare`. Replace the URL on filter changes and push a new entry on selection, so Back works.

### 14. Header and map chrome (P2, S)

- **Where:** `AppHeader.tsx:27-37` and `:39-86`; `App.tsx:176-179` and `:367-371`.
- **What:**
  - The title has no backdrop, so it can't be read on the Moon 2D map or on bright imagery ([21](ui-review-2026-09-25/21-moon-2d-title-illegible.jpg)).
  - Opening the left pane pushes the title right and wraps the toggles onto the map toolbar ([18](ui-review-2026-09-25/18-filter-and-header-wrap.jpg)).
  - Switching between Earth and Moon always resets the view to 3D, even from Table.
  - The Home button flies to France, on the Moon too.
  - On a phone there is no product name, and Earth and 3D use the same unlabelled globe icon ([23](ui-review-2026-09-25/23-phone-landing.jpg)).
  - The "Go to…" geocoder takes the most prominent slot in the header but serves no simulant task.
- **Do:** use the fixed bar from #3. Keep the current view when switching planet, and make Home show the whole globe. On phones, show a short name ("LRS Database"). Label the view switch "Globe | Map | Table" and give Earth a different icon. Move "Go to" into the map toolbar or drop it.

### 15. Maps: what a pin means, and what's selected (P2, M)

- **Where:** `App.tsx:84-95` and `:162-167`; `src/components/controls/LegendWidget.tsx:16-21`; `src/components/map/GlobeView.tsx:101-112` and `:159-165`; `LeafletMap.tsx:113` and `:133-134`.
- **What:**
  - Nothing says what a pin's location is. Each site is a feedstock quarry or a lab (`site_type`).
  - The legend lists 3 types but the data has 7: Dust, Icy, Mechanical and Specialty are drawn as "General". The green clusters aren't in the legend at all ([01](ui-review-2026-09-25/01-landing-globe.jpg)).
  - The selected simulant is not highlighted on the globe or the map.
  - The globe rotates and the cluster rings pulse by default, even while you try to click a thin 3D point, and nothing honours reduced-motion settings.
  - On the 2D map, each click zooms to level 10, and the popup repeats what the pane shows.
  - The 2D attribution credits OpenStreetMap, but the tiles are Esri World Imagery ([07](ui-review-2026-09-25/07-map-2d.jpg)).
- **Do:** add a legend line ("Pin: feedstock source or producing lab") and use different marker shapes for quarries and labs. Make the legend cover every type, or group the types and say so. Ring the selected marker. Turn rotation off by default and always under `prefers-reduced-motion`. Keep the current zoom on click, and fix the attribution.

### 16. Table layout (P2, M)

- **Where:** `SimulantTable.tsx:159-227`, and `:163` with `:180` (two sticky rows both at `top-0`); `App.tsx:332-342`.
- **What:**
  - The table has 17 columns and is 2,376 px wide in a 1,406 px frame ([08](ui-review-2026-09-25/08-table.jpg)). Name isn't sticky, so rows lose their names as soon as you scroll right ([10](ui-review-2026-09-25/10-table-scrolled-units-uppercased.jpg)).
  - The selection bar and the header row are both sticky at the top and overlap.
  - The left-pane toggle floats over the select-all box and the "2 selected" label ([12](ui-review-2026-09-25/12-table-selection-under-toggle.jpg)).
  - "Lunar Ref" mostly repeats Type ("General", "Mare").
  - Sorting is mouse-only: pressing Enter on a focused header does nothing.
- **Do:** make the Name column sticky. Move the selection bar out of the scrolling area, or make it sticky below the header. Group the columns (Identity · Geotechnical · Data) and add a column picker. Move the toggle into the fixed bar. Sort with a `<button>` inside each `<th>`, and set `aria-sort`.

### 17. Export drops the provenance (P2, M)

- **Where:** `src/utils/csv.ts:53-80`; `App.tsx:433-442`.
- **What:** the CSV has values but not their sources. It keeps only references whose type is exactly "composition" or "usage", so data sheets, geotechnical papers, reviews and combined types such as "composition,geotechnical" are dropped. It has no Figures of Merit and no physical-property sources. The Export button also shows on the Moon, where it exports simulants.
- **Do:** export each value with its reference number and location, plus a references sheet numbered as in the pane. Include every reference. On the Moon, either hide Export or export the sites.

### 18. The Moon section is an island (P2, M)

- **Where:** `LunarSitePanel.tsx:31-95`; `LunarSampleTable.tsx:47` and `:75-99`; `App.tsx:402-404`.
- **What:**
  - The site panel links neither to the simulants that target the site nor to the lunar sample used in comparisons (`lunar_reference`, which has chemistry and sources).
  - The table can't sort by density, friction or cohesion, the columns a researcher would compare with simulants. Samples sort as text, so "101 g" comes before "21.5 kg" ([22](ui-review-2026-09-25/22-moon-table.jpg)).
  - The coordinates get the biggest box in the panel ([20](ui-review-2026-09-25/20-moon-panel-covers-header.jpg)).
  - "Chang-e" and "Chang'e" both appear.
  - Citations are in progress in the working tree.
- **Do:** add a "Simulants that replicate this site" list (matched on `lunar_sample_reference`) and a "Compare a simulant with this site's sample" action. Show the returned-sample chemistry. Sort the geotechnical columns as numbers, and the samples as grams. Show the coordinates on one small line.

---

## P3: quality floor

### 19. The Pin button does nothing (P3, S)

- **Where:** `PanelShell.tsx:61-68`; `usePanelState.ts:29-37` (`minimizeUnpinned` is never called).
- **Do:** remove the button.

### 20. Contrast (P3, S)

- **What:** text in `slate-500` (76 uses) measures 3.4–3.75:1 on the panel backgrounds, and `slate-600` (11 uses) measures 2.2–2.4:1. Both are used for 10 px uppercase labels (39 uses of `text-[10px]`). WCAG AA requires 4.5:1 for text this size.
- **Do:** use `slate-400` as the minimum text colour (6.3–7:1) and 11–12 px as the minimum size, and drop the uppercase labels.

### 21. Keyboard and screen readers (P3, M)

- **What:**
  - Table rows can't take focus, so a keyboard user can't open a simulant from the table.
  - The sort headers take focus but do nothing (#16).
  - The list nests a button inside a button (`SimulantList.tsx:33` and `:44`). That is invalid HTML, and screen readers announce it wrongly.
  - Icon-only buttons (pane actions, map toolbar, close) rely on `title`; the whole codebase has one `aria-label`.
  - Escape closes nothing, and focus doesn't move into the pane when it opens or back when it closes.
  - Every tooltip wraps its trigger in a `tabIndex=0` span, so a keyboard user tabs through 17 headers before reaching the first row.
- **Do:** make rows focusable and open them with Enter. Add aria-labels to icon buttons. Make Escape close the top overlay. Move focus into the pane on open and back to the row on close. Make only the triggers that need a tooltip focusable.

### 22. Information only on hover (P3, M, shared with #10)

- **What:** column definitions, property definitions, the FoM explanations, citation details and globe point labels all appear on hover only.
- **Do:** open them on tap as well. Put an "i" button next to each definition, and on phones show definitions inline under their label.

### 23. Phone (P3, M)

- **What:**
  - The landing screen shows no product name ([23](ui-review-2026-09-25/23-phone-landing.jpg)).
  - The table scrolls 17 columns sideways with only Name and Type in view, and the Export button floats over the rows ([25](ui-review-2026-09-25/25-phone-table.jpg)).
  - Header buttons measure 40×28 px, below the recommended 44 px.
  - The pane is a 70 vh sheet holding 7 screens of content ([24](ui-review-2026-09-25/24-phone-panel.jpg)); drag-to-close is in the working tree.
- **Do:** on phones, show the table as a list (name, type, three key values, data marks). Make touch targets 44 px. The jump links from #9 matter most on phones.

### 24. Loading, error and empty states (P3, S)

- **What:**
  - Every load shows the splash for at least 2 s (`App.tsx:56-61`).
  - The first switch to Globe or 2D shows the full splash again (`App.tsx:230`, where the Suspense fallback is `LoadingScreen`). The comparison views have no fallback, so while their code loads, clicks seem to do nothing.
  - There is no error boundary (#1).
  - The empty table says "No simulants match the current filters." but offers no way to clear them.
  - Help mentions a GPS button that doesn't exist (`Sidebar.tsx:195`), and you can only reach Help with the left pane open.
- **Do:** drop the minimum splash time and show a small in-place spinner for views that are still loading. Add the error boundary and a "Clear filters" button in empty states. Fix the Help text and move Help to the fixed bar.

### 25. Consistency (P3, S–M)

- **What:**
  - Colours change role between views: the first simulant is emerald in the comparison and blue in the lunar comparison, the mineral chart is emerald and the chemical chart blue, and highland titles are cyan.
  - An empty value appears four ways: "N/A" (pane cards), "—" (table), "0.00" (comparison) and "-" (the lunar column in composition tables).
  - The comparison opens on Chart, while the pane and the lunar comparison open on Table.
  - One action has three names: "Compare against lunar reference", "Full comparison view" and "Cross-Comparison".
  - The theme tokens in `src/index.css` (`--color-primary` and the rest) are unused; components use raw Tailwind colours.
- **Do:** define one token per role (simulant A, simulant B, lunar, citation, warning). Use a single empty mark, "—". Open on Table everywhere. Call the action "Compare with a lunar sample" throughout.

---

## Suggested order

1. Fix the small, broken items first: #1, #2, #8, #11, #12, #19.
2. Then the layout: the fixed top bar (#3), the table and pane rule (#4), the Find pane (#5), and the compare tray (#6).
3. Then traceability: the pane's structure (#9), clickable citations (#10), citations in comparisons (#7), URLs (#13) and export (#17).
4. Everything else can follow in any order.
