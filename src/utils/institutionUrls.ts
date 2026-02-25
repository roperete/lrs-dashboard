export const institutionUrls: Record<string, string> = {
  'NASA': 'https://www.nasa.gov',
  'ESA': 'https://www.esa.int',
  'JAXA': 'https://www.jaxa.jp/en/',
  'CNES': 'https://cnes.fr/en',
  'DLR': 'https://www.dlr.de/en',
  'ISRO': 'https://www.isro.gov.in',
  'CSA': 'https://www.asc-csa.gc.ca/eng/',
  'CNSA': 'https://www.cnsa.gov.cn',
};

export function getInstitutionUrl(institution: string): string | null {
  for (const [key, url] of Object.entries(institutionUrls)) {
    if (institution.toUpperCase().includes(key)) return url;
  }
  return null;
}
