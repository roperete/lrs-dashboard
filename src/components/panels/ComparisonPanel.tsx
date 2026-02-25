import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ArrowRightLeft, X, Activity, FlaskConical } from 'lucide-react';
import { motion } from 'motion/react';
import type { Simulant, Composition, ChemicalComposition } from '../../types';

interface ComparisonPanelProps {
  simulant1: Simulant; composition1: Composition[]; chemicalComposition1: ChemicalComposition[];
  simulant2: Simulant; composition2: Composition[]; chemicalComposition2: ChemicalComposition[];
  onClose: () => void;
}

export function ComparisonPanel({
  simulant1, composition1, chemicalComposition1,
  simulant2, composition2, chemicalComposition2, onClose,
}: ComparisonPanelProps) {
  const mineralComparison = useMemo(() => {
    const all = new Set([...composition1.map(c => c.component_name), ...composition2.map(c => c.component_name)]);
    return Array.from(all).map(name => ({
      name,
      val1: composition1.find(c => c.component_name === name)?.value_pct || 0,
      val2: composition2.find(c => c.component_name === name)?.value_pct || 0,
    })).filter(d => d.val1 > 0 || d.val2 > 0).sort((a, b) => (b.val1 + b.val2) - (a.val1 + a.val2));
  }, [composition1, composition2]);

  const chemicalComparison = useMemo(() => {
    const all = new Set([...chemicalComposition1.map(c => c.component_name), ...chemicalComposition2.map(c => c.component_name)]);
    return Array.from(all).map(name => ({
      name,
      val1: chemicalComposition1.find(c => c.component_name === name)?.value_wt_pct || 0,
      val2: chemicalComposition2.find(c => c.component_name === name)?.value_wt_pct || 0,
    })).filter(d => d.val1 > 0 || d.val2 > 0).sort((a, b) => (b.val1 + b.val2) - (a.val1 + a.val2));
  }, [chemicalComposition1, chemicalComposition2]);

  return (
    <motion.div
      initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed bottom-0 left-0 right-0 h-[80vh] bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-[1001] overflow-y-auto shadow-2xl"
    >
      <div className="p-6 max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <ArrowRightLeft className="text-emerald-400" size={28} />
            <div>
              <h2 className="text-2xl font-bold text-white">Comparison</h2>
              <p className="text-slate-400 text-sm">
                <span className="text-emerald-400 font-semibold">{simulant1.name}</span>
                <span className="mx-2">vs</span>
                <span className="text-blue-400 font-semibold">{simulant2.name}</span>
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
            <X size={24} />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section>
            <div className="flex items-center gap-3 mb-4">
              <Activity className="text-emerald-400" size={20} />
              <h3 className="text-lg font-bold text-white">Mineral Comparison (%)</h3>
            </div>
            <div className="h-[350px] bg-slate-900/50 rounded-2xl p-4 border border-slate-800">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mineralComparison}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }} />
                  <Bar dataKey="val1" name={simulant1.name} fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="val2" name={simulant2.name} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section>
            <div className="flex items-center gap-3 mb-4">
              <FlaskConical className="text-blue-400" size={20} />
              <h3 className="text-lg font-bold text-white">Chemical Comparison (wt%)</h3>
            </div>
            <div className="h-[350px] bg-slate-900/50 rounded-2xl p-4 border border-slate-800">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chemicalComparison}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }} />
                  <Bar dataKey="val1" name={simulant1.name} fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="val2" name={simulant2.name} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      </div>
    </motion.div>
  );
}
