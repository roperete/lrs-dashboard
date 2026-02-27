import React from 'react';
import { Info } from 'lucide-react';
import { PanelShell } from '../ui/PanelShell';
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
            <p className="text-xs text-slate-500 uppercase font-bold mb-1">Date</p>
            <p className="text-lg font-medium text-slate-200">{site.date}</p>
          </div>
          <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
            <p className="text-xs text-slate-500 uppercase font-bold mb-1">Samples</p>
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
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Bulk Density</p>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.bulk_density} g/cm³</p>
                </div>
              )}
              {site.geotechnical.friction_angle != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Friction Angle</p>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.friction_angle}°</p>
                </div>
              )}
              {site.geotechnical.cohesion != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Cohesion</p>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.cohesion} kPa</p>
                </div>
              )}
              {site.geotechnical.bearing_capacity != null && (
                <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                  <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Bearing Capacity</p>
                  <p className="text-sm font-medium text-slate-200">{site.geotechnical.bearing_capacity} kPa</p>
                </div>
              )}
            </div>
            <p className="text-[10px] text-slate-600 mt-2">Source: Gasteiner et al. 2025 Open Database</p>
          </div>
        )}
        <div className="bg-amber-900/20 p-4 rounded-xl border border-amber-500/20">
          <p className="text-xs text-amber-500 uppercase font-bold mb-1">Coordinates</p>
          <p className="text-lg font-medium text-amber-200 font-mono">{site.lat.toFixed(4)}, {site.lng.toFixed(4)}</p>
        </div>
      </div>
    </PanelShell>
  );
}
