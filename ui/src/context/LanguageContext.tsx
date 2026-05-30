// claude-haiku-4-5
import React, { createContext, useContext, useState, useCallback } from 'react';
import en from '../locales/en.json';
import id from '../locales/id.json';
import api from '../lib/api';

type Lang = 'en' | 'id';
type Locales = typeof en;

interface LanguageContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, fallback?: string) => string;
}

const locales: Record<Lang, Locales> = { en, id };
const STORAGE_KEY = 'aras_lang';

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    return (saved === 'en' || saved === 'id') ? saved : 'en';
  });
  const [remoteLocales, setRemoteLocales] = useState<Partial<Record<Lang, Record<string, any>>>>({});

  const setLang = useCallback((newLang: Lang) => {
    setLangState(newLang);
    localStorage.setItem(STORAGE_KEY, newLang);
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    api.get(`/i18n/${lang}.json`)
      .then((res) => {
        if (!cancelled) setRemoteLocales((current) => ({ ...current, [lang]: res.data || {} }));
      })
      .catch(() => {
        if (!cancelled) setRemoteLocales((current) => ({ ...current, [lang]: current[lang] || {} }));
      });
    return () => {
      cancelled = true;
    };
  }, [lang]);

  const t = useCallback((key: string, fallback?: string): string => {
    const activeLocale = { ...(locales[lang] as Record<string, any>), ...(remoteLocales[lang] || {}) };
    const direct = activeLocale[key];
    if (typeof direct === 'string') return direct;

    const keys = key.split('.');
    let value: any = activeLocale;
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return fallback || key;
      }
    }
    
    return typeof value === 'string' ? value : (fallback || key);
  }, [lang, remoteLocales]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
