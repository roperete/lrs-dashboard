import React from 'react';
import { ArrowRightLeft, Download, X } from 'lucide-react';
import { motion } from 'motion/react';
import type { Simulant } from '../../types';
import { MAX_COMPARE } from '../../hooks/usePanelState';

interface CompareTrayProps {
  simulants: Simulant[];
  onRemove: (id: string) => void;
  onCompare: () => void;
  onExport?: () => void;
  onClear: () => void;
  /** Leave room for an open pane on the right. */
  paneOpen?: boolean;
}

/**
 * The one place simulants are collected for comparing (review #6). The pane's "Add to
 * compare", the table's and the list's checkboxes all put a chip here; Compare needs two.
 */
export function CompareTray({ simulants, onRemove, onCompare, onExport, onClear, paneOpen }: CompareTrayProps) {
  if (simulants.length === 0) return null;
  const ready = simulants.length >= 2;
  return (
    <motion.div
      initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }}
      role="region" aria-label="Compare tray"
      className={`fixed bottom-4 z-[1100] left-1/2 -translate-x-1/2 ${paneOpen ? 'sm:left-[calc(50%-225px)]' : ''} max-w-[calc(100vw-1rem)]`}
    >
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl">
        <span className="text-xs text-slate-400 pr-1">Compare</span>
        {simulants.map(s => (
          <span key={s.simulant_id} className="flex items-center gap-1 pl-2.5 pr-1 py-1 bg-slate-800 border border-slate-700 rounded-full text-xs text-slate-200">
            {s.name}
            <button onClick={() => onRemove(s.simulant_id)} aria-label={`Remove ${s.name} from the comparison`}
              className="p-0.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-700"><X size={12} /></button>
          </span>
        ))}
        {simulants.length < MAX_COMPARE && (
          <span className="text-[11px] text-slate-500">{ready ? `up to ${MAX_COMPARE}` : 'add one more'}</span>
        )}
        <button onClick={onCompare} disabled={!ready}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-400 text-slate-950 rounded-lg text-xs font-semibold transition-colors">
          <ArrowRightLeft size={13} />Compare{ready ? ` ${simulants.length}` : ''}
        </button>
        {onExport && (
          <button onClick={onExport} title="Export these simulants as CSV" aria-label="Export these simulants as CSV"
            className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800"><Download size={14} /></button>
        )}
        <button onClick={onClear} className="px-2 py-1 text-xs text-slate-400 hover:text-white">Clear</button>
      </div>
    </motion.div>
  );
}
