import React from 'react';
import type { PhysicalProperties } from '../../types';

const PROP_CONFIG: { key: keyof PhysicalProperties; label: string; unit: string }[] = [
  { key: 'bulk_density', label: 'Bulk Density', unit: 'g/cm³' },
  { key: 'density_g_cm3', label: 'Density', unit: 'g/cm³' },
  { key: 'specific_gravity', label: 'Specific Gravity', unit: '' },
  { key: 'cohesion', label: 'Cohesion', unit: 'kPa' },
  { key: 'friction_angle', label: 'Friction Angle', unit: '°' },
  { key: 'particle_size_d50', label: 'Particle Size D50', unit: 'μm' },
  { key: 'particle_size_distribution', label: 'Size Distribution', unit: '' },
  { key: 'particle_morphology', label: 'Morphology', unit: '' },
  { key: 'particle_ruggedness', label: 'Ruggedness', unit: '' },
  { key: 'glass_content_percent', label: 'Glass Content', unit: '%' },
  { key: 'nasa_fom_score', label: 'NASA FoM Score', unit: '' },
  { key: 'ti_content_percent', label: 'Ti Content', unit: '%' },
];

interface PhysicalPropertiesSectionProps {
  properties: PhysicalProperties;
}

export function PhysicalPropertiesSection({ properties }: PhysicalPropertiesSectionProps) {
  const entries = PROP_CONFIG.filter(({ key }) => properties[key] != null);

  if (entries.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Physical Properties</h3>
      <div className="grid grid-cols-2 gap-2">
        {entries.map(({ key, label, unit }) => (
          <div key={key} className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase font-bold mb-0.5">{label}</p>
            <p className="text-sm font-medium text-cyan-400">
              {String(properties[key])}{unit && <span className="text-slate-500 ml-1">{unit}</span>}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
