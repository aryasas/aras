import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { TextStyle, ViewStyle } from 'react-native';
import api from './api';

type OverrideRow = {
  selector: string;
  css_json?: Record<string, any>;
  hidden?: boolean;
  text_override?: string | null;
};

type NativeOverride = {
  style?: ViewStyle & TextStyle;
  hidden: boolean;
  textOverride?: string | null;
};

type DesignOverrideContextValue = {
  rows: OverrideRow[];
  refresh: () => Promise<void>;
};

const DesignOverrideContext = createContext<DesignOverrideContextValue>({
  rows: [],
  refresh: async () => undefined,
});

function numeric(value: unknown): number | undefined {
  if (typeof value === 'number') return value;
  if (typeof value !== 'string') return undefined;
  const parsed = Number(value.replace('px', '').trim());
  return Number.isFinite(parsed) ? parsed : undefined;
}

function cssToNative(css?: Record<string, any>): ViewStyle & TextStyle {
  const out: ViewStyle & TextStyle = {};
  if (!css) return out;
  for (const [key, value] of Object.entries(css)) {
    if (value == null || value === '' || key.startsWith('@media')) continue;
    const n = numeric(value);
    switch (key) {
      case 'background-color':
        out.backgroundColor = String(value);
        break;
      case 'color':
        out.color = String(value);
        break;
      case 'border-color':
        out.borderColor = String(value);
        break;
      case 'border-radius':
        if (n !== undefined) out.borderRadius = n;
        break;
      case 'border-width':
        if (n !== undefined) out.borderWidth = n;
        break;
      case 'font-size':
        if (n !== undefined) out.fontSize = n;
        break;
      case 'font-weight':
        out.fontWeight = String(value) as TextStyle['fontWeight'];
        break;
      case 'line-height':
        if (n !== undefined) out.lineHeight = n;
        break;
      case 'padding':
        if (n !== undefined) out.padding = n;
        break;
      case 'padding-horizontal':
        if (n !== undefined) out.paddingHorizontal = n;
        break;
      case 'padding-vertical':
        if (n !== undefined) out.paddingVertical = n;
        break;
      case 'margin':
        if (n !== undefined) out.margin = n;
        break;
      case 'gap':
        if (n !== undefined) out.gap = n;
        break;
      case 'width':
        if (n !== undefined) out.width = n;
        break;
      case 'height':
        if (n !== undefined) out.height = n;
        break;
      case 'opacity':
        if (n !== undefined) out.opacity = n;
        break;
      case 'text-align':
        out.textAlign = String(value) as TextStyle['textAlign'];
        break;
      default:
        break;
    }
  }
  return out;
}

export function DesignOverrideProvider({ children, path = 'mobile' }: { children: React.ReactNode; path?: string }) {
  const [rows, setRows] = useState<OverrideRow[]>([]);

  const refresh = useCallback(async () => {
    try {
      const res = await api.get(`/dev/dev/style-overrides?path=${encodeURIComponent(path)}`);
      setRows(Array.isArray(res.data) ? res.data : []);
    } catch {
      setRows([]);
    }
  }, [path]);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo(() => ({ rows, refresh }), [refresh, rows]);
  return <DesignOverrideContext.Provider value={value}>{children}</DesignOverrideContext.Provider>;
}

export function useDesignOverride(...selectors: string[]): NativeOverride {
  const { rows } = useContext(DesignOverrideContext);
  return useMemo(() => {
    const matches = rows.filter((row) => selectors.includes(row.selector));
    return matches.reduce<NativeOverride>((acc, row) => ({
      style: { ...(acc.style || {}), ...cssToNative(row.css_json) },
      hidden: acc.hidden || Boolean(row.hidden),
      textOverride: row.text_override ?? acc.textOverride,
    }), { hidden: false });
  }, [rows, selectors]);
}
