import React from 'react';
import { Info } from 'lucide-react';
import { PanelShell } from '../ui/PanelShell';
import { Tooltip } from '../ui/Tooltip';
import { LunarRefs, LunarSourceList } from '../ui/LunarRefs';
import { EMPTY_CITATIONS, type LunarCitations } from '../../utils/lunarCitations';

/** Explanations shown on hover over each label. */
const HELP = {
  date: 'Landing date.',
  samples: 'Mass of lunar material brought back to Earth. Only crewed and sample-return missions return any.',
  bulk_density: 'Bulk density of the regolith at the site: mass per volume including the pore space, from in-situ measurements or returned cores.',
  friction_angle: 'Internal angle of friction of the regolith, from in-situ soil-mechanics measurements. Governs slope stability and bearing capacity.',
  cohesion: 'Shear strength of the regolith at zero normal stress: how much the grains hold together.',
  bearing_capacity: 'Load per unit area the surface carries before it gives way, estimated from how far landers, footpads or penetrometers sank.',
  coordinates: 'Latitude and longitude of the landing point in degrees (selenographic; east and north positive).',
};

function Label({ help, children, className }: { help: string; children: React.ReactNode; className: string }) {
  return (
    <Tooltip text={help} align="left">
      <p className={`${className} border-b border-dotted border-slate-600`}>{children}</p>
    </Tooltip>
  );
}
import type { LunarSite, Simulant } from '../../types';

interface LunarSitePanelProps {
  site: LunarSite;
  /** Numbered sources of this site's values. */
  citations?: LunarCitations;
  /** Simulants whose producers say they replicate this site's material. */
  replicas?: Simulant[];
  onSelectSimulant?: (id: string) => void;
  onClose: () => void;
}

export function LunarSitePanel({ site, citations = EMPTY_CITATIONS, replicas = [], onSelectSimulant, onClose }: LunarSitePanelProps) {
  const refs = (...fields: string[]) => {
    const seen = new Set<number>();
    const cites = fields.flatMap(f => citations.cite(f)).filter(c => !seen.has(c.n) && !!seen.add(c.n));
    return <LunarRefs cites={cites} />;
  };
  const geo = site.geotechnical || {};
  const hasGeo = Object.values(geo).some(v => v != null);
  return (
    <PanelShell title={site.name} subtitle={site.mission} onClose={onClose} accentColor="text-amber-400" scrollKey={site.id}>
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
            <Label help={HELP.date} className="text-[11px] text-slate-400 font-semibold mb-1">Date</Label>
            <p className="text-lg font-medium text-slate-200">{site.date ?? '—'}{site.date && refs('date')}</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
            <Label help={HELP.samples} className="text-[11px] text-slate-400 font-semibold mb-1">Samples</Label>
            <p className="text-lg font-medium text-slate-200">{site.samples_returned || '—'}{site.samples_returned && refs('samples_returned')}</p>
          </div>
        </div>
        {site.description && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Info size={18} className="text-amber-400" />
            <h3 className="text-lg font-semibold text-slate-200">Mission Description</h3>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
            <p className="text-slate-400 leading-relaxed text-sm">{site.description}{refs('description')}</p>
          </div>
        </div>
        )}
        {hasGeo && (
          <div>
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">In-Situ Geotechnical Properties</h3>
            <div className="grid grid-cols-2 gap-3">
              {geo.bulk_density != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.bulk_density} className="text-[11px] text-slate-400 font-semibold mb-1">Bulk Density</Label>
                  <p className="text-sm font-medium text-slate-200">{geo.bulk_density} g/cm³{refs('bulk_density')}</p>
                </div>
              )}
              {geo.friction_angle != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.friction_angle} className="text-[11px] text-slate-400 font-semibold mb-1">Friction Angle</Label>
                  <p className="text-sm font-medium text-slate-200">{geo.friction_angle}°{refs('friction_angle')}</p>
                </div>
              )}
              {geo.cohesion != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.cohesion} className="text-[11px] text-slate-400 font-semibold mb-1">Cohesion</Label>
                  <p className="text-sm font-medium text-slate-200">{geo.cohesion} kPa{refs('cohesion')}</p>
                </div>
              )}
              {geo.bearing_capacity != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.bearing_capacity} className="text-[11px] text-slate-400 font-semibold mb-1">Bearing Capacity</Label>
                  <p className="text-sm font-medium text-slate-200">{geo.bearing_capacity} kPa{refs('bearing_capacity')}</p>
                </div>
              )}
            </div>
          </div>
        )}
        <p className="text-xs text-slate-400">
          <Tooltip text={HELP.coordinates} align="left"><span className="border-b border-dotted border-slate-600">Coordinates</span></Tooltip>{' '}
          <span className="font-mono text-slate-300">{site.lat}, {site.lng}</span>{refs('lat', 'lng')}
        </p>
        {replicas.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-slate-300 mb-2">Simulants that replicate this site</h3>
            <ul className="flex flex-wrap gap-1.5">
              {replicas.map(r => (
                <li key={r.simulant_id}>
                  <button onClick={() => onSelectSimulant?.(r.simulant_id)}
                    className="px-2.5 py-1 rounded-full border border-slate-700 text-xs text-slate-200 hover:border-emerald-500 hover:text-emerald-300">{r.name}</button>
                </li>
              ))}
            </ul>
            <p className="mt-1 text-[11px] text-slate-400">As each producer states the lunar sample it replicates.</p>
          </div>
        )}
        <LunarSourceList citations={citations} id="pane-sources" />
        <p className="text-[10px] text-slate-400">
          Each value is cited to the document that states it.
        </p>
      </div>
    </PanelShell>
  );
}
