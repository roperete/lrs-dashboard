import React from 'react';
import type { Simulant, SimulantExtra, PropertySource } from '../../types';
import { getInstitutionUrl } from '../../utils/institutionUrls';
import { getCountryDisplay } from '../../utils/countryUtils';
import { RefSup } from '../ui/RefSup';

interface SimulantPropertiesProps {
  simulant: Simulant;
  extra?: SimulantExtra;
  /** property_sources rows of this simulant keyed by field, for citation marks. */
  sources?: Map<string, PropertySource>;
  refNumber?: (referenceId: string) => number | undefined;
  refLabel?: (referenceId: string) => string | undefined;
}

/**
 * "About": the identity of the simulant as a compact list (review #9). Empty fields are left
 * out, Type is the pane's subtitle and Availability sits under Purchase, so neither repeats
 * here. A value traced to a document carries its mark; the others say so in the footnote.
 */
export function SimulantProperties({ simulant, extra, sources, refNumber, refLabel }: SimulantPropertiesProps) {
  const lunarSampleRef = [simulant.lunar_sample_reference, extra?.replica_of]
    .filter(Boolean)
    .filter((v, i, a) => a.indexOf(v) === i)
    .join(' / ') || null;

  let petrographic: string | null = extra?.petrographic_class || null;
  if (petrographic) {
    try {
      const parsed = JSON.parse(petrographic);
      if (parsed?.Rocks) {
        petrographic = Object.entries(parsed.Rocks as Record<string, number>)
          .filter(([, v]) => v > 0).sort(([, a], [, b]) => b - a).map(([k, v]) => `${k} ${v}%`).join(', ') || petrographic;
      }
    } catch { /* plain string */ }
  }

  const rows: { label: string; value: string | number | null | undefined; field?: string }[] = [
    { label: 'Producer', value: simulant.institution, field: 'institution' },
    { label: 'Country', value: getCountryDisplay(simulant.country_code), field: 'country_code' },
    { label: 'Released', value: simulant.release_date, field: 'release_date' },
    { label: 'Lunar sample it replicates', value: lunarSampleRef, field: 'lunar_sample_reference' },
    { label: 'Product grade', value: simulant.product_grade, field: 'product_grade' },
    { label: 'Produced (t)', value: simulant.tons_produced_mt, field: 'tons_produced_mt' },
    { label: 'Classification', value: extra?.classification },
    { label: 'Application', value: extra?.application },
    { label: 'Feedstock', value: extra?.feedstock },
    { label: 'Petrographic class', value: petrographic },
  ].filter(r => r.value != null && r.value !== '' && r.value !== 'N/A');

  const institutionUrl = simulant.institution ? getInstitutionUrl(simulant.institution) : null;
  const unsourced = rows.some(r => !(r.field && sources?.get(r.field)));

  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-1.5 text-sm">
        {rows.map(({ label, value, field }) => {
          const src = field ? sources?.get(field) : undefined;
          const n = src ? refNumber?.(src.reference_id) : undefined;
          return (
            <React.Fragment key={label}>
              <dt className="text-slate-400">{label}</dt>
              <dd className="text-slate-200 min-w-0 break-words">
                {label === 'Producer' && institutionUrl
                  ? <a href={institutionUrl} target="_blank" rel="noopener noreferrer" className="text-emerald-400 hover:text-emerald-300">{String(value)}</a>
                  : String(value)}
                {src && n != null && <RefSup n={n} location={src.location} quote={src.quote} source={refLabel?.(src.reference_id)} align="left" />}
              </dd>
            </React.Fragment>
          );
        })}
      </dl>
      {simulant.notes && (
        <p className="text-sm text-slate-300 leading-relaxed"><span className="text-slate-400">Notes: </span>{simulant.notes}</p>
      )}
      {unsourced && <p className="text-[11px] text-slate-500">Values without a mark are not yet traced to a document.</p>}
    </div>
  );
}
