import React from 'react';
import { RefSup } from '../ui/RefSup';

interface TableRow {
  name: string;
  value: number;
  /** The lunar reference sample's value for the same component. */
  refValue?: number;
  /** Number of the document this row was read from, within the simulant's References list.
   *  Shown on the row itself, even when every row cites the same document: a reader
   *  checking one value should not have to look elsewhere for its source. */
  refNumber?: number;
  /** Hover text for that citation: the document's title. */
  refTooltip?: string;
}

interface CompositionTableProps {
  data: TableRow[];
  valueLabel: string;
  refLabel?: string;
  /** Decimal places shown. Manufacturer sheets report oxides to two decimals; rounding
   *  to one hid 0.06 as 0.1 and made the total disagree with the rows. Default 2. */
  decimals?: number;
  /** Below this sum the table is a partial analysis — only the components a source states —
   *  and a "Total" would read as a failed analysis (NEU-1B's lone TiO2 row "totalled" 6.50%). */
  partialBelow?: number;
}

export function CompositionTable({ data, valueLabel, refLabel, decimals = 2, partialBelow }: CompositionTableProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const partial = partialBelow !== undefined && total < partialBelow;
  const refTotal = refLabel ? data.reduce((sum, d) => sum + (d.refValue || 0), 0) : undefined;
  const fmt = (v: number) => v.toFixed(decimals);

  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="text-left py-2 px-3 text-xs font-bold text-slate-500 uppercase">Name</th>
            <th className="text-right py-2 px-3 text-xs font-bold text-slate-500 uppercase">{valueLabel}</th>
            {refLabel && (
              <th className="text-right py-2 px-3 text-xs font-bold text-amber-500/70 uppercase">{refLabel}</th>
            )}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.name} className={i % 2 === 0 ? 'bg-slate-800/20' : ''}>
              <td className="py-1.5 px-3 text-slate-300">{row.name}</td>
              <td className="py-1.5 px-3 text-right text-slate-200 font-mono">
                {fmt(row.value)}
                {row.refNumber != null && (
                  <RefSup n={row.refNumber} fallback={row.refTooltip} align="right" />
                )}
              </td>
              {refLabel && (
                <td className="py-1.5 px-3 text-right text-amber-400/70 font-mono">
                  {row.refValue !== undefined ? fmt(row.refValue) : '-'}
                </td>
              )}
            </tr>
          ))}
          <tr className="border-t border-slate-700/50 font-bold">
            <td className="py-2 px-3 text-slate-400" title={partial
              ? 'The source states only these components, so there is no total to show.'
              : 'Sum of the rows listed above, as published by the source'}>{partial ? 'Partial analysis' : 'Total'}</td>
            <td className="py-2 px-3 text-right text-slate-500 font-mono">{partial ? '—' : <span className="text-slate-200">{fmt(total)}</span>}</td>
            {refLabel && (
              <td className="py-2 px-3 text-right text-amber-400/70 font-mono">
                {refTotal !== undefined ? fmt(refTotal) : '-'}
              </td>
            )}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
