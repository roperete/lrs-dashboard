import React, { useState, useRef, useEffect } from 'react';
import { Download, ChevronDown } from 'lucide-react';
import { exportToCSV } from '../../utils/csv';
import type { Simulant, Composition, ChemicalComposition, Reference, PropertySource, FigureOfMerit } from '../../types';

interface ExportMenuProps {
  currentSimulant: Simulant | null;
  filteredSimulants: Simulant[];
  allSimulants: Simulant[];
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  propertySources?: PropertySource[];
  figuresOfMerit?: FigureOfMerit[];
}

export function ExportMenu({
  currentSimulant, filteredSimulants, allSimulants,
  compositions, chemicalCompositions, references, propertySources, figuresOfMerit,
}: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const timestamp = new Date().toISOString().slice(0, 10);

  const doExport = (simulants: Simulant[], label: string) => {
    exportToCSV(simulants, { compositions, chemicalCompositions, references, propertySources, figuresOfMerit }, `lrs_${label}_${timestamp}.csv`);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} aria-haspopup="menu" aria-expanded={open}
        className="flex items-center gap-1.5 px-3 h-10 hover:bg-slate-800 rounded-lg text-sm text-slate-300 hover:text-white transition-colors">
        <Download size={16} />
        <span className="hidden md:inline">Export</span>
        <ChevronDown size={12} />
      </button>
      {open && (
        <div role="menu" className="absolute top-full right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden min-w-[180px] z-[200]">
          {currentSimulant && (
            <button onClick={() => doExport([currentSimulant], currentSimulant.name.replace(/[^a-z0-9]/gi, '_'))}
              className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700 transition-colors">
              Export Current Simulant
            </button>
          )}
          <button onClick={() => doExport(filteredSimulants, 'filtered')}
            className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700 transition-colors">
            Export Filtered ({filteredSimulants.length})
          </button>
          <button onClick={() => doExport(allSimulants, 'all')}
            className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700 transition-colors">
            Export All ({allSimulants.length})
          </button>
        </div>
      )}
    </div>
  );
}
