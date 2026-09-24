import React from 'react';
import { Tooltip } from '../ui/Tooltip';
import { RefSup } from '../ui/RefSup';
import type { FigureOfMerit } from '../../types';

/** What a Figure of Merit is, shown on hover over the section heading. */
const FOM_HELP =
  'A Figure of Merit (NASA, Schrader et al. 2010) scores how closely a simulant matches a lunar reference ' +
  'material, one property at a time: 1 (or 100%) is identical, 0 is no match. Each score below is as the ' +
  'cited document prints it, against the lunar material that document names.';

const PROPERTY_HELP: Record<string, string> = {
  composition: 'How closely the bulk chemistry matches the lunar reference.',
  mineralogy: 'How closely the mineral content matches the lunar reference.',
  particle_size: 'How closely the particle size distribution matches the lunar reference.',
  shape: 'How closely the particle shapes match the lunar reference.',
  density: 'How closely the density matches the lunar reference.',
  overall: 'A single score combining the property scores, as the document computes it.',
  other: 'A score the document defines; see the citation.',
};

const ORDER = ['overall', 'composition', 'mineralogy', 'particle_size', 'shape', 'density', 'other'];

interface Props {
  foms: FigureOfMerit[];
  /** Number of a reference within this simulant's list; see utils/references.ts. */
  refNumber: (referenceId: string) => number | undefined;
  /** First line of a citation hover: which document the score is from. */
  refLabel?: (referenceId: string) => string | undefined;
}

export function FigureOfMeritSection({ foms, refNumber, refLabel }: Props) {
  if (foms.length === 0) return null;
  const rows = [...foms].sort((a, b) => ORDER.indexOf(a.property) - ORDER.indexOf(b.property)
    || (a.reference_sample || '').localeCompare(b.reference_sample || ''));
  return (
    <div className="space-y-3">
      <Tooltip text={FOM_HELP} align="left">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-dotted border-slate-600">Figures of Merit</h3>
      </Tooltip>
      <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="text-left py-2 px-3 text-xs font-bold text-slate-500 uppercase">
                <Tooltip text="The property the score compares." align="left"><span>Property</span></Tooltip>
              </th>
              <th className="text-left py-2 px-3 text-xs font-bold text-slate-500 uppercase">
                <Tooltip text="The lunar material the score is computed against, as the cited document names it." align="left"><span>Against</span></Tooltip>
              </th>
              <th className="text-right py-2 px-3 text-xs font-bold text-slate-500 uppercase">
                <Tooltip text="The score as printed, on the document's own scale (0–1 or 0–100 / %)." align="right"><span>Score</span></Tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((f, i) => {
              const n = refNumber(f.reference_id);
              return (
                <tr key={f.fom_id} className={i % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-1.5 px-3 text-slate-300">
                    <Tooltip text={PROPERTY_HELP[f.property] || PROPERTY_HELP.other} align="left"><span>{f.property_label}</span></Tooltip>
                  </td>
                  <td className="py-1.5 px-3 text-slate-400 text-xs">{f.reference_sample || '—'}</td>
                  <td className="py-1.5 px-3 text-right text-slate-200 font-mono whitespace-nowrap">
                    {f.score_text || f.score}
                    {f.scale && !String(f.score_text || '').includes('%') && f.scale.includes('%') ? '%' : ''}
                    {n != null && <RefSup n={n} location={f.location} quote={f.quote} align="right" source={refLabel?.(f.reference_id)} />}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
