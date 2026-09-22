import React from 'react';
import { BookOpen, ExternalLink, Search, Quote, Sparkles, CircleCheck, TriangleAlert } from 'lucide-react';
import { Tooltip } from '../ui/Tooltip';
import { orderReferences } from '../../utils/references';
import type { Reference } from '../../types';

interface ReferencesSectionProps {
  references: Reference[];
  simulantName?: string;
}

/** Extract the first URL from text, if any */
function extractUrl(text: string): { url: string | null; cleanText: string } {
  const urlMatch = text.match(/https?:\/\/[^\s)]+/);
  if (!urlMatch) return { url: null, cleanText: text };
  const url = urlMatch[0];
  const cleanText = text.replace(url, '').replace(/\s{2,}/g, ' ').trim().replace(/\.$/, '');
  return { url, cleanText };
}

/** Detect DOI and return link */
function extractDoi(text: string): string | null {
  const doiMatch = text.match(/10\.\d{4,}\/[^\s)]+/);
  return doiMatch ? `https://doi.org/${doiMatch[0]}` : null;
}

/** Extract likely article title: text before the year or first ~100 chars */
function extractTitle(text: string): string {
  // Try to grab text before a (YYYY) or , YYYY pattern
  const beforeYear = text.match(/^(.+?)(?:\(?\d{4}\)?)/);
  if (beforeYear && beforeYear[1].length > 10) {
    return beforeYear[1].replace(/[,.\s]+$/, '').trim();
  }
  return text.slice(0, 100).replace(/[,.\s]+$/, '').trim();
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
    .filter(Boolean);
  return types.length > 0 ? types : ['general'];
}

function badgeFor(type: string): { label: string; className: string } {
  return TYPE_BADGES[type] ?? { label: type, className: TYPE_BADGES.general.className };
}

/** Whether a reader confirmed the document names this exact simulant. An unchecked
 *  reference (names_simulant null) shows no mark either way. */
function NamesMark({ reference }: { reference: Reference }) {
  if (reference.names_simulant === 1) {
    return (
      <Tooltip
        text={reference.mention_quote ? `"${reference.mention_quote}"` : 'A reader confirmed this document names the simulant'}
        align="left"
      >
        <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400">
          <CircleCheck size={11} aria-hidden />
          names this simulant
        </span>
      </Tooltip>
    );
  }
  if (reference.names_simulant === 0) {
    return (
      <Tooltip
        text="A reader checked this document and did not find this simulant named in it. It stays listed for the owner's decision."
        align="left"
      >
        <span className="inline-flex items-center gap-1 text-[10px] text-amber-400">
          <TriangleAlert size={11} aria-hidden />
          does not name this simulant
        </span>
      </Tooltip>
    );
  }
  return null;
}

function ReferenceCard({ reference, n }: { reference: Reference; n: number }) {
  // Normalize: new-schema refs have title/authors/year instead of reference_text
  const refText = reference.reference_text
    || [reference.authors, `(${reference.year})`, `"${reference.title}"`, reference.doi ? `https://doi.org/${reference.doi}` : ''].filter(Boolean).join(', ');
  const { url, cleanText } = extractUrl(refText);
  const doi = extractDoi(refText);
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
          {linkUrl && (
            <a href={linkUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              <ExternalLink size={11} />
              {doi && !url ? 'DOI' : 'Source'}
            </a>
          )}
          <a href={`https://scholar.google.com/scholar?q=${encodeURIComponent(refText.slice(0, 120))}`}
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-400 transition-colors">
            <BookOpen size={11} />
            Scholar
          </a>
          <a href={`https://scholar.google.com/scholar?q=${encodeURIComponent('"' + extractTitle(refText) + '"')}`}
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-400 transition-colors">
            <Quote size={11} />
            Cited by
          </a>
          {typesOf(reference).map(type => {
            const badge = badgeFor(type);
            return (
              <span key={type} className={`text-[10px] px-1.5 py-0.5 rounded border uppercase tracking-wide ${badge.className}`}>
                {badge.label}
              </span>
            );
          })}
          <NamesMark reference={reference} />
          {reference.checked_on && (
            <span className="text-[10px] text-slate-600">checked {reference.checked_on}</span>
          )}
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
  const named = references.filter(r => r.names_simulant === 1).length;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen size={18} className="text-amber-400" />
        <h3 className="text-lg font-semibold text-slate-200">References & Credits</h3>
        <span className="text-xs text-slate-500 ml-auto">{references.length} source{references.length !== 1 ? 's' : ''}</span>
      </div>

      {ordered.length > 0 && (
        <div>
          <p className="text-[10px] text-slate-500 mb-2">
            Numbers match the superscripts on values above. {named} of {ordered.length} confirmed to name {simulantName || 'this simulant'}.
          </p>
          <ol className="space-y-2 list-none p-0 m-0">
            {ordered.map((r, i) => (
              <li key={r.reference_id}>
                <ReferenceCard reference={r} n={i + 1} />
              </li>
            ))}
          </ol>
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
              <p className="text-[10px] text-slate-500">Search Google Scholar for papers citing {simulantName}</p>
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
              <p className="text-[10px] text-slate-500">AI-powered search for published studies using {simulantName}</p>
            </div>
          </a>
        </div>
      )}
    </div>
  );
}
