// claude-sonnet-4-6
import { useEffect, useState, useCallback } from 'react';
import { ChevronDown, ChevronUp, BarChart2, TrendingUp, Hash, DollarSign, Percent } from 'lucide-react';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';

interface InsightDef {
  key: string;
  label: string;
  format: 'number' | 'currency' | 'percent';
  icon?: string | null;
  prefix?: string | null;
  suffix?: string | null;
}

interface InsightResult extends InsightDef {
  value: number;
}

interface Props {
  resource: string;
  insights: InsightDef[];
  recordId?: string | number;
}

const STORAGE_KEY = 'aras_insight_strip_open';

function formatValue(value: number, format: InsightResult['format'], prefix?: string | null, suffix?: string | null): string {
  let formatted: string;
  if (format === 'currency') {
    formatted = new Intl.NumberFormat('en-US', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(value);
  } else if (format === 'percent') {
    formatted = value.toFixed(1) + '%';
  } else {
    formatted = value >= 1_000_000
      ? (value / 1_000_000).toFixed(1) + 'M'
      : value >= 1_000
      ? (value / 1_000).toFixed(1) + 'k'
      : String(Math.round(value));
  }
  return (prefix ? prefix + ' ' : '') + formatted + (suffix ? ' ' + suffix : '');
}

const ICON_MAP: Record<string, any> = {
  bar: BarChart2,
  trend: TrendingUp,
  hash: Hash,
  dollar: DollarSign,
  percent: Percent,
};

// claude-sonnet-4-6
export function InsightStrip({ resource, insights, recordId }: Props) {
  const [open, setOpen] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) !== 'false'; } catch { return true; }
  });
  const [data, setData] = useState<InsightResult[]>([]);
  const [loading, setLoading] = useState(false);

  const toggle = useCallback(() => {
    setOpen(v => {
      const next = !v;
      try { localStorage.setItem(STORAGE_KEY, String(next)); } catch {}
      return next;
    });
  }, []);

  useEffect(() => {
    if (!open || !insights.length) return;
    setLoading(true);
    const path = cleanResourcePath(resource);
    // Form mode: fetch insights scoped to this record via query param
    const url = recordId ? `/${path}/insights?record_id=${recordId}` : `/${path}/insights`;
    api.get(url)
      .then(r => setData(r.data?.data ?? r.data ?? []))
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [resource, insights.length, open, recordId]);

  if (!insights.length) return null;

  return (
    <div className="w-full border-b border-[var(--line)] bg-[var(--bg)]">
      {/* Toggle row */}
      <button
        type="button"
        onClick={toggle}
        className="w-full flex items-center gap-2 px-5 sm:px-7 lg:px-8 py-1.5 text-[11px] font-medium text-[var(--text-3)] hover:text-[var(--text-2)] transition-colors select-none"
      >
        <BarChart2 size={11} />
        <span className="flex-1 text-left tracking-[0.06em] uppercase">Insights</span>
        {open ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>

      {open && (
        <div className="px-5 sm:px-7 lg:px-8 pb-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5">
          {(loading ? insights : data).map((ins, i) => {
            const IconComp = ICON_MAP[ins.icon ?? ''] ?? BarChart2;
            const displayVal = loading
              ? '—'
              : formatValue((ins as InsightResult).value ?? 0, ins.format, ins.prefix, ins.suffix);

            return (
              <div
                key={ins.key ?? i}
                className="flex flex-col gap-0.5 rounded-[var(--aras-radius)] border border-[var(--line)] bg-[var(--surface)] px-3 py-2.5 min-w-0"
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <IconComp size={11} className="shrink-0 text-[var(--accent)]" />
                  <span className="text-[10px] font-medium text-[var(--text-3)] truncate uppercase tracking-[0.08em]">
                    {ins.label}
                  </span>
                </div>
                <span
                  className="text-[20px] font-semibold text-[var(--text)] leading-tight tabular-nums"
                  style={{ letterSpacing: '-0.02em' }}
                >
                  {loading ? (
                    <span className="inline-block h-5 w-14 rounded bg-[var(--surface-2)] animate-pulse" />
                  ) : displayVal}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
