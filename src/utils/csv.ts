import type { Simulant, Composition, ChemicalComposition, Reference } from '../types';

function escapeCSV(value: unknown): string {
  if (value === null || value === undefined) return '';
  let str = String(value).replace(/\r?\n/g, ' ').trim();
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    str = '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

export function exportToCSV(
  simulants: Simulant[],
  compositions: Composition[],
  chemicalCompositions: ChemicalComposition[],
  references: Reference[],
  filename: string,
) {
  const columns: { key: keyof Simulant; label: string }[] = [
    { key: 'simulant_id', label: 'Simulant ID' },
    { key: 'name', label: 'Name' },
    { key: 'type', label: 'Type' },
    { key: 'country_code', label: 'Country' },
    { key: 'institution', label: 'Institution' },
    { key: 'availability', label: 'Availability' },
    { key: 'release_date', label: 'Release Date' },
    { key: 'tons_produced_mt', label: 'Tons Produced (MT)' },
    { key: 'specific_gravity', label: 'Specific Gravity' },
    { key: 'notes', label: 'Notes' },
    { key: 'lunar_sample_reference', label: 'Lunar Sample Reference' },
  ];

  const allMineralNames = [...new Set(compositions.map(c => c.component_name))].sort();
  const allChemicalNames = [...new Set(
    chemicalCompositions
      .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum')
      .map(c => c.component_name)
  )].sort();

  const headers = [
    ...columns.map(c => c.label),
    ...allMineralNames.map(n => `Mineral: ${n} (%)`),
    ...allChemicalNames.map(n => `Chemical: ${n} (wt%)`),
    'Composition Sources',
    'Usage Studies',
  ];

  const rows = simulants.map(s => {
    const row: string[] = columns.map(col => escapeCSV(s[col.key]));

    allMineralNames.forEach(name => {
      const m = compositions.find(c => c.simulant_id === s.simulant_id && c.component_name === name);
      row.push(m ? String(m.value_pct) : '');
    });

    allChemicalNames.forEach(name => {
      const c = chemicalCompositions.find(ch => ch.simulant_id === s.simulant_id && ch.component_name === name);
      row.push(c ? String(c.value_wt_pct) : '');
    });

    const simRefs = references.filter(r => r.simulant_id === s.simulant_id);
    const compRefs = simRefs.filter(r => r.reference_type === 'composition');
    const usageRefs = simRefs.filter(r => r.reference_type === 'usage' || !r.reference_type);

    row.push(escapeCSV(compRefs.map(r => r.reference_text).join(' | ')));
    row.push(escapeCSV(usageRefs.map(r => r.reference_text).join(' | ')));

    return row;
  });

  const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  downloadFile(csvContent, filename, 'text/csv;charset=utf-8;');
}

export function downloadFile(content: string, filename: string, mimeType: string) {
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

export function downloadSimulantCSV(
  simulant: Simulant,
  compositions: Composition[],
  chemicalCompositions: ChemicalComposition[],
  references: Reference[],
) {
  const timestamp = new Date().toISOString().slice(0, 10);
  const filename = `${simulant.name.replace(/[^a-z0-9]/gi, '_')}_${timestamp}.csv`;
  exportToCSV([simulant], compositions, chemicalCompositions, references, filename);
}
