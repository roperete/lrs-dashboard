import { LunarSite } from './types';

export const lunarSites: LunarSite[] = [
  {
    id: 'A11',
    name: 'Apollo 11 - Sea of Tranquility',
    mission: 'Apollo 11',
    date: 'July 20, 1969',
    lat: 0.67409,
    lng: 23.47297,
    samples_returned: '21.5 kg',
    description: 'First human landing on the Moon. Collected basaltic rocks and breccias.',
    type: 'Apollo'
  },
  {
    id: 'A12',
    name: 'Apollo 12 - Ocean of Storms',
    mission: 'Apollo 12',
    date: 'November 19, 1969',
    lat: -3.01239,
    lng: -23.42157,
    samples_returned: '34.3 kg',
    description: 'Landed near Surveyor 3. Collected basaltic samples from the Oceanus Procellarum.',
    type: 'Apollo'
  },
  {
    id: 'A14',
    name: 'Apollo 14 - Fra Mauro',
    mission: 'Apollo 14',
    date: 'February 5, 1971',
    lat: -3.64530,
    lng: -17.47136,
    samples_returned: '42.3 kg',
    description: 'Landed in the Fra Mauro highlands. Collected impact-derived breccias.',
    type: 'Apollo'
  },
  {
    id: 'A15',
    name: 'Apollo 15 - Hadley-Apennine',
    mission: 'Apollo 15',
    date: 'July 30, 1971',
    lat: 26.13222,
    lng: 3.63386,
    samples_returned: '77.3 kg',
    description: 'First use of the Lunar Roving Vehicle. Collected samples from the Apennine Front and Hadley Rille.',
    type: 'Apollo'
  },
  {
    id: 'A16',
    name: 'Apollo 16 - Descartes Highlands',
    mission: 'Apollo 16',
    date: 'April 21, 1972',
    lat: -8.97301,
    lng: 15.49812,
    samples_returned: '95.7 kg',
    description: 'Landed in the lunar highlands. Collected ancient crustal rocks (anorthosites).',
    type: 'Apollo'
  },
  {
    id: 'A17',
    name: 'Apollo 17 - Taurus-Littrow',
    mission: 'Apollo 17',
    date: 'December 11, 1972',
    lat: 20.19080,
    lng: 30.77168,
    samples_returned: '110.5 kg',
    description: 'Final Apollo mission. Collected orange soil and diverse rock types from a valley.',
    type: 'Apollo'
  },
  {
    id: 'L16',
    name: 'Luna 16 - Mare Fecunditatis',
    mission: 'Luna 16',
    date: 'September 20, 1970',
    lat: -0.68,
    lng: 56.30,
    samples_returned: '101 g',
    description: 'First robotic sample return mission. Collected mare basalt.',
    type: 'Luna'
  },
  {
    id: 'L20',
    name: 'Luna 20 - Apollonius Highlands',
    mission: 'Luna 20',
    date: 'February 21, 1972',
    lat: 3.53,
    lng: 56.55,
    samples_returned: '55 g',
    description: 'Robotic sample return from the highlands near Mare Fecunditatis.',
    type: 'Luna'
  },
  {
    id: 'L24',
    name: 'Luna 24 - Mare Crisium',
    mission: 'Luna 24',
    date: 'August 18, 1976',
    lat: 12.71,
    lng: 62.21,
    samples_returned: '170 g',
    description: 'Final Soviet Luna mission. Collected samples from Mare Crisium.',
    type: 'Luna'
  },
  {
    id: 'CE5',
    name: 'Chang\'e 5 - Oceanus Procellarum',
    mission: 'Chang\'e 5',
    date: 'December 1, 2020',
    lat: 43.0576,
    lng: -51.9161,
    samples_returned: '1.73 kg',
    description: 'First Chinese sample return mission. Collected young volcanic rocks.',
    type: 'Chang-e'
  },
  {
    id: 'CE6',
    name: 'Chang\'e 6 - South Pole-Aitken Basin',
    mission: 'Chang\'e 6',
    date: 'June 2, 2024',
    lat: -41.6385,
    lng: -153.9852,
    samples_returned: '1.93 kg',
    description: 'First sample return from the lunar far side. Collected samples from the Apollo crater.',
    type: 'Chang-e'
  }
];
