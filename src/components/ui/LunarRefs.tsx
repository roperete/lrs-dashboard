import React from 'react';
import { ExternalLink } from 'lucide-react';
import { RefSup } from './RefSup';
import type { LunarCite, LunarCitations } from '../../utils/lunarCitations';
import { lunarDocumentLabel } from '../../utils/lunarCitations';

/** The superscripts of one lunar value, e.g. [1][3]. */
export function LunarRefs({ cites, prefix = '', align = 'center' }: { cites: LunarCite[]; prefix?: string; align?: 'left' | 'center' | 'right' }) {
  return (
    <>
      {cites.map(c => (
        <React.Fragment key={`${c.n}-${c.location}`}>
          <RefSup n={c.n} prefix={prefix} align={align}
            source={lunarDocumentLabel(c.document)} location={c.location} quote={c.quote} />
        </React.Fragment>
      ))}
    </>
  );
}

/** The numbered list of documents a lunar site or sample cites. */
export function LunarSourceList({ citations, prefix = '', title = 'Sources' }: { citations: LunarCitations; prefix?: string; title?: string }) {
  if (citations.documents.length === 0) return null;
  return (
    <div>
      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">{title}</h3>
      <ol className="space-y-1.5 text-xs text-slate-400">
        {citations.documents.map((d, i) => {
          const href = d.url || (d.doi ? `https://doi.org/${d.doi}` : null);
          return (
            <li key={d.document_id} className="flex gap-2">
              <span className="font-semibold text-amber-400/90 shrink-0">[{prefix}{i + 1}]</span>
              <span>
                {d.authors ? `${d.authors}${d.year ? ` (${d.year})` : ''}. ` : d.year ? `(${d.year}) ` : ''}
                <span className="text-slate-300">{d.title}</span>
                {href && (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 ml-1 text-amber-400/80 hover:text-amber-300">
                    <ExternalLink size={10} />link
                  </a>
                )}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
