import React from 'react';
import type { Simulant, SimulantExtra } from '../../types';
import { getInstitutionUrl } from '../../utils/institutionUrls';

interface SimulantPropertiesProps {
  simulant: Simulant;
  extra?: SimulantExtra;
}

export function SimulantProperties({ simulant, extra }: SimulantPropertiesProps) {
  // Combine lunar_sample_reference and replica_of into one field
  const lunarSampleRef = [simulant.lunar_sample_reference, extra?.replica_of]
    .filter(Boolean)
    .filter((v, i, a) => a.indexOf(v) === i) // dedupe
    .join(' / ') || null;

  const props: [string, string | number | null | undefined][] = [
    ['Type', simulant.type],
    ['Origin', simulant.country_code],
    ['Institution', simulant.institution],
    ['Availability', simulant.availability],
    ['Release Date', simulant.release_date],
    ['Specific Gravity', simulant.specific_gravity],
    ['Lunar Sample Reference', lunarSampleRef],
    ['Production (MT)', simulant.tons_produced_mt],
  ];

  if (extra) {
    if (extra.classification) props.push(['Classification', extra.classification]);
    if (extra.application) props.push(['Application', extra.application]);
    if (extra.feedstock) props.push(['Feedstock', extra.feedstock]);
    if (extra.grain_size_mm) props.push(['Grain Size (mm)', extra.grain_size_mm]);
    if (extra.petrographic_class) {
      let petroDisplay = extra.petrographic_class;
      try {
        const parsed = JSON.parse(extra.petrographic_class);
        if (parsed?.Rocks) {
          petroDisplay = Object.entries(parsed.Rocks as Record<string, number>)
            .filter(([, v]) => v > 0)
            .sort(([, a], [, b]) => b - a)
            .map(([k, v]) => `${k} ${v}%`)
            .join(', ') || extra.petrographic_class;
        }
      } catch { /* plain string, use as-is */ }
      props.push(['Petrographic Class', petroDisplay]);
    }
  }

  const institutionUrl = simulant.institution ? getInstitutionUrl(simulant.institution) : null;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {props.map(([label, value]) => (
          <div key={label as string} className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">{label}</p>
            {label === 'Institution' && institutionUrl ? (
              <a href={institutionUrl} target="_blank" rel="noopener noreferrer"
                className="text-sm font-medium text-emerald-400 hover:text-emerald-300 transition-colors">
                {String(value || 'N/A')}
              </a>
            ) : (
              <p className="text-sm font-medium text-slate-200">{value != null && value !== '' ? String(value) : 'N/A'}</p>
            )}
          </div>
        ))}
      </div>

      {simulant.notes && (
        <div className="bg-slate-800/30 p-3 rounded-xl border border-slate-700/30">
          <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Notes</p>
          <p className="text-sm text-slate-300 leading-relaxed">{simulant.notes}</p>
        </div>
      )}
    </div>
  );
}
