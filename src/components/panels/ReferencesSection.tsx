import React, { useEffect, useState } from 'react';
import { BookOpen, ExternalLink, Search, Sparkles } from 'lucide-react';
import { orderReferences } from '../../utils/references';
import type { Reference } from '../../types';

interface ReferencesSectionProps {
  references: Reference[];
  simulantName?: string;
}

/** Trailing punctuation that ends a sentence, not a link; a closing bracket only when it has no
 *  opening partner (DOIs such as 10.1061/(ASCE)0893-1321(2009)22:1(53) contain brackets). */
export function trimLinkEnd(link: string): string {
  let out = link.replace(/[.,;:]+$/, '');
  while (out.endsWith(')') && (out.match(/\(/g) || []).length < (out.match(/\)/g) || []).length) {
    out = out.slice(0, -1).replace(/[.,;:]+$/, '');
  }
  return out;
}

/** Extract the first URL from text, if any */
function extractUrl(text: string): { url: string | null; cleanText: string } {
  const urlMatch = text.match(/https?:\/\/\S+/);
  if (!urlMatch) return { url: null, cleanText: text };
  const url = trimLinkEnd(urlMatch[0]);
  const cleanText = text.replace(url, '').replace(/\s{2,}/g, ' ').trim().replace(/\.$/, '');
  return { url, cleanText };
}

/** Detect DOI and return link */
function extractDoi(text: string): string | null {
  const doiMatch = text.match(/10\.\d{4,}\/\S+/);
  return doiMatch ? `https://doi.org/${trimLinkEnd(doiMatch[0])}` : null;
}


/** One badge per reference type (schema.sql lists the known ones). A reference may
 *  carry several, comma-separated, such as "composition,geotechnical". */
const TYPE_BADGES: Record<string, { label: string; className: string }> = {
  datasheet: { label: 'data sheet', className: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  composition: { label: 'composition source', className: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
  geotechnical: { label: 'geotechnical', className: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30' },
  usage: { label: 'usage study', className: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  review: { label: 'review', className: 'bg-purple-500/15 text-purple-300 border-purple-500/30' },
  report: { label: 'report', className: 'bg-slate-500/20 text-slate-300 border-slate-500/30' },
  general: { label: 'general', className: 'bg-slate-700/50 text-slate-400 border-slate-600/40' },
};

function typesOf(reference: Reference): string[] {
  const types = (reference.reference_type || 'general')
    .split(',')
    .map(t => t.trim().toLowerCase())
    .filter(Boolean)
    .filter(t => t !== 'general');   // "general" tells a reader nothing
  return types;
}

function badgeFor(type: string): { label: string; className: string } {
  return TYPE_BADGES[type] ?? { label: type, className: TYPE_BADGES.general.className };
}

function ReferenceCard({ reference, n }: { reference: Reference; n: number }) {
  // Normalize: new-schema refs have title/authors/year instead of reference_text
  // The stored citation is often the title alone; then authors and year come first, as a
  // reader expects a reference to read.
  const titleOnly = !!reference.title && (!reference.reference_text || reference.reference_text.trim() === reference.title.trim());
  const composed = reference.authors
    ? [reference.authors, reference.year ? `(${reference.year}).` : '', reference.title].filter(Boolean).join(' ')
    : [reference.title, reference.year ? `(${reference.year})` : ''].filter(Boolean).join(' ');
  const refText = titleOnly ? composed : reference.reference_text || composed;
  const { url, cleanText } = extractUrl(refText);
  // the stored DOI field first; the citation text only when there is none
  const doi = reference.doi ? `https://doi.org/${reference.doi.trim()}` : extractDoi(refText);
  const linkUrl = url || doi;

  return (
    <div className="group flex gap-3 p-3 bg-slate-800/20 hover:bg-slate-800/40 rounded-lg border border-slate-700/20 hover:border-slate-700/40 transition-all">
      <span
        className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700/50 flex items-center justify-center text-[10px] font-bold text-amber-400/90 mt-0.5"
        title={`Reference ${n}: cited as [${n}] on values above`}
      >
        {n}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 leading-relaxed">{cleanText}</p>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
          {linkUrl ? (
            <a href={linkUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              <ExternalLink size={11} />
              {doi && !url ? 'View (DOI)' : 'View'}
            </a>
          ) : (reference.title || cleanText) && (
            <a href={`https://scholar.google.com/scholar?q=${encodeURIComponent('"' + (reference.title || cleanText).slice(0, 200) + '"')}`}
              target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              <Search size={11} />
              Find it
            </a>
          )}
          {typesOf(reference).map(type => {
            const badge = badgeFor(type);
            return (
              <span key={type} className={`text-[10px] px-1.5 py-0.5 rounded border uppercase tracking-wide ${badge.className}`}>
                {badge.label}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function ReferencesSection({ references, simulantName }: ReferencesSectionProps) {
  if (references.length === 0 && !simulantName) return null;

  // Every reference is listed, whatever its type, numbered in reference_id order: the
  // same order utils/references.ts uses for the superscripts on values above.
  const ordered = orderReferences(references);
  // The first five, then "Show all"; a citation mark pointing further down expands the list.
  const [showAll, setShowAll] = useState(false);
  useEffect(() => {
    const onShow = (e: Event) => {
      const { n, prefix } = (e as CustomEvent).detail || {};
      if (!prefix && n > 5) setShowAll(true);
    };
    window.addEventListener('lrs:show-reference', onShow);
    return () => window.removeEventListener('lrs:show-reference', onShow);
  }, []);
  const shown = showAll ? ordered : ordered.slice(0, 5);

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen size={18} className="text-amber-400" />
        <h3 className="text-lg font-semibold text-slate-200">References & Credits</h3>
        <span className="text-xs text-slate-400 ml-auto">{references.length} source{references.length !== 1 ? 's' : ''}</span>
      </div>

      {ordered.length > 0 && (
        <div>
          <p className="text-[10px] text-slate-400 mb-2">
            The numbers match the [n] marks on the values above.
          </p>
          <ol className="space-y-2 list-none p-0 m-0">
            {shown.map((r, i) => (
              <li key={r.reference_id} id={`pane-ref-${i + 1}`} className="scroll-mt-16 rounded-lg transition-shadow">
                <ReferenceCard reference={r} n={i + 1} />
              </li>
            ))}
          </ol>
          {ordered.length > 5 && (
            <button onClick={() => setShowAll(v => !v)} className="mt-2 text-xs text-emerald-400 hover:text-emerald-300">
              {showAll ? 'Show the first 5' : `Show all ${ordered.length}`}
            </button>
          )}
        </div>
      )}

      {simulantName && (
        <div className="space-y-2 mt-4">
          <a
            href={`https://scholar.google.com/scholar?q=${encodeURIComponent(simulantName + ' lunar regolith simulant')}`}
            target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 bg-emerald-500/5 hover:bg-emerald-500/10 border border-emerald-500/20 rounded-xl transition-all group"
          >
            <div className="p-2 bg-emerald-500/10 rounded-lg group-hover:bg-emerald-500/20 transition-colors">
              <Search size={16} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-emerald-400">Find Citing Sources</p>
              <p className="text-[10px] text-slate-400">Search Google Scholar for papers citing {simulantName}</p>
            </div>
          </a>
          <a
            href={`https://www.google.com/search?q=${encodeURIComponent(simulantName + ' lunar regolith simulant published studies experiments applications site:scholar.google.com OR site:researchgate.net OR site:sciencedirect.com')}&udm=50`}
            target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/20 rounded-xl transition-all group"
          >
            <div className="p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
              <Sparkles size={16} className="text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-purple-400">Ask AI about this simulant</p>
              <p className="text-[10px] text-slate-400">AI search for published studies using {simulantName}. Its answers are not checked by this database.</p>
            </div>
          </a>
        </div>
      )}
    </div>
  );
}
