document.addEventListener('DOMContentLoaded', () => {
    // Initialize map
    let map = L.map('map', {
        zoomControl: true,
        attributionControl: true
    }).setView([46.6, 2.5], 3);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles © Esri'
    }).addTo(map);

    // Custom moon icon
    const moonIcon = L.icon({
        iconUrl: './img/moon.png',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -16]
    });

    // Marker cluster
    let markers = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false
    });
    map.addLayer(markers);

    // Global state
    let countryLayer = null;
    let countryGeoJson = null;
    let simulants = [], sites = [], minerals = [], chemicals = [], references = [];
    let markerMap = {};
    let charts = {
        mineral1: null,
        chemical1: null,
        mineral2: null,
        chemical2: null
    };
    let panelStates = {
        panel1: { open: false, pinned: false, simulantId: null },
        panel2: { open: false, pinned: false, simulantId: null }
    };
    let compareMode = false;
    let isProgrammaticMove = false;

    // Constants
    const euCountries = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
        "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"];

    const countryMap = {
        "USA": "USA", "UK": "GBR", "EU": "EU", "France": "FRA",
        "Germany": "DEU", "Italy": "ITA", "China": "CHN",
        "Australia": "AUS", "Norway": "NOR", "Canada": "CAN",
        "Japan": "JPN", "South Korea": "KOR", "India": "IND",
        "Turkey": "TUR", "Thailand": "THA", "Ital": "ITA", "Spain": "ESP"
    };

    // Display names for country codes in filters
    const countryDisplayNames = {
        "USA": "United States",
        "UK": "United Kingdom",
        "EU": "European Union",
        "Ital": "Italy"
    };

    // Institution website URLs
    const institutionUrls = {
        "Space Resource Technologies": "https://exolithsimulants.com/",
        "Space Resources (Exolith Lab)": "https://exolithsimulants.com/",
        "Hispansion": "https://www.hispansion.io/",
        "Off Planet Research": "https://www.offplanetresearch.com/",
        "NASA": "https://www.nasa.gov/",
        "ESA": "https://www.esa.int/",
        "ESA / Technical University of Bari": "https://www.esa.int/",
        "ESA/Technical University Braunschweig": "https://www.esa.int/",
        "JAXA, LETO": "https://global.jaxa.jp/",
        "European Astronaut Centre (EAC": "https://www.esa.int/About_Us/EAC",
        "Shimizu Corporation": "https://www.shimz.co.jp/en/",
        "Colorado School of Mines": "https://www.mines.edu/",
        "University of Minnesota": "https://twin-cities.umn.edu/",
        "Technische Universität Berlin": "https://www.tu.berlin/en/",
        "Technische Universität Braunschweig": "https://www.tu-braunschweig.de/en/",
        "The University of Manchester": "https://www.manchester.ac.uk/",
        "The University of Winnipeg": "https://www.uwinnipeg.ca/",
        "Wuhan University": "https://en.whu.edu.cn/",
        "Tongji University": "https://en.tongji.edu.cn/",
        "Jilin University Changchun": "https://global.jlu.edu.cn/",
        "Northeastern University": "https://english.neu.edu.cn/",
        "China University of Mining and Technology": "https://www.cumt.edu.cn/",
        "University of Geosciences": "https://en.cug.edu.cn/",
        "Polish Academy of Sciences": "https://institution.pan.pl/",
        "Goddard Space Center": "https://www.nasa.gov/goddard/",
        "MSFC": "https://www.nasa.gov/marshall/",
        "NASA-MSFC and USGS": "https://www.nasa.gov/marshall/",
        "NASA and USGS": "https://www.nasa.gov/",
        "NASA/USGS": "https://www.nasa.gov/",
        "NASA/Washington Mills": "https://www.nasa.gov/",
        "KIGAM": "https://www.kigam.re.kr/english/",
        "ISAC": "https://www.isro.gov.in/ISAC.html",
        "SolSys Mining": "https://solsysmining.com/",
        "Hudson Resources Inc.": "https://hudsonresources.ca/",
        "Orbitec, Inc.": "https://www.sncorp.com/",
        "Astroport Space Technologies, Inc.": "https://www.astroport.space/",
        "Space Zab Company": "https://www.spacezab.com/",
        "Deltion Innovations Ltd. Canada": "https://www.deltion.ca/",
        "Deltion Innovations Ltd": "https://www.deltion.ca/",
        "NORCAT": "https://www.norcat.org/",
        "UCF": "https://www.ucf.edu/"
    };

    // Loading overlay
    function showLoading() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <p style="font-weight: 500; color: var(--text-secondary);">Loading lunar data...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    function hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.remove();
    }

    // Load data
    showLoading();
    Promise.all([
        fetch('./data/simulant.json').then(r => r.json()),
        fetch('./data/site.json').then(r => r.json()),
        fetch('./data/composition.json').then(r => r.json()),
        fetch('./data/chemical_composition.json').then(r => r.json()),
        fetch('./data/references.json').then(r => r.json()),
        fetch('./data/countries.geojson').then(r => r.json())
    ]).then(([simData, siteData, minData, chemData, refData, geoData]) => {
        simulants = simData;
        sites = siteData;
        minerals = minData;
        chemicals = chemData;
        references = refData;
        countryGeoJson = geoData;

        console.log('✓ Data loaded:', {
            simulants: simulants.length,
            sites: sites.length,
            minerals: minerals.length,
            chemicals: chemicals.length
        });

        hideLoading();
        populateFilters();
        updateMap();
        initializePanels();
        initializeExport();
        updateSimulantCount();
    }).catch(error => {
        hideLoading();
        console.error('Error loading data:', error);
        alert('Failed to load data. Check console for details.');
    });

    // Update simulant count dynamically
    function updateSimulantCount() {
        const typeFilter = Array.from(document.getElementById('type-filter').selectedOptions).map(o => o.value);
        const countryFilter = Array.from(document.getElementById('country-filter').selectedOptions).map(o => o.value);
        const mineralFilter = Array.from(document.getElementById('mineral-filter').selectedOptions).map(o => o.value);
        const chemicalFilter = Array.from(document.getElementById('chemical-filter').selectedOptions).map(o => o.value);
        const institutionFilter = Array.from(document.getElementById('institution-filter').selectedOptions).map(o => o.value);

        let filtered = simulants.filter(s => {
            let keep = true;
            if (typeFilter.length) keep = keep && typeFilter.includes(s.type);
            if (countryFilter.length) keep = keep && countryFilter.includes(s.country_code);
            if (institutionFilter.length) keep = keep && institutionFilter.includes(s.institution);
            if (mineralFilter.length) {
                let sMinerals = minerals.filter(m => m.simulant_id === s.simulant_id).map(m => m.component_name);
                keep = keep && mineralFilter.some(m => sMinerals.includes(m));
            }
            if (chemicalFilter.length) {
                let sChemicals = chemicals.filter(c => c.simulant_id === s.simulant_id).map(c => c.component_name);
                keep = keep && chemicalFilter.some(c => sChemicals.includes(c));
            }
            return keep;
        });

        const countEl = document.getElementById('simulant-count');
        if (filtered.length === simulants.length) {
            countEl.textContent = `${simulants.length} simulants loaded`;
        } else {
            countEl.textContent = `${filtered.length} of ${simulants.length} simulants`;
        }
    }

    // Populate filters
    function populateFilters() {
        const lrsDropdown = document.getElementById('lrs-dropdown');
        const typeFilter = document.getElementById('type-filter');
        const countryFilter = document.getElementById('country-filter');
        const mineralFilter = document.getElementById('mineral-filter');
        const chemicalFilter = document.getElementById('chemical-filter');
        const institutionFilter = document.getElementById('institution-filter');

        simulants.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.simulant_id;
            opt.text = s.name;
            lrsDropdown.appendChild(opt);
        });

        [...new Set(simulants.map(s => s.type).filter(Boolean))].sort().forEach(t => {
            const opt = document.createElement('option');
            opt.value = t;
            opt.text = t;
            typeFilter.appendChild(opt);
        });

        [...new Set(simulants.map(s => s.country_code).filter(Boolean))].sort().forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.text = countryDisplayNames[c] || c;
            countryFilter.appendChild(opt);
        });

        [...new Set(minerals.map(m => m.component_name).filter(Boolean))].sort().forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.text = m;
            mineralFilter.appendChild(opt);
        });

        [...new Set(chemicals.map(c => c.component_name).filter(Boolean))].sort().forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.text = c;
            chemicalFilter.appendChild(opt);
        });

        [...new Set(simulants.map(s => s.institution).filter(Boolean))].sort().forEach(i => {
            const opt = document.createElement('option');
            opt.value = i;
            opt.text = i.replace(/\r?\n/g, ' ').trim(); // Clean up multiline institution names
            institutionFilter.appendChild(opt);
        });

        // Event listeners for filters with toggle behavior
        [typeFilter, countryFilter, mineralFilter, chemicalFilter, institutionFilter].forEach(filter => {
            filter.addEventListener('mousedown', (e) => {
                if (e.target.tagName === 'OPTION') {
                    e.preventDefault();
                    const option = e.target;
                    option.selected = !option.selected;
                    updateMap();
                    updateSimulantCount();

                    // Update country panel if country filter changed
                    if (filter === countryFilter) {
                        updateCountryPanel();
                    }
                }
            });
        });

        // Select All buttons
        // Select All / Deselect All buttons
        document.querySelectorAll('.select-all-btn, .deselect-all-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.dataset.target;
                const action = btn.dataset.action;
                const select = document.getElementById(targetId);
                const shouldSelect = action === 'select';
                Array.from(select.options).forEach(opt => opt.selected = shouldSelect);
                updateMap();
                updateSimulantCount();
                if (targetId === 'country-filter') {
                    updateCountryPanel();
                }
            });
        });

        lrsDropdown.addEventListener('change', () => {
            const selected = lrsDropdown.value;
            if (selected) {
                if (compareMode && panelStates.panel2.open) {
                    showInfo(selected, 2, true, true);
                } else {
                    showInfo(selected, 1, true, true);
                }
            }
        });
    }

    // Initialize panel interactions
    function initializePanels() {
        // Panel handles
        document.querySelectorAll('.panel-handle').forEach(handle => {
            handle.addEventListener('click', () => {
                const panelNum = handle.dataset.panel;
                togglePanel(panelNum);
            });
        });

        // Close buttons
        document.querySelectorAll('.close-panel').forEach(btn => {
            btn.addEventListener('click', () => {
                const panelNum = btn.dataset.panel;
                closePanel(panelNum);
            });
        });

        // Pin buttons
        document.getElementById('pin-panel-1').addEventListener('click', function () {
            panelStates.panel1.pinned = !panelStates.panel1.pinned;
            this.classList.toggle('active', panelStates.panel1.pinned);
            const panel = document.getElementById('info-panel-1');
            if (panelStates.panel1.pinned) {
                panel.classList.add('pinned');
            } else {
                panel.classList.remove('pinned');
            }
        });

        document.getElementById('pin-panel-2').addEventListener('click', function () {
            panelStates.panel2.pinned = !panelStates.panel2.pinned;
            this.classList.toggle('active', panelStates.panel2.pinned);
            const panel = document.getElementById('info-panel-2');
            if (panelStates.panel2.pinned) {
                panel.classList.add('pinned');
            } else {
                panel.classList.remove('pinned');
            }
        });

        // Search Sources buttons - opens Google Scholar search for the simulant
        document.getElementById('search-sources-1').addEventListener('click', function () {
            const simulantId = panelStates.panel1.simulantId;
            if (!simulantId) {
                alert('Please select a simulant first');
                return;
            }
            const s = simulants.find(x => x.simulant_id === simulantId);
            if (s) {
                const query = encodeURIComponent(`"${s.name}" lunar regolith`);
                window.open(`https://scholar.google.com/scholar?q=${query}`, '_blank');
            }
        });

        document.getElementById('search-sources-2').addEventListener('click', function () {
            const simulantId = panelStates.panel2.simulantId;
            if (!simulantId) {
                alert('Please select a simulant first');
                return;
            }
            const s = simulants.find(x => x.simulant_id === simulantId);
            if (s) {
                const query = encodeURIComponent(`"${s.name}" lunar regolith`);
                window.open(`https://scholar.google.com/scholar?q=${query}`, '_blank');
            }
        });

        // Download buttons in panels
        document.getElementById('download-btn-1').addEventListener('click', function () {
            const simulantId = panelStates.panel1.simulantId;
            if (!simulantId) {
                alert('Please select a simulant first');
                return;
            }
            const s = simulants.find(x => x.simulant_id === simulantId);
            if (s) {
                downloadSimulantCSV(s);
            }
        });

        document.getElementById('download-btn-2').addEventListener('click', function () {
            const simulantId = panelStates.panel2.simulantId;
            if (!simulantId) {
                alert('Please select a simulant first');
                return;
            }
            const s = simulants.find(x => x.simulant_id === simulantId);
            if (s) {
                downloadSimulantCSV(s);
            }
        });

        // Compare buttons in panels
        document.getElementById('compare-btn-1').addEventListener('click', function () {
            if (!panelStates.panel1.simulantId) {
                alert('Please select a simulant first');
                return;
            }
            compareMode = !compareMode;
            this.classList.toggle('active', compareMode);

            if (compareMode) {
                document.getElementById('info-panel-1').classList.add('comparison-mode');
                openPanel(2);
            } else {
                document.getElementById('info-panel-1').classList.remove('comparison-mode');
                closePanel(2);
            }
        });

        // Map interactions - minimize unpinned panels (but not during programmatic moves)
        map.on('drag', () => {
            if (isProgrammaticMove) return;
            if (!panelStates.panel1.pinned && panelStates.panel1.open) {
                minimizePanel(1);
            }
            if (!panelStates.panel2.pinned && panelStates.panel2.open) {
                minimizePanel(2);
            }
        });

        map.on('zoomstart', () => {
            if (isProgrammaticMove) return;
            if (!panelStates.panel1.pinned && panelStates.panel1.open) {
                minimizePanel(1);
            }
            if (!panelStates.panel2.pinned && panelStates.panel2.open) {
                minimizePanel(2);
            }
        });

        // Close unpinned panels when clicking on the map (not on markers)
        map.on('click', (e) => {
            // Don't close if clicking on a marker (marker clicks are handled separately)
            if (e.originalEvent.target.closest('.leaflet-marker-icon')) return;

            if (!panelStates.panel1.pinned && panelStates.panel1.open) {
                minimizePanel(1);
            }
            if (!panelStates.panel2.pinned && panelStates.panel2.open) {
                minimizePanel(2);
            }
        });

        // Country panel close button
        document.getElementById('close-country-panel').addEventListener('click', () => {
            document.getElementById('country-panel').classList.remove('open');
        });
    }

    function togglePanel(panelNum) {
        const state = panelStates[`panel${panelNum}`];
        if (state.open) {
            minimizePanel(panelNum);
        } else {
            openPanel(panelNum);
        }
    }

    function openPanel(panelNum) {
        const panel = document.getElementById(`info-panel-${panelNum}`);
        panel.classList.add('open');
        panelStates[`panel${panelNum}`].open = true;
    }

    function minimizePanel(panelNum) {
        const panel = document.getElementById(`info-panel-${panelNum}`);
        if (!panelStates[`panel${panelNum}`].pinned) {
            panel.classList.remove('open');
            panelStates[`panel${panelNum}`].open = false;
        }
    }

    function closePanel(panelNum) {
        const panel = document.getElementById(`info-panel-${panelNum}`);
        panel.classList.remove('open', 'pinned');
        panelStates[`panel${panelNum}`].open = false;
        panelStates[`panel${panelNum}`].pinned = false;
        panelStates[`panel${panelNum}`].simulantId = null;

        document.getElementById(`pin-panel-${panelNum}`).classList.remove('active');

        document.querySelector(`#info-panel-${panelNum} .panel-title`).textContent =
            panelNum === '1' ? 'Select a simulant' : 'Select second simulant';
        document.getElementById(`properties-panel-${panelNum}`).innerHTML =
            '<p class="placeholder-text">Select a simulant to view properties</p>';
        document.getElementById(`references-panel-${panelNum}`).innerHTML =
            '<p class="placeholder-text">Select a simulant to view references</p>';

        // If closing panel 1 and compare mode is on, turn it off
        if (panelNum === '1' && compareMode) {
            compareMode = false;
            document.getElementById('compare-btn-1').classList.remove('active');
            document.getElementById('info-panel-1').classList.remove('comparison-mode');
            closePanel(2);
        }
    }

    // Update country panel
    function updateCountryPanel() {
        const countryFilter = Array.from(document.getElementById('country-filter').selectedOptions).map(o => o.value);
        const panel = document.getElementById('country-panel');
        const content = document.getElementById('country-panel-content');
        const title = document.getElementById('country-panel-title');

        if (countryFilter.length === 0) {
            panel.classList.remove('open');
            return;
        }

        if (countryFilter.length === 1) {
            title.textContent = `Simulants in ${countryDisplayNames[countryFilter[0]] || countryFilter[0]}`;
        } else {
            title.textContent = `Simulants in ${countryFilter.length} Countries`;
        }

        const filtered = simulants.filter(s => countryFilter.includes(s.country_code));

        content.innerHTML = '';
        if (filtered.length === 0) {
            content.innerHTML = '<p class="placeholder-text">No simulants found</p>';
        } else {
            filtered.forEach(s => {
                const item = document.createElement('div');
                item.className = 'simulant-list-item';
                item.innerHTML = `
                    <div class="simulant-list-item-name">${s.name}</div>
                    <div class="simulant-list-item-type">${s.type || 'N/A'}</div>
                `;
                item.addEventListener('click', () => {
                    showInfo(s.simulant_id, compareMode && panelStates.panel1.simulantId ? 2 : 1, true, true);
                });
                content.appendChild(item);
            });
        }

        panel.classList.add('open');
    }

    // Update map
    function updateMap() {
        markers.clearLayers();
        markerMap = {};

        const typeFilter = Array.from(document.getElementById('type-filter').selectedOptions).map(o => o.value);
        const countryFilter = Array.from(document.getElementById('country-filter').selectedOptions).map(o => o.value);
        const mineralFilter = Array.from(document.getElementById('mineral-filter').selectedOptions).map(o => o.value);
        const chemicalFilter = Array.from(document.getElementById('chemical-filter').selectedOptions).map(o => o.value);
        const institutionFilter = Array.from(document.getElementById('institution-filter').selectedOptions).map(o => o.value);

        let filtered = simulants.filter(s => {
            let keep = true;
            if (typeFilter.length) keep = keep && typeFilter.includes(s.type);
            if (countryFilter.length) keep = keep && countryFilter.includes(s.country_code);
            if (mineralFilter.length) {
                let sMinerals = minerals.filter(m => m.simulant_id === s.simulant_id).map(m => m.component_name);
                keep = keep && mineralFilter.some(m => sMinerals.includes(m));
            }
            if (chemicalFilter.length) {
                let sChemicals = chemicals.filter(c => c.simulant_id === s.simulant_id).map(c => c.component_name);
                keep = keep && chemicalFilter.some(c => sChemicals.includes(c));
            }
            if (institutionFilter.length) keep = keep && institutionFilter.includes(s.institution);
            return keep;
        });

        if (countryFilter.length === 1) {
            highlightCountry(countryFilter[0]);
        } else if (countryLayer) {
            map.removeLayer(countryLayer);
        }

        filtered.forEach(s => {
            let siteRows = sites.filter(site => site.simulant_id === s.simulant_id);
            siteRows.forEach(site => {
                let lat = parseFloat(site.lat) || 0;
                let lon = parseFloat(site.lon) || 0;

                if (lat === 0 && lon === 0) return;

                let marker = L.marker([lat, lon], { icon: moonIcon });
                const countryName = s.country_code ? (countryDisplayNames[s.country_code] || s.country_code) : 'N/A';
                let popupContent = `<b>${s.name}</b><br>Type: ${s.type || 'N/A'}<br>Country: ${countryName}`;
                marker.bindPopup(popupContent);
                marker.bindTooltip(s.name, { permanent: false, direction: "top" });

                marker.on('click', () => {
                    if (compareMode && panelStates.panel1.simulantId && !panelStates.panel2.simulantId) {
                        showInfo(s.simulant_id, 2, false, true);
                    } else {
                        showInfo(s.simulant_id, 1, false, true);
                    }
                });

                markers.addLayer(marker);
                markerMap[s.simulant_id] = marker;
            });
        });

        console.log(`Map updated: ${filtered.length} simulants`);
    }

    // Helper to get country code from GeoJSON feature (some countries like France have iso_a3: -99)
    function getCountryCode(props) {
        const iso = props.iso_a3 || props.ISO_A3;
        if (iso && iso !== -99 && iso !== '-99') return iso;
        return props.adm0_a3 || props.ADM0_A3;
    }

    // Highlight country
    function highlightCountry(countryCode) {
        if (!countryGeoJson || !countryCode) return;
        if (countryLayer) map.removeLayer(countryLayer);

        let featuresToHighlight = [];

        if (countryCode === "EU") {
            featuresToHighlight = countryGeoJson.features.filter(f =>
                euCountries.includes(getCountryCode(f.properties))
            );
        } else {
            const code = countryMap[countryCode] || countryCode;
            const feat = countryGeoJson.features.find(f =>
                getCountryCode(f.properties) === code ||
                (f.properties.iso_a2 || f.properties.ISO_A2) === code
            );
            if (feat) featuresToHighlight.push(feat);
        }

        if (featuresToHighlight.length > 0) {
            countryLayer = L.geoJSON(featuresToHighlight, {
                style: {
                    color: "#667eea",
                    weight: 2,
                    fillColor: "#764ba2",
                    fillOpacity: 0.1
                }
            }).addTo(map);
            countryLayer.bringToFront();
        }
    }

    // Show simulant info
    function showInfo(simulant_id, panelNum = 1, centerMap = false, openPopup = false) {
        const s = simulants.find(x => x.simulant_id === simulant_id);
        if (!s) return;

        panelStates[`panel${panelNum}`].simulantId = simulant_id;

        document.querySelector(`#info-panel-${panelNum} .panel-title`).textContent = s.name;

        if (countryLayer) map.removeLayer(countryLayer);
        let featuresToHighlight = [];

        if (s.country_code === "EU") {
            featuresToHighlight = countryGeoJson.features.filter(f =>
                euCountries.includes(getCountryCode(f.properties))
            );
        } else {
            const code = countryMap[s.country_code] || s.country_code;
            const feat = countryGeoJson.features.find(f =>
                getCountryCode(f.properties) === code ||
                (f.properties.iso_a2 || f.properties.ISO_A2) === code
            );
            if (feat) featuresToHighlight.push(feat);
        }

        if (featuresToHighlight.length > 0) {
            countryLayer = L.geoJSON(featuresToHighlight, {
                style: {
                    color: "#667eea",
                    weight: 2,
                    fillColor: "#764ba2",
                    fillOpacity: 0.15
                }
            }).addTo(map);
            countryLayer.bringToFront();
        }

        const site = sites.find(site => site.simulant_id === simulant_id);
        if (site && site.lat && site.lon) {
            if (centerMap) {
                isProgrammaticMove = true;
                setTimeout(() => {
                    map.flyTo([site.lat, site.lon], 7);
                    map.once('moveend', () => {
                        isProgrammaticMove = false;
                    });
                }, 250);
            }
            if (openPopup && markerMap[simulant_id]) {
                markerMap[simulant_id].openPopup();
            }
        }

        updateProperties(simulant_id, panelNum);
        updateMineralChart(simulant_id, panelNum);
        updateChemicalChart(simulant_id, panelNum);
        updateReferences(simulant_id, panelNum);

        openPanel(panelNum);
    }

    function updateProperties(simulant_id, panelNum) {
        const propPanel = document.getElementById(`properties-panel-${panelNum}`);
        propPanel.innerHTML = '';

        const s = simulants.find(x => x.simulant_id === simulant_id);
        if (!s) {
            propPanel.innerHTML = '<p class="placeholder-text">No properties available</p>';
            return;
        }

        // Define properties to display with labels
        const propertyDefs = [
            { key: 'type', label: 'Type' },
            { key: 'lunar_sample_reference', label: 'Lunar Sample' },
            { key: 'institution', label: 'Institution' },
            { key: 'availability', label: 'Availability' },
            { key: 'release_date', label: 'Release Date' },
            { key: 'tons_produced_mt', label: 'Tons Produced (MT)' },
            { key: 'density_g_cm3', label: 'Density (g/cm³)' },
            { key: 'specific_gravity', label: 'Specific Gravity' },
            { key: 'glass_content_percent', label: 'Glass Content (%)' },
            { key: 'ti_content_percent', label: 'Ti Content (%)' },
            { key: 'nanophase_iron_content', label: 'Nanophase Iron' },
            { key: 'particle_size_distribution', label: 'Particle Size' },
            { key: 'particle_morphology', label: 'Particle Morphology' },
            { key: 'particle_ruggedness', label: 'Particle Ruggedness' },
            { key: 'nasa_fom_score', label: 'NASA FoM Score' },
            { key: 'notes', label: 'Notes' }
        ];

        const grid = document.createElement('div');
        grid.className = 'properties-grid';

        let hasProperties = false;
        propertyDefs.forEach(prop => {
            const value = s[prop.key];
            if (value !== null && value !== undefined && value !== '' && value !== 'null') {
                hasProperties = true;
                const item = document.createElement('div');
                item.className = 'property-item';

                const label = document.createElement('span');
                label.className = 'property-label';
                label.textContent = prop.label;

                const val = document.createElement('span');
                val.className = 'property-value';

                // Make institution clickable if URL is available
                if (prop.key === 'institution') {
                    const cleanValue = String(value).replace(/\r?\n/g, ' ').trim();
                    const url = institutionUrls[cleanValue];
                    if (url) {
                        const link = document.createElement('a');
                        link.href = url;
                        link.target = '_blank';
                        link.rel = 'noopener noreferrer';
                        link.textContent = cleanValue;
                        link.className = 'institution-link';
                        val.appendChild(link);
                    } else {
                        val.textContent = cleanValue;
                    }
                } else {
                    val.textContent = value;
                }

                item.appendChild(label);
                item.appendChild(val);
                grid.appendChild(item);
            }
        });

        if (hasProperties) {
            propPanel.appendChild(grid);
        } else {
            propPanel.innerHTML = '<p class="placeholder-text">No properties available</p>';
        }
    }

    function updateMineralChart(simulant_id, panelNum) {
        const chartKey = `mineral${panelNum}`;
        const canvas = document.getElementById(`mineral-chart-${panelNum}`);
        const ctx = canvas.getContext('2d');

        if (charts[chartKey]) charts[chartKey].destroy();

        const minSubset = minerals.filter(m => m.simulant_id === simulant_id && m.value_pct > 0)
            .sort((a, b) => b.value_pct - a.value_pct);

        if (minSubset.length > 0) {
            canvas.style.display = 'block';
            const wrapper = canvas.parentElement;
            const noDataMsg = wrapper.querySelector('.no-data-message');
            if (noDataMsg) noDataMsg.remove();

            charts[chartKey] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: minSubset.map(m => m.component_name),
                    datasets: [{
                        label: 'Mineral %',
                        data: minSubset.map(m => m.value_pct),
                        backgroundColor: 'rgba(0, 180, 216, 0.8)',
                        borderColor: 'rgba(0, 180, 216, 1)',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(20, 27, 45, 0.95)',
                            titleColor: '#00b4d8',
                            bodyColor: '#e8eaed',
                            borderColor: 'rgba(0, 180, 216, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 6
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 100,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#9aa0a6' }
                        },
                        y: {
                            ticks: { autoSkip: false, font: { size: 11 }, color: '#e8eaed' },
                            grid: { display: false }
                        }
                    }
                }
            });
        } else {
            canvas.style.display = 'none';
            const wrapper = canvas.parentElement;
            if (!wrapper.querySelector('.no-data-message')) {
                const msg = document.createElement('p');
                msg.className = 'no-data-message placeholder-text';
                msg.textContent = 'Data not available. See references for more information.';
                wrapper.appendChild(msg);
            }
        }
    }

    function updateChemicalChart(simulant_id, panelNum) {
        const chartKey = `chemical${panelNum}`;
        const canvas = document.getElementById(`chemical-chart-${panelNum}`);
        const ctx = canvas.getContext('2d');

        if (charts[chartKey]) charts[chartKey].destroy();

        const chemSubset = chemicals.filter(c =>
            c.simulant_id === simulant_id &&
            c.component_type === 'oxide' &&
            c.component_name?.toLowerCase() !== 'sum'
        );

        if (chemSubset.length === 0) {
            canvas.style.display = 'none';
            const wrapper = canvas.parentElement;
            if (!wrapper.querySelector('.no-data-message')) {
                const msg = document.createElement('p');
                msg.className = 'no-data-message placeholder-text';
                msg.textContent = 'Data not available. See references for more information.';
                wrapper.appendChild(msg);
            }
        } else {
            canvas.style.display = 'block';
            const wrapper = canvas.parentElement;
            const noDataMsg = wrapper.querySelector('.no-data-message');
            if (noDataMsg) noDataMsg.remove();
            charts[chartKey] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: chemSubset.map(c => c.component_name),
                    datasets: [{
                        data: chemSubset.map(c => c.value_wt_pct),
                        backgroundColor: [
                            '#00b4d8', '#fc3d21', '#fca311', '#48cae4',
                            '#90e0ef', '#ff6b6b', '#c77dff', '#06d6a0'
                        ],
                        borderWidth: 2,
                        borderColor: '#141b2d'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 10,
                                font: { size: 11 },
                                usePointStyle: true,
                                color: '#e8eaed'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(20, 27, 45, 0.95)',
                            titleColor: '#00b4d8',
                            bodyColor: '#e8eaed',
                            borderColor: 'rgba(0, 180, 216, 0.3)',
                            borderWidth: 1,
                            padding: 12,
                            cornerRadius: 6
                        }
                    }
                }
            });
        }
    }

    function updateReferences(simulant_id, panelNum) {
        const refPanel = document.getElementById(`references-panel-${panelNum}`);
        refPanel.innerHTML = '';

        const refSubset = references.filter(r => r.simulant_id === simulant_id);

        if (refSubset.length === 0) {
            refPanel.innerHTML = '<p class="placeholder-text">No references available</p>';
        } else {
            refSubset.forEach(r => {
                const div = document.createElement('div');
                div.className = 'reference-item';

                const text = r.reference_text || '';

                // Create clickable reference link to Google Scholar
                const refLink = document.createElement('a');
                refLink.className = 'reference-link';
                refLink.href = `https://scholar.google.com/scholar?q=${encodeURIComponent(text)}`;
                refLink.target = '_blank';
                refLink.rel = 'noopener noreferrer';
                refLink.title = 'Search on Google Scholar';
                refLink.textContent = text;

                div.appendChild(refLink);
                refPanel.appendChild(div);
            });
        }
    }

    // Clear filters and navigate home
    document.getElementById('clear-filters').addEventListener('click', () => {
        ['type-filter', 'country-filter', 'mineral-filter', 'chemical-filter', 'institution-filter'].forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                Array.from(select.options).forEach(opt => opt.selected = false);
            }
        });
        document.getElementById('lrs-dropdown').selectedIndex = 0;

        // Close country panel
        document.getElementById('country-panel').classList.remove('open');

        // Close info panels
        closePanel('1');
        closePanel('2');

        updateMap();
        updateSimulantCount();
        map.flyTo([46.6, 2.5], 3, { animate: true, duration: 1.5 });
        if (countryLayer) map.removeLayer(countryLayer);
    });

    // Home button
    document.getElementById('home-button').addEventListener('click', () => {
        map.flyTo([46.6, 2.5], 3, { animate: true, duration: 1.5 });
        if (countryLayer) map.removeLayer(countryLayer);
    });

    // Mobile sidebar toggle
    const menuToggle = document.getElementById('menu-toggle');
    const closeSidebar = document.getElementById('close-sidebar');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobile-overlay');

    function openMobileSidebar() {
        sidebar.classList.add('open');
        mobileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeMobileSidebar() {
        sidebar.classList.remove('open');
        mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    menuToggle.addEventListener('click', () => {
        if (sidebar.classList.contains('open')) {
            closeMobileSidebar();
        } else {
            openMobileSidebar();
        }
    });

    closeSidebar.addEventListener('click', closeMobileSidebar);
    mobileOverlay.addEventListener('click', closeMobileSidebar);

    // Close sidebar when selecting a simulant on mobile
    const originalLrsDropdownChange = lrsDropdown.onchange;
    lrsDropdown.addEventListener('change', () => {
        if (window.innerWidth <= 768 && lrsDropdown.value) {
            closeMobileSidebar();
        }
    });

    // Handle window resize - close mobile sidebar if resizing to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeMobileSidebar();
        }
    });

    // ===== EXPORT FUNCTIONALITY =====
    function initializeExport() {
        const exportBtn = document.getElementById('export-btn');
        const exportDropdown = document.getElementById('export-dropdown');

        // Toggle export dropdown
        exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportDropdown.classList.toggle('open');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!exportDropdown.contains(e.target) && !exportBtn.contains(e.target)) {
                exportDropdown.classList.remove('open');
            }
        });

        // Handle export options
        document.querySelectorAll('.export-option').forEach(btn => {
            btn.addEventListener('click', () => {
                const exportType = btn.dataset.export;
                const timestamp = new Date().toISOString().slice(0, 10);

                switch (exportType) {
                    case 'current':
                        const currentSimulantId = panelStates.panel1.simulantId;
                        if (!currentSimulantId) {
                            alert('Please select a simulant first');
                            return;
                        }
                        const currentSimulant = simulants.find(s => s.simulant_id === currentSimulantId);
                        if (currentSimulant) {
                            exportToCSV([currentSimulant], `${currentSimulant.name.replace(/[^a-z0-9]/gi, '_')}_${timestamp}.csv`);
                        }
                        break;

                    case 'filtered':
                        const filtered = getFilteredSimulants();
                        if (filtered.length === 0) {
                            alert('No simulants match the current filters');
                            return;
                        }
                        exportToCSV(filtered, `lunar_simulants_filtered_${timestamp}.csv`);
                        break;

                    case 'all':
                        exportToCSV(simulants, `lunar_simulants_all_${timestamp}.csv`);
                        break;
                }

                exportDropdown.classList.remove('open');
            });
        });
    }

    // Get filtered simulants based on current filters
    function getFilteredSimulants() {
        const typeFilter = Array.from(document.getElementById('type-filter').selectedOptions).map(o => o.value);
        const countryFilter = Array.from(document.getElementById('country-filter').selectedOptions).map(o => o.value);
        const mineralFilter = Array.from(document.getElementById('mineral-filter').selectedOptions).map(o => o.value);
        const chemicalFilter = Array.from(document.getElementById('chemical-filter').selectedOptions).map(o => o.value);
        const institutionFilter = Array.from(document.getElementById('institution-filter').selectedOptions).map(o => o.value);

        return simulants.filter(s => {
            let keep = true;
            if (typeFilter.length) keep = keep && typeFilter.includes(s.type);
            if (countryFilter.length) keep = keep && countryFilter.includes(s.country_code);
            if (mineralFilter.length) {
                let sMinerals = minerals.filter(m => m.simulant_id === s.simulant_id).map(m => m.component_name);
                keep = keep && mineralFilter.some(m => sMinerals.includes(m));
            }
            if (chemicalFilter.length) {
                let sChemicals = chemicals.filter(c => c.simulant_id === s.simulant_id).map(c => c.component_name);
                keep = keep && chemicalFilter.some(c => sChemicals.includes(c));
            }
            if (institutionFilter.length) keep = keep && institutionFilter.includes(s.institution);
            return keep;
        });
    }

    // Export simulants to CSV
    function exportToCSV(simulantsToExport, filename) {
        if (!simulantsToExport || simulantsToExport.length === 0) {
            alert('No simulants to export');
            return;
        }

        // Define columns for export
        const columns = [
            { key: 'name', label: 'Name' },
            { key: 'type', label: 'Type' },
            { key: 'country_code', label: 'Country' },
            { key: 'institution', label: 'Institution' },
            { key: 'availability', label: 'Availability' },
            { key: 'release_date', label: 'Release Date' },
            { key: 'lunar_sample_reference', label: 'Lunar Sample Reference' },
            { key: 'density_g_cm3', label: 'Density (g/cm³)' },
            { key: 'specific_gravity', label: 'Specific Gravity' },
            { key: 'glass_content_percent', label: 'Glass Content (%)' },
            { key: 'ti_content_percent', label: 'Ti Content (%)' },
            { key: 'particle_size_distribution', label: 'Particle Size' },
            { key: 'particle_morphology', label: 'Particle Morphology' },
            { key: 'nasa_fom_score', label: 'NASA FoM Score' },
            { key: 'tons_produced_mt', label: 'Tons Produced (MT)' },
            { key: 'notes', label: 'Notes' }
        ];

        // Build CSV header
        const headers = columns.map(c => c.label);

        // Add mineral and chemical composition columns dynamically
        const allMineralNames = [...new Set(minerals.map(m => m.component_name).filter(Boolean))].sort();
        const allChemicalNames = [...new Set(chemicals.filter(c => c.component_type === 'oxide' && c.component_name?.toLowerCase() !== 'sum').map(c => c.component_name).filter(Boolean))].sort();

        allMineralNames.forEach(m => headers.push(`Mineral: ${m} (%)`));
        allChemicalNames.forEach(c => headers.push(`Chemical: ${c} (wt%)`));

        // Add references column
        headers.push('References');

        // Build CSV rows
        const rows = simulantsToExport.map(s => {
            const row = columns.map(col => {
                let value = s[col.key];
                if (value === null || value === undefined) return '';
                // Clean multiline values and escape quotes
                value = String(value).replace(/\r?\n/g, ' ').trim();
                if (value.includes(',') || value.includes('"') || value.includes('\n')) {
                    value = '"' + value.replace(/"/g, '""') + '"';
                }
                return value;
            });

            // Add mineral composition values
            allMineralNames.forEach(mineralName => {
                const mineralData = minerals.find(m => m.simulant_id === s.simulant_id && m.component_name === mineralName);
                row.push(mineralData ? mineralData.value_pct : '');
            });

            // Add chemical composition values
            allChemicalNames.forEach(chemName => {
                const chemData = chemicals.find(c => c.simulant_id === s.simulant_id && c.component_name === chemName);
                row.push(chemData ? chemData.value_wt_pct : '');
            });

            // Add references (combined into single cell, separated by " | ")
            const simRefs = references.filter(r => r.simulant_id === s.simulant_id);
            let refsText = simRefs.map(r => r.reference_text).join(' | ');
            // Escape for CSV
            if (refsText.includes(',') || refsText.includes('"') || refsText.includes('\n')) {
                refsText = '"' + refsText.replace(/"/g, '""') + '"';
            }
            row.push(refsText);

            return row;
        });

        // Combine header and rows
        const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');

        // Download file
        downloadFile(csvContent, filename, 'text/csv;charset=utf-8;');
    }

    // Download file helper
    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    // Download single simulant CSV (used by panel download buttons)
    function downloadSimulantCSV(simulant) {
        const timestamp = new Date().toISOString().slice(0, 10);
        const filename = `${simulant.name.replace(/[^a-z0-9]/gi, '_')}_${timestamp}.csv`;
        exportToCSV([simulant], filename);
    }
});