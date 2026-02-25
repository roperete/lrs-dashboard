import React from 'react';

interface TableRow {
  name: string;
  value: number;
  refValue?: number;
}

interface CompositionTableProps {
  data: TableRow[];
  valueLabel: string;
  refLabel?: string;
}

export function CompositionTable({ data, valueLabel, refLabel }: CompositionTableProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const refTotal = refLabel ? data.reduce((sum, d) => sum + (d.refValue || 0), 0) : undefined;

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
              <td className="py-1.5 px-3 text-right text-slate-200 font-mono">{row.value.toFixed(1)}</td>
              {refLabel && (
                <td className="py-1.5 px-3 text-right text-amber-400/70 font-mono">
                  {row.refValue !== undefined ? row.refValue.toFixed(1) : '-'}
                </td>
              )}
            </tr>
          ))}
          <tr className="border-t border-slate-700/50 font-bold">
            <td className="py-2 px-3 text-slate-400">Total</td>
            <td className="py-2 px-3 text-right text-slate-200 font-mono">{total.toFixed(1)}</td>
            {refLabel && (
              <td className="py-2 px-3 text-right text-amber-400/70 font-mono">
                {refTotal !== undefined ? refTotal.toFixed(1) : '-'}
              </td>
            )}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
