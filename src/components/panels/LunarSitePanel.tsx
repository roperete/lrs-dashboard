import React from 'react';
import { Info } from 'lucide-react';
import { PanelShell } from '../ui/PanelShell';
import { Tooltip } from '../ui/Tooltip';

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
import type { LunarSite } from '../../types';

interface LunarSitePanelProps {
  site: LunarSite;
  onClose: () => void;
}

export function LunarSitePanel({ site, onClose }: LunarSitePanelProps) {
  return (
    <PanelShell title={site.name} subtitle={site.mission} onClose={onClose} accentColor="text-amber-400">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
            <Label help={HELP.date} className="text-xs text-slate-500 uppercase font-bold mb-1">Date</Label>
            <p className="text-lg font-medium text-slate-200">{site.date}</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
            <Label help={HELP.samples} className="text-xs text-slate-500 uppercase font-bold mb-1">Samples</Label>
            <p className="text-lg font-medium text-slate-200">{site.samples_returned || 'N/A'}</p>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Info size={18} className="text-amber-400" />
            <h3 className="text-lg font-semibold text-slate-200">Mission Description</h3>
          </div>
          <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
            <p className="text-slate-400 leading-relaxed text-sm">{site.description}</p>
          </div>
        </div>
        {site.geotechnical && (
          <div>
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-3">In-Situ Geotechnical Properties</h3>
            <div className="grid grid-cols-2 gap-3">
              {site.geotechnical.bulk_density != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.bulk_density} className="text-[10px] text-slate-500 uppercase font-bold mb-1">Bulk Density</Label>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.bulk_density} g/cm³</p>
                </div>
              )}
              {site.geotechnical.friction_angle != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.friction_angle} className="text-[10px] text-slate-500 uppercase font-bold mb-1">Friction Angle</Label>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.friction_angle}°</p>
                </div>
              )}
              {site.geotechnical.cohesion != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.cohesion} className="text-[10px] text-slate-500 uppercase font-bold mb-1">Cohesion</Label>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.cohesion} kPa</p>
                </div>
              )}
              {site.geotechnical.bearing_capacity != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <Label help={HELP.bearing_capacity} className="text-[10px] text-slate-500 uppercase font-bold mb-1">Bearing Capacity</Label>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.bearing_capacity} kPa</p>
                </div>
              )}
            </div>
            <p className="text-[10px] text-slate-500 mt-2">
              Compiled from Gasteiner et al., <em>An Open Database of Lunar Regolith and Simulants Properties</em>.
              Not yet checked value by value against the original mission reports.
            </p>
          </div>
        )}
        <div className="bg-amber-900/20 p-4 rounded-xl border border-amber-500/20">
          <Label help={HELP.coordinates} className="text-xs text-amber-500 uppercase font-bold mb-1">Coordinates</Label>
          <p className="text-lg font-medium text-amber-200 font-mono">{site.lat.toFixed(4)}, {site.lng.toFixed(4)}</p>
        </div>
      </div>
    </PanelShell>
  );
}
