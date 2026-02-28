import React from 'react';
import { BookOpen, ExternalLink, Search, Quote, Sparkles } from 'lucide-react';
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

/** Extract likely article title — text before the year or first ~100 chars */
function extractTitle(text: string): string {
  // Try to grab text before a (YYYY) or , YYYY pattern
  const beforeYear = text.match(/^(.+?)(?:\(?\d{4}\)?)/);
  if (beforeYear && beforeYear[1].length > 10) {
    return beforeYear[1].replace(/[,.\s]+$/, '').trim();
  }
  return text.slice(0, 100).replace(/[,.\s]+$/, '').trim();
}

function ReferenceCard({ reference, index }: { reference: Reference; index: number }) {
  const { url, cleanText } = extractUrl(reference.reference_text);
  const doi = extractDoi(reference.reference_text);
  const linkUrl = url || doi;

  return (
    <div className="group flex gap-3 p-3 bg-slate-800/20 hover:bg-slate-800/40 rounded-lg border border-slate-700/20 hover:border-slate-700/40 transition-all">
      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700/50 flex items-center justify-center text-[10px] font-bold text-slate-500 mt-0.5">
        {index + 1}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 leading-relaxed">{cleanText}</p>
        <div className="flex items-center gap-3 mt-2">
          {linkUrl && (
            <a href={linkUrl} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
              <ExternalLink size={11} />
              {doi && !url ? 'DOI' : 'Source'}
            </a>
          )}
          <a href={`https://scholar.google.com/scholar?q=${encodeURIComponent(reference.reference_text.slice(0, 120))}`}
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-400 transition-colors">
            <BookOpen size={11} />
            Scholar
          </a>
          <a href={`https://scholar.google.com/scholar?q=${encodeURIComponent('"' + extractTitle(reference.reference_text) + '"')}`}
            target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-400 transition-colors">
            <Quote size={11} />
            Cited by
          </a>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500 uppercase">
            {reference.reference_type || 'general'}
          </span>
        </div>
      </div>
    </div>
  );
}

export function ReferencesSection({ references, simulantName }: ReferencesSectionProps) {
  if (references.length === 0 && !simulantName) return null;

  const compSources = references.filter(r => r.reference_type === 'composition');
  const usageStudies = references.filter(r => r.reference_type === 'usage' || (!r.reference_type && r.reference_type !== 'composition'));

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen size={18} className="text-amber-400" />
        <h3 className="text-lg font-semibold text-slate-200">References & Credits</h3>
        <span className="text-xs text-slate-500 ml-auto">{references.length} source{references.length !== 1 ? 's' : ''}</span>
      </div>

      {compSources.length > 0 && (
        <div className="mb-4">
          <p className="text-[10px] text-amber-400/60 uppercase font-bold tracking-wider mb-2">Composition Sources</p>
          <div className="space-y-2">
            {compSources.map((r, i) => <ReferenceCard key={r.reference_id} reference={r} index={i} />)}
          </div>
        </div>
      )}

      {usageStudies.length > 0 && (
        <div>
          <p className="text-[10px] text-blue-400/60 uppercase font-bold tracking-wider mb-2">Usage Studies</p>
          <div className="space-y-2">
            {usageStudies.map((r, i) => <ReferenceCard key={r.reference_id} reference={r} index={i} />)}
          </div>
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
            href={`https://www.google.com/search?q=${encodeURIComponent('What is ' + simulantName + ' lunar regolith simulant used for in research')}&udm=50`}
            target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-3 p-3 bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/20 rounded-xl transition-all group"
          >
            <div className="p-2 bg-purple-500/10 rounded-lg group-hover:bg-purple-500/20 transition-colors">
              <Sparkles size={16} className="text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-purple-400">Ask AI about this simulant</p>
              <p className="text-[10px] text-slate-500">Google AI overview for {simulantName} research applications</p>
            </div>
          </a>
        </div>
      )}
    </div>
  );
}
