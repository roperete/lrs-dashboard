import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { APP_VERSION } from '../../version';

/** Quick guide and About, opened from the top bar. */
export function HelpModal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const section = (title: string, body: React.ReactNode) => (
    <div>
      <h4 className="text-emerald-400 font-semibold mb-1">{title}</h4>
      <p>{body}</p>
    </div>
  );

  return (
    <div className="fixed inset-0 z-[1300] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-label="Quick guide"
        className="bg-slate-900 border border-slate-700 rounded-2xl max-h-[80vh] max-w-lg overflow-y-auto w-full shadow-2xl"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-slate-800 sticky top-0 bg-slate-900 rounded-t-2xl">
          <h3 className="text-sm font-semibold text-white">Quick guide</h3>
          <button onClick={onClose} aria-label="Close the guide" className="p-1 hover:bg-slate-800 rounded-lg text-slate-400">
            <X size={16} />
          </button>
        </div>
        <div className="p-4 space-y-4 text-sm text-slate-300 leading-relaxed">
          {section('Views', <>Switch between <b>Globe</b>, <b>Map</b> and <b>Table</b> in the top bar, and between <b>Earth</b> (simulants and where they are made) and the <b>Moon</b> (landing sites).</>)}
          {section('Find', <>The <b>Find</b> pane on the left searches by name, producer or country, and filters by type, availability, the data a simulant has, and ranges of density, particle size, friction angle and cohesion. More filters (country, mineral, oxide, lunar sample, reference) are under <b>More filters</b>.</>)}
          {section('A simulant', <>Click a marker, a list row or a table row to open its pane: properties, composition, Figures of Merit, where to buy it, and its references. Every value carries a mark such as <b>[3]</b>: hover or tap it to see which document states the value, where, and the quoted sentence.</>)}
          {section('Compare', <>Tick simulants in the table or the list, or use <b>Add to compare</b> in a pane. They collect in the tray at the bottom; compare two to four at once. <b>Compare with a lunar sample</b> in the pane sets a simulant against an Apollo or Chang'e sample.</>)}
          {section('Export', <>The <b>Export</b> button in the top bar downloads the current simulant, the filtered set or the whole database as CSV.</>)}
          {section('Map controls', <>The toolbar on the right: full screen, day or night (globe), reset the view, auto-rotate (globe), zoom, and <b>Go to</b> a place on the map.</>)}
          <div className="pt-3 border-t border-slate-800 space-y-3">
            <p className="text-slate-400">An initiative of <b className="text-slate-300">The Spring Institute for Forests on the Moon</b>, sponsored by <b className="text-slate-300">CNES</b>. {APP_VERSION}.</p>
            <div className="flex items-center gap-6">
              <a href="https://cnes.fr" target="_blank" rel="noopener noreferrer" aria-label="CNES">
                <img src={import.meta.env.BASE_URL + 'assets/cnes-logo.png'} alt="CNES" className="h-10 w-auto object-contain" />
              </a>
              <a href="https://thespringinstitute.com" target="_blank" rel="noopener noreferrer" aria-label="The Spring Institute">
                <img src={import.meta.env.BASE_URL + 'assets/spring-logo.png'} alt="The Spring Institute" className="h-10 w-auto object-contain" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
