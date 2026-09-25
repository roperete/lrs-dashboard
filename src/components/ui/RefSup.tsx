import React from 'react';
import { Tooltip } from './Tooltip';

interface RefSupProps {
  /** The reference's number within its simulant's list, matching the References section. */
  n: number;
  /** Page, table or figure where the reader found the value. */
  location?: string | null;
  /** The line in the document that states the value. */
  quote?: string | null;
  /** Hover text when there is no location or quote, e.g. a composition row that cites a
   *  document as a whole; falls back to "Reference n". */
  fallback?: string;
  align?: 'left' | 'center' | 'right';
  /** The document the mark points to, shown first: otherwise nothing on the hover says which
   *  reference [n] is, short of scrolling to the References section. */
  source?: string | null;
  /** Marks a separate numbering, e.g. "L" for the lunar sources listed under the lunar comparison. */
  prefix?: string;
  /** Instead of jumping to the reference in the pane (e.g. the table opens the pane). */
  onActivate?: () => void;
}

/** Scroll the pane to reference n and flash it; the References list expands if it was shortened. */
export function goToReference(n: number, prefix = ''): boolean {
  window.dispatchEvent(new CustomEvent('lrs:show-reference', { detail: { n, prefix } }));
  const find = () => document.getElementById(`pane-ref-${prefix}${n}`);
  const el = find();
  if (!el && prefix) return false;
  setTimeout(() => {
    const target = find();
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    target.classList.add('ring-2', 'ring-amber-400');
    setTimeout(() => target.classList.remove('ring-2', 'ring-amber-400'), 1600);
  }, el ? 0 : 60);
  return true;
}

/**
 * Citation mark such as [2]. Hover, focus or tap shows which document states the value, where,
 * and the quoted line; clicking jumps to that reference in the pane (review #10), or runs
 * onActivate where there is no list to jump to (the table opens the pane at its References).
 */
export function RefSup({ n, location, quote, fallback, align = 'center', source, prefix = '', onActivate }: RefSupProps) {
  const parts = [location?.trim(), quote?.trim()].filter((p): p is string => !!p);
  const detail = parts.length > 0 ? parts.join(' — ') : fallback;
  const text = [source?.trim() ? `[${prefix}${n}] ${source.trim()}` : undefined, detail].filter(Boolean).join('\n') || `Reference ${prefix}${n}`;
  return (
    <sup className="ml-0.5 text-[10px] leading-none">
      <Tooltip text={text} align={align} focusable={false}>
        <button type="button" aria-label={`Reference ${prefix}${n}${source ? `: ${source}` : ''}`}
          onClick={(e) => { e.stopPropagation(); if (onActivate) onActivate(); else goToReference(n, prefix); }}
          className="font-semibold text-amber-400/90 hover:text-amber-300 focus:outline-none focus-visible:ring-1 focus-visible:ring-amber-400 rounded-sm">
          [{prefix}{n}]
        </button>
      </Tooltip>
    </sup>
  );
}
