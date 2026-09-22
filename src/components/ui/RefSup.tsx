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
}

/**
 * Citation superscript such as [2]. The number is the reference's position in the
 * simulant's numbered References section; hovering shows where in that document the
 * value was read. A real <sup> so it sits like a footnote mark next to the value.
 */
export function RefSup({ n, location, quote, fallback, align = 'center' }: RefSupProps) {
  const parts = [location?.trim(), quote?.trim()].filter((p): p is string => !!p);
  const text = parts.length > 0 ? parts.join(' — ') : fallback || `Reference ${n}`;
  return (
    <sup className="ml-0.5 text-[10px] leading-none">
      <Tooltip text={text} align={align}>
        <span className="font-semibold text-amber-400/90 hover:text-amber-300" aria-label={`Reference ${n}`}>
          [{n}]
        </span>
      </Tooltip>
    </sup>
  );
}
