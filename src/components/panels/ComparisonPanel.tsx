import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowRightLeft, X, Activity, FlaskConical, BarChart3, TableProperties, Ruler } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../utils/cn';
import { RefSup } from '../ui/RefSup';
import { referenceNumbers, referenceHoverLabel, rowCitationTooltip } from '../../utils/references';
import type { Simulant, Composition, ChemicalComposition, Reference, PropertySource } from '../../types';

type ViewMode = 'chart' | 'table';

/** One side of a row: the value a source states for that simulant, or null when none does. */
interface Cell { value: number | null; n?: number; source?: string; location?: string | null; quote?: string | null; stated?: string | null }
interface Row { name: string; cells: Cell[] }

interface Side {
  simulant: Simulant;
  composition: Composition[];
  chemical: ChemicalComposition[];
  references: Reference[];
  sources?: Map<string, PropertySource>;
}

interface ComparisonPanelProps {
  simulants: Simulant[];
  compositionBySimulant: Map<string, Composition[]>;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  referencesBySimulant: Map<string, Reference[]>;
  propertySourcesBySimulant?: Map<string, Map<string, PropertySource>>;
  onClose: () => void;
}

/** One colour per column, A to D. */
const COLOURS = [
  { text: 'text-emerald-400', fill: '#10b981' },
  { text: 'text-blue-400', fill: '#3b82f6' },
  { text: 'text-violet-400', fill: '#8b5cf6' },
  { text: 'text-orange-400', fill: '#f97316' },
];
const LETTERS = ['A', 'B', 'C', 'D'];

const PHYSICAL: { label: string; key: keyof Simulant }[] = [
  { label: 'Specific gravity', key: 'specific_gravity' },
  { label: 'Bulk density (g/cm³)', key: 'bulk_density' },
  { label: 'Particle density (g/cm³)', key: 'density_g_cm3' },
  { label: 'Cohesion (kPa)', key: 'cohesion' },
  { label: 'Friction angle (°)', key: 'friction_angle' },
  { label: 'Particle size D50 (µm)', key: 'particle_size_d50' },
  { label: 'Glass content (%)', key: 'glass_content_percent' },
];

function cite(side: Side, referenceId: string | null | undefined) {
  if (!referenceId) return {};
  const numbers = referenceNumbers(side.references);
  return { n: numbers.get(referenceId), source: referenceHoverLabel(side.references.find(r => r.reference_id === referenceId)) };
}

function compositionRows(sides: Side[], pick: (s: Side) => { name: string; value: number; reference_id?: string | null; value_text?: string | null }[]): Row[] {
  const maps = sides.map(side => new Map(pick(side).map(r => [r.name, r] as const)));
  const cell = (side: Side, r?: { value: number; reference_id?: string | null; value_text?: string | null }): Cell =>
    r ? { value: r.value, stated: r.value_text, ...cite(side, r.reference_id) } : { value: null };
  const total = (row: Row) => row.cells.reduce((t, c) => t + (c.value ?? 0), 0);
  return [...new Set(maps.flatMap(m => [...m.keys()]))]
    .map(name => ({ name, cells: sides.map((side, i) => cell(side, maps[i].get(name))) }))
    .sort((x, y) => total(y) - total(x));
}

export function ComparisonPanel({
  simulants, compositionBySimulant, chemicalBySimulant, referencesBySimulant, propertySourcesBySimulant, onClose,
}: ComparisonPanelProps) {
  // Table first: it is the view that carries the citations (the charts cannot).
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const sides: Side[] = useMemo(() => simulants.map(sim => ({
    simulant: sim,
    composition: compositionBySimulant.get(sim.simulant_id) || [],
    chemical: chemicalBySimulant.get(sim.simulant_id) || [],
    references: referencesBySimulant.get(sim.simulant_id) || [],
    sources: propertySourcesBySimulant?.get(sim.simulant_id),
  })), [simulants, compositionBySimulant, chemicalBySimulant, referencesBySimulant, propertySourcesBySimulant]);

  const minerals = useMemo(() => compositionRows(sides, s => s.composition.map(c => ({ name: c.component_name, value: c.value_pct, reference_id: c.reference_id, value_text: c.value_text }))), [sides]);
  const chemistry = useMemo(() => compositionRows(sides, s => s.chemical
    .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum')
    .map(c => ({ name: c.component_name, value: c.value_wt_pct, reference_id: c.reference_id, value_text: c.value_text }))), [sides]);
  const physical = useMemo(() => PHYSICAL.map(p => ({
    name: p.label,
    cells: sides.map((side): Cell => {
      const v = side.simulant[p.key];
      const x = v == null || v === '' ? null : Number(v);
      if (x == null || !Number.isFinite(x)) return { value: null };
      const src = side.sources?.get(String(p.key));
      return { value: x, location: src?.location, quote: src?.quote, ...cite(side, src?.reference_id) };
    }),
  })).filter(r => r.cells.some(c => c.value != null)), [sides]);

  // Mineral tables that share few names come from different classifications (modal minerals
  // against rock types, say); the rows then mostly have values for some simulants only.
  const shared = minerals.filter(r => r.cells.every(c => c.value != null)).length;
  const vocabularyNote = minerals.length > 3 && shared / minerals.length < 0.5;
  const names = simulants.map(s => s.name);

  const toolbarButton = (mode: ViewMode, icon: React.ReactNode, label: string) => (
    <button onClick={() => setViewMode(mode)}
      className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
        viewMode === mode ? "bg-emerald-500/20 text-emerald-400" : "text-slate-400 hover:text-slate-200")}>
      {icon}{label}
    </button>
  );

  return (
    <motion.div
      initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed bottom-0 left-0 right-0 h-[80vh] bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-[1150] overflow-y-auto shadow-2xl"
    >
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <ArrowRightLeft className="text-emerald-400" size={28} />
            <div>
              <h2 className="text-2xl font-bold text-white">Comparison</h2>
              <p className="text-slate-400 text-sm flex flex-wrap gap-x-3">
                {simulants.map((s, i) => <span key={s.simulant_id} className={cn(COLOURS[i].text, "font-semibold")}>{LETTERS[i]}: {s.name}</span>)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700">
              {toolbarButton('table', <TableProperties size={14} />, 'Table')}
              {toolbarButton('chart', <BarChart3 size={14} />, 'Chart')}
            </div>
            <button onClick={onClose} aria-label="Close comparison" className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
              <X size={24} />
            </button>
          </div>
        </div>

        <p className="text-xs text-slate-400 mb-6">
          "—" means no source on record gives that value; it is not zero.{simulants.length === 2 && ' Δ is A − B, shown only when both have a value.'}
          {vocabularyNote && ' The mineral tables use different classifications, so most mineral rows have values for some simulants only.'}
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {viewMode === 'chart' ? (
            <>
              <ChartSection title="Minerals (%)" icon={<Activity className="text-emerald-400" size={20} />} rows={minerals} names={names} />
              <ChartSection title="Oxides (wt%)" icon={<FlaskConical className="text-blue-400" size={20} />} rows={chemistry} names={names} />
            </>
          ) : (
            <>
              <ComparisonTable title="Minerals (%)" icon={<Activity className="text-emerald-400" size={20} />} rows={minerals} names={names} />
              <ComparisonTable title="Oxides (wt%)" icon={<FlaskConical className="text-blue-400" size={20} />} rows={chemistry} names={names} />
            </>
          )}
          {physical.length > 0 && (
            <ComparisonTable title="Physical properties" icon={<Ruler className="text-amber-400" size={20} />} rows={physical} names={names} />
          )}
        </div>
      </div>
    </motion.div>
  );
}

function ChartSection({ title, icon, rows, names }: { title: string; icon: React.ReactNode; rows: Row[]; names: string[] }) {
  // null, not 0, for a value no source gives: the bar is left out rather than drawn at zero
  const data = rows.map(r => Object.fromEntries([['name', r.name], ...r.cells.map((c, i) => [`v${i}`, c.value])]));
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">{icon}<h3 className="text-lg font-bold text-white">{title}</h3></div>
      <div className="h-[350px] bg-slate-900/50 rounded-2xl p-4 border border-slate-800">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-45} textAnchor="end" height={60} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }} />
            {names.map((n, i) => <Bar key={n} dataKey={`v${i}`} name={n} fill={COLOURS[i].fill} radius={[4, 4, 0, 0]} />)}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function ValueCell({ cell }: { cell: Cell; key?: React.Key }) {
  if (cell.value == null) return <td className="py-2 px-4 text-right font-mono text-slate-500">—</td>;
  return (
    <td className="py-2 px-4 text-right font-mono text-slate-200 whitespace-nowrap">
      {cell.value.toFixed(2)}
      {cell.n != null && (
        <RefSup n={cell.n} source={cell.source} location={cell.location} quote={cell.quote}
          fallback={rowCitationTooltip(cell.stated, undefined)} align="right" />
      )}
    </td>
  );
}

function ComparisonTable({ title, icon, rows, names }: { title: string; icon: React.ReactNode; rows: Row[]; names: string[] }) {
  const pair = names.length === 2;
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">{icon}<h3 className="text-lg font-bold text-white">{title}</h3></div>
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="py-2.5 px-4 text-left text-xs font-semibold text-slate-400">Component</th>
              {names.map((n, i) => (
                <th key={n} className={cn("py-2.5 px-4 text-right text-xs font-semibold truncate max-w-[140px]", COLOURS[i].text)}>{LETTERS[i]}: {n}</th>
              ))}
              {pair && <th className="py-2.5 px-4 text-right text-xs font-semibold text-slate-400">Δ A − B</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const [a, b] = row.cells;
              const diff = pair && a.value != null && b.value != null ? a.value - b.value : null;
              return (
                <tr key={row.name} className={i % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-2 px-4 text-slate-300 font-medium">{row.name}</td>
                  {row.cells.map((c, j) => <ValueCell key={j} cell={c} />)}
                  {pair && (
                    <td className={cn("py-2 px-4 text-right font-mono text-xs",
                      diff == null ? "text-slate-500" : diff > 0 ? "text-emerald-400" : diff < 0 ? "text-blue-400" : "text-slate-400")}>
                      {diff == null ? '—' : `${diff > 0 ? '+' : diff < 0 ? '\u2212' : ''}${Math.abs(diff).toFixed(2)}`}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div className="flex items-center justify-center h-20 text-slate-400 text-sm">None of these simulants has values here.</div>
        )}
      </div>
    </section>
  );
}
