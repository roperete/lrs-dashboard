/**
 * Third-party data the database reuses, with the attribution each licence asks for. One place,
 * so the Help window, the simulant pane and the CSV export say the same thing.
 *
 * The Lunar Regolith Database of Gasteiner, Murdoch & D'Angelo is published under the Licence
 * Ouverte 2.0 (etalab-2.0), which asks a reuser to name the source (at least the licensor) and
 * the date of the last update of the data reused, and not to suggest that the licensor endorses
 * the reuse (LO.md, "Réutilisation"). Checked 2026-09-25 on recherche.data.gouv.fr (version 2,
 * updated 27/08/2026) and Crossref (the paper, 10.1002/nag.70432).
 */

export const GASTEINER = {
  short: "Gasteiner, Murdoch & D'Angelo (2026), Lunar Regolith Database",
  dataset: "Gasteiner, L., Murdoch, N. & D'Angelo, O. (2026). Mechanical Properties of Lunar Soil: Raw Dataset for the Lunar Regolith Database. Recherche Data Gouv, version 2, last updated 27 August 2026.",
  datasetUrl: 'https://doi.org/10.57745/NTSZ8G',
  paper: "Gasteiner, L., Murdoch, N. & D'Angelo, O. (2026). An Open Database of Lunar Regolith and Simulants Properties. International Journal for Numerical and Analytical Methods in Geomechanics.",
  paperUrl: 'https://doi.org/10.1002/nag.70432',
  licence: 'Licence Ouverte / Open Licence 2.0 (etalab-2.0)',
  licenceUrl: 'https://github.com/etalab/licence-ouverte/blob/master/LO.md',
  use: 'Used to find the original sources of simulant and Moon values, and as the source of parts of the simulant descriptions '
    + '(classification, application, feedstock, rock type) and of the list of Moon landing sites. Every value shown here is cited '
    + 'to the original document that states it; values were checked against those documents and corrected where they differed. '
    + 'The authors and ISAE-SUPAERO do not endorse this database.',
};

/** Base maps and images. */
export const MAP_CREDITS = [
  { what: 'Country outlines', who: 'Natural Earth (public domain)', url: 'https://www.naturalearthdata.com' },
  { what: 'Moon map tiles', who: 'OpenPlanetaryMap', url: 'https://github.com/openplanetary/opm' },
  { what: 'Globe', who: 'three-globe and react-globe.gl by Vasco Asturiano, with their example textures', url: 'https://github.com/vasturiano/react-globe.gl' },
];

/** The same, as plain lines for a CSV or a text file. */
export function creditLines(): string[] {
  return [
    `Data reused: ${GASTEINER.dataset} ${GASTEINER.datasetUrl}. Licence: ${GASTEINER.licence}, ${GASTEINER.licenceUrl}. ${GASTEINER.use}`,
    `Paper describing that database: ${GASTEINER.paper} ${GASTEINER.paperUrl}`,
    ...MAP_CREDITS.map(c => `${c.what}: ${c.who}, ${c.url}`),
  ];
}
