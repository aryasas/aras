// claude-haiku-4-5
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import en from '../locales/en.json';
import id from '../locales/id.json';

type Lang = 'en' | 'id';
type Locales = typeof en;

interface LanguageContextType {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, fallback?: string) => string;
  isReady: boolean;
}

const locales: Record<Lang, Locales> = { en, id };
const STORAGE_KEY = 'aras_lang';

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Lang>('en');
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const loadLang = async () => {
      try {
        const saved = await AsyncStorage.getItem(STORAGE_KEY);
        if (saved === 'en' || saved === 'id') {
          setLangState(saved);
        }
      } catch (e) {
        console.error('Failed to load language', e);
      } finally {
        setIsReady(true);
      }
    };
    loadLang();
  }, []);

  const setLang = useCallback(async (newLang: Lang) => {
    setLangState(newLang);
    try {
      await AsyncStorage.setItem(STORAGE_KEY, newLang);
    } catch (e) {
      console.error('Failed to save language', e);
    }
  }, []);

  const t = useCallback((key: string, fallback?: string): string => {
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
    <LanguageContext.Provider value={{ lang, setLang, t, isReady }}>
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
