import React from 'react';
import { Info } from 'lucide-react';
import type { Reference } from '../../types';

interface ReferencesSectionProps {
  references: Reference[];
}

export function ReferencesSection({ references }: ReferencesSectionProps) {
  const compSources = references.filter(r => r.reference_type === 'composition');
  const usageStudies = references.filter(r => r.reference_type === 'usage' || !r.reference_type);

  if (compSources.length === 0 && usageStudies.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Info size={18} className="text-slate-400" />
        <h3 className="text-lg font-semibold text-slate-200">References</h3>
      </div>
      {compSources.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Composition Sources</p>
          <div className="space-y-2">
            {compSources.map((r, i) => (
              <a key={i}
                href={`https://scholar.google.com/scholar?q=${encodeURIComponent(r.reference_text)}`}
                target="_blank" rel="noopener noreferrer"
                className="block text-sm text-slate-400 hover:text-emerald-400 transition-colors leading-relaxed">
                {r.reference_text}
              </a>
            ))}
          </div>
        </div>
      )}
      {usageStudies.length > 0 && (
        <div>
          <p className="text-[10px] text-slate-500 uppercase font-bold mb-2">Usage Studies</p>
          <div className="space-y-2">
            {usageStudies.map((r, i) => (
              <a key={i}
                href={`https://scholar.google.com/scholar?q=${encodeURIComponent(r.reference_text)}`}
                target="_blank" rel="noopener noreferrer"
                className="block text-sm text-slate-400 hover:text-emerald-400 transition-colors leading-relaxed">
                {r.reference_text}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
