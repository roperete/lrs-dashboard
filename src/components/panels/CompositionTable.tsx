import React from 'react';
import { RefSup } from '../ui/RefSup';

interface TableRow {
  name: string;
  value: number;
  /** The lunar reference sample's value for the same component. */
  refValue?: number;
  /** Number of the document this row was read from, within the simulant's References list. */
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
}

export function CompositionTable({ data, valueLabel, refLabel, decimals = 2 }: CompositionTableProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const refTotal = refLabel ? data.reduce((sum, d) => sum + (d.refValue || 0), 0) : undefined;
  const fmt = (v: number) => v.toFixed(decimals);

  // One document behind every row: cite it once, in the column header. Several
  // documents, or some rows cited and others not: cite each row on its own.
  const cited = data.filter(r => r.refNumber != null);
  const distinct = new Set(cited.map(r => r.refNumber));
  const headerRef = distinct.size === 1 && cited.length === data.length ? cited[0] : undefined;
  const perRow = headerRef === undefined && cited.length > 0;

  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="text-left py-2 px-3 text-xs font-bold text-slate-500 uppercase">Name</th>
            <th className="text-right py-2 px-3 text-xs font-bold text-slate-500 uppercase">
              {valueLabel}
              {headerRef?.refNumber != null && (
                <RefSup n={headerRef.refNumber} fallback={headerRef.refTooltip} align="right" />
              )}
            </th>
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
                {perRow && row.refNumber != null && (
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
            <td className="py-2 px-3 text-slate-400" title="Sum of the rows listed above, as published by the source">Total</td>
            <td className="py-2 px-3 text-right text-slate-200 font-mono">{fmt(total)}</td>
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
