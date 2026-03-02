import React from 'react';
import type { PhysicalProperties } from '../../types';

const PROP_CONFIG: { key: keyof PhysicalProperties; label: string; unit: string; desc: string }[] = [
  { key: 'bulk_density', label: 'Bulk Density', unit: 'g/cm³', desc: 'Mass per unit volume including pore spaces between grains' },
  { key: 'density_g_cm3', label: 'Density', unit: 'g/cm³', desc: 'Solid grain density excluding inter-particle voids' },
  { key: 'specific_gravity', label: 'Specific Gravity', unit: '', desc: 'Ratio of grain density to water density (dimensionless)' },
  { key: 'cohesion', label: 'Cohesion', unit: 'kPa', desc: 'Shear strength at zero confining pressure — measures how well grains stick together' },
  { key: 'friction_angle', label: 'Friction Angle', unit: '°', desc: 'Internal angle of friction — controls slope stability and bearing capacity' },
  { key: 'particle_size_d50', label: 'Particle Size D50', unit: 'μm', desc: 'Median particle diameter — 50% of grains are smaller than this value' },
  { key: 'particle_size_distribution', label: 'Particle Size Distribution', unit: 'μm', desc: 'Range of particle sizes present in the simulant' },
  { key: 'particle_morphology', label: 'Morphology', unit: '', desc: 'Shape characteristics of individual grains (angular, rounded, etc.)' },
  { key: 'particle_ruggedness', label: 'Ruggedness', unit: '', desc: 'Surface roughness and irregularity of grain surfaces' },
  { key: 'glass_content_percent', label: 'Glass Content', unit: '%', desc: 'Proportion of amorphous glassy material — key for simulating agglutinates' },
  { key: 'nasa_fom_score', label: 'NASA FoM Score', unit: '', desc: 'NASA Figure of Merit — overall fidelity score comparing simulant to real regolith' },
  { key: 'ti_content_percent', label: 'Ti Content', unit: '%', desc: 'Titanium content — distinguishes high-Ti mare from low-Ti highland simulants' },
  { key: 'grain_size_mm', label: 'Grain Size', unit: 'mm', desc: 'Representative grain size or size range from the Gasteiner database' },
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
        {entries.map(({ key, label, unit, desc }) => (
          <div key={key} className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700/50">
            <p className="text-[10px] text-slate-500 uppercase font-bold mb-0.5 cursor-help" title={desc}>{label}</p>
            <p className="text-sm font-medium text-cyan-400">
              {String(properties[key])}{unit && <span className="text-slate-500 ml-1">{unit}</span>}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
