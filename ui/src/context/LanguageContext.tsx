// claude-haiku-4-5
import React, { createContext, useContext, useState, useCallback } from 'react';
import en from '../locales/en.json';
import id from '../locales/id.json';

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

  const setLang = useCallback((newLang: Lang) => {
    setLangState(newLang);
    localStorage.setItem(STORAGE_KEY, newLang);
  }, []);

  const t = useCallback((key: string, fallback?: string): string => {
    const direct = (locales[lang] as Record<string, any>)[key];
    if (typeof direct === 'string') return direct;

    const keys = key.split('.');
    let value: any = locales[lang];
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return fallback || key;
      }
    }
    
    return typeof value === 'string' ? value : (fallback || key);
  }, [lang]);

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
