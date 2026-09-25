import React from 'react';
import { Tooltip } from '../ui/Tooltip';
import { RefSup } from '../ui/RefSup';
import type { PhysicalProperties, PropertySource } from '../../types';

const PROP_CONFIG: { key: keyof PhysicalProperties; label: string; unit: string; desc: string }[] = [
  { key: 'bulk_density', label: 'Bulk Density', unit: 'g/cm³', desc: 'Mass per unit volume including pore spaces between grains' },
  { key: 'bulk_density_range', label: 'Bulk Density Range', unit: '', desc: 'Minimum to maximum, or loose to settled, as stated on the data sheet' },
  { key: 'density_g_cm3', label: 'Density', unit: 'g/cm³', desc: 'Solid grain density excluding inter-particle voids' },
  { key: 'specific_gravity', label: 'Specific Gravity', unit: '', desc: 'Ratio of grain density to water density (dimensionless)' },
  { key: 'cohesion', label: 'Cohesion', unit: 'kPa', desc: 'Shear strength at zero confining pressure — measures how well grains stick together' },
  { key: 'friction_angle', label: 'Friction Angle', unit: '°', desc: 'Internal angle of friction — controls slope stability and bearing capacity' },
  { key: 'angle_of_repose', label: 'Angle of Repose', unit: '', desc: 'Steepest stable slope of a poured pile, with the sample mass used, as stated on the data sheet' },
  { key: 'ph', label: 'pH', unit: '', desc: 'pH of the simulant as stated on the data sheet; the property that matters most for plant growth and bioremediation' },
  { key: 'particle_size_d50', label: 'Particle Size D50', unit: 'μm', desc: 'Median particle diameter — 50% of grains are smaller than this value' },
  { key: 'particle_size_mean_um', label: 'Mean Particle Size', unit: 'μm', desc: 'Arithmetic mean particle diameter as stated on the data sheet' },
  { key: 'particle_size_distribution', label: 'Particle Size Distribution', unit: 'μm', desc: 'Range of particle sizes present in the simulant' },
  { key: 'magnetic_susceptibility', label: 'Magnetic Susceptibility', unit: '', desc: 'Mass magnetic susceptibility as stated on the data sheet' },
  { key: 'particle_morphology', label: 'Morphology', unit: '', desc: 'Shape characteristics of individual grains (angular, rounded, etc.)' },
  { key: 'particle_ruggedness', label: 'Ruggedness', unit: '', desc: 'Surface roughness and irregularity of grain surfaces' },
  { key: 'glass_content_percent', label: 'Glass Content', unit: '%', desc: 'Proportion of amorphous glassy material — key for simulating agglutinates' },
  { key: 'nasa_fom_score', label: 'NASA FoM score', unit: '%', desc: 'NASA Figure of Merit — overall fidelity score comparing simulant to real regolith' },
  { key: 'ti_content_percent', label: 'Ti Content', unit: '%', desc: 'Titanium content — distinguishes high-Ti mare from low-Ti highland simulants' },
  { key: 'grain_size_mm', label: 'Grain Size', unit: 'mm', desc: 'Representative grain size or size range from the Gasteiner database' },
];

/** A text value that already names a unit ("<1mm", "0–90 μm") gets no second one. */
function statesOwnUnit(v: unknown): boolean {
  return typeof v === 'string' && /[a-zµμ°%]/i.test(v);
}

interface PhysicalPropertiesSectionProps {
  properties: PhysicalProperties;
  /** property_sources rows of this simulant keyed by field. The export nulls any scalar
   *  without a row, so normally every value shown has one; grain_size_mm, which comes
   *  from the Gasteiner database rather than the simulants table, never does. */
  sources?: Map<string, PropertySource>;
  /** Number of a reference within this simulant's list; see utils/references.ts. */
  refNumber?: (referenceId: string) => number | undefined;
  /** "Author et al. (year). Title" of a reference, the first line of its citation hover. */
  refLabel?: (referenceId: string) => string | undefined;
}

export function PhysicalPropertiesSection({ properties, sources, refNumber, refLabel }: PhysicalPropertiesSectionProps) {
  const entries = PROP_CONFIG.filter(({ key }) => properties[key] != null);

  if (entries.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Physical Properties</h3>
      <div className="grid grid-cols-2 gap-2">
        {entries.map(({ key, label, unit, desc }) => {
          const source = sources?.get(key);
          const n = source ? refNumber?.(source.reference_id) : undefined;
          return (
            <div key={key} className="bg-slate-800/50 p-2.5 rounded-lg border border-slate-700/50">
              <Tooltip text={desc} align="left">
                <p className="text-[11px] text-slate-400 font-semibold mb-0.5 border-b border-dotted border-slate-600">{label}</p>
              </Tooltip>
              <p className="text-sm font-medium text-cyan-400">
                {String(properties[key])}
                {unit && !statesOwnUnit(properties[key]) && <span className="text-slate-400 ml-1">{unit}</span>}
                {source && n != null && <RefSup n={n} location={source.location} quote={source.quote} align="left" source={refLabel?.(source.reference_id)} />}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
