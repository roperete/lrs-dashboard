export const euMemberCountryCodes = [
  'AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 'FRA',
  'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD',
  'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE',
];

export function isEUMember(code: string): boolean {
  return code === 'EU' || euMemberCountryCodes.includes(code);
}

export const countryDisplayNames: Record<string, string> = {
  USA: 'United States',
  GBR: 'United Kingdom',
  CHN: 'China',
  JPN: 'Japan',
  DEU: 'Germany',
  FRA: 'France',
  ITA: 'Italy',
  KOR: 'South Korea',
  IND: 'India',
  CAN: 'Canada',
  AUS: 'Australia',
  BRA: 'Brazil',
  RUS: 'Russia',
  EU: 'European Union',
  POL: 'Poland',
  NOR: 'Norway',
  CHE: 'Switzerland',
  ISR: 'Israel',
  ARE: 'UAE',
  DNK: 'Denmark',
  NLD: 'Netherlands',
  ESP: 'Spain',
  AUT: 'Austria',
  FIN: 'Finland',
  BEL: 'Belgium',
  SWE: 'Sweden',
  CZE: 'Czech Republic',
  PRT: 'Portugal',
  HUN: 'Hungary',
  GRC: 'Greece',
  TWN: 'Taiwan',
};

export function getCountryDisplay(code: string): string {
  return countryDisplayNames[code] || code;
}

export function getCountryCode(geoJsonProps: Record<string, unknown>): string | null {
  const code = geoJsonProps['ISO_A3'] as string || geoJsonProps['iso_a3'] as string;
  if (!code || code === '-99') return null;
  return code;
}
