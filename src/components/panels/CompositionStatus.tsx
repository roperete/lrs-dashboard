import { ShieldCheck, ShieldAlert, FileX2, HelpCircle, ExternalLink } from 'lucide-react';
import type { Simulant } from '../../types';

export type CompositionStatus =
  | 'verified'
  | 'withheld_unverified'
  | 'not_published'
  | 'not_extracted';

const NOTICES: Record<CompositionStatus, { title: string; body: string; tone: string; Icon: typeof ShieldCheck }> = {
  verified: {
    title: 'Verified against source',
    body: 'These values were read from the source cited below and independently re-checked against it.',
    tone: 'text-emerald-400',
    Icon: ShieldCheck,
  },
  withheld_unverified: {
    title: 'Composition withheld',
    body:
      'Values were previously listed here, but they could not be confirmed against a manufacturer data sheet or ' +
      'the publication that characterised this simulant. They have been removed rather than shown unconfirmed.',
    tone: 'text-amber-400',
    Icon: ShieldAlert,
  },
  not_published: {
    title: 'Composition not published',
    body:
      'The producer and the publication that defines this simulant do not disclose a composition for it. ' +
      'Nothing is being withheld here; the data does not exist in the public record.',
    tone: 'text-slate-400',
    Icon: FileX2,
  },
  not_extracted: {
    title: 'Composition not yet verified',
    body:
      'This simulant has not yet been through the source audit. A composition may well be published for it; ' +
      'we have not confirmed one, so we do not show numbers.',
    tone: 'text-slate-400',
    Icon: HelpCircle,
  },
};

export function statusOf(simulant: Pick<Simulant, 'composition_status'>): CompositionStatus {
  const s = simulant.composition_status;
  if (s === 'verified' || s === 'withheld_unverified' || s === 'not_published') return s;
  return 'not_extracted';
}

/** Empty-state notice shown in place of a composition chart. */
export function CompositionStatusNotice({
  status,
  kind,
}: {
  status: CompositionStatus;
  kind: 'mineral' | 'chemical';
}) {
  const n = NOTICES[status];
  const what = kind === 'mineral' ? 'Mineral composition' : 'Chemical composition';
  return (
    <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700/30">
      <div className="flex items-start gap-3">
        <n.Icon size={18} className={`${n.tone} mt-0.5 shrink-0`} aria-hidden />
        <div>
          <p className={`text-sm font-semibold ${n.tone}`}>
            {what}: {n.title.toLowerCase()}
          </p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">{n.body}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * The one line that says where a simulant's published numbers came from.
 * Deliberately separate from the reference list, which holds usage studies.
 */
export function DataSourceLine({ simulant }: { simulant: Simulant }) {
  const status = statusOf(simulant);
  if (status !== 'verified') return null;

  const title = simulant.composition_source_title || 'Source on file';
  // Only a web address may become a link. The audit's working copies live on local
  // disk; a local path rendered as an href resolves against this site and 404s.
  const candidate = simulant.composition_source_url || simulant.datasheet_url || '';
  const url = /^https?:\/\//i.test(candidate) ? candidate : '';
  const kindLabel =
    simulant.composition_source_kind === 'manufacturer_datasheet'
      ? 'Manufacturer data sheet'
      : simulant.composition_source_kind === 'primary_paper'
        ? 'Primary characterisation paper'
        : simulant.composition_source_kind === 'agency_report'
          ? 'Agency report'
          : simulant.composition_source_kind === 'secondary_reproduction'
            ? 'Reproduced in a later publication; the original paper could not be opened'
            : 'Source';

  return (
    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-4 py-3">
      <div className="flex items-start gap-3">
        <ShieldCheck size={16} className="text-emerald-400 mt-0.5 shrink-0" aria-hidden />
        <div className="min-w-0">
          <p className="text-[10px] uppercase font-bold tracking-wider text-emerald-400/70">
            Composition data source
          </p>
          <p className="text-sm text-slate-200 mt-0.5 break-words">
            {url ? (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-emerald-300 underline decoration-emerald-500/40 underline-offset-2"
              >
                {title}
                <ExternalLink size={12} className="inline ml-1 mb-0.5" aria-hidden />
              </a>
            ) : (
              title
            )}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {kindLabel}
            {simulant.datasheet_document_id ? ` · ${simulant.datasheet_document_id}` : ''}
            {simulant.datasheet_date ? ` · ${simulant.datasheet_date}` : ''}
            {simulant.composition_needs_review ? ' · flagged for a second human check' : ''}
          </p>
          {simulant.datasheet_notes && (
            <details className="mt-1">
              <summary className="text-[11px] text-slate-400 cursor-pointer hover:text-slate-300">
                Methods and caveats stated on the sheet
              </summary>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{simulant.datasheet_notes}</p>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
