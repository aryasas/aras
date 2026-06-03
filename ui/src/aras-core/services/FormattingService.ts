import api from '../../lib/api';

export interface RegionalConfig {
  dateFormat: string;
  numberFormat: string;
  decimalPrecision: number;
  currencySymbol: string;
  language: string;
}

let config: RegionalConfig = {
  dateFormat: 'YYYY-MM-DD',
  numberFormat: '#,###.##',
  decimalPrecision: 2,
  currencySymbol: '',
  language: 'en-US'
};

function resolveLocale(locale?: string) {
  if (locale) return locale
  if (config.language.includes('-')) return config.language
  if (config.language === 'id') return 'id-ID'
  return 'en-US'
}

export const FormattingService = {
  async init() {
    try {
      const response = await api.get('/settings/core');
      // Backend returns { section_key: { field_key: value, ... }, ... }
      const sections = (response.data || {}) as Record<string, Record<string, any>>;
      const flat: Record<string, string> = {};
      Object.values(sections).forEach(section => {
        Object.entries(section || {}).forEach(([k, v]) => { flat[k] = String(v ?? ''); });
      });

      config = {
        dateFormat: flat['date_format'] || 'YYYY-MM-DD',
        numberFormat: flat['number_format'] || '#,###.##',
        decimalPrecision: parseInt(flat['decimal_precision'] || '2'),
        currencySymbol: flat['currency_symbol'] || '',
        language: flat['language_default'] || 'en-US'
      };
    } catch (err) {
      console.error('[FormattingService] Failed to load config:', err);
    }
  },

  getConfig() {
    return config;
  },

  formatCurrency(value: number, currency?: string) {
    if (typeof Intl !== 'undefined' && typeof Intl.NumberFormat === 'function' && currency && currency.length === 3) {
      return new Intl.NumberFormat(resolveLocale(), {
        style: 'currency',
        currency,
      }).format(value)
    }

    const locale = config.numberFormat === '#.###,##' ? 'de-DE' : resolveLocale()
    const formatted = new Intl.NumberFormat(locale, {
      minimumFractionDigits: config.decimalPrecision,
      maximumFractionDigits: config.decimalPrecision,
    }).format(value)
    return config.currencySymbol ? `${formatted} ${config.currencySymbol}` : formatted
  },

  formatDate(value: string | Date, locale?: string, options?: Intl.DateTimeFormatOptions) {
    if (!value) return '';
    const date = new Date(value);

    if (typeof Intl !== 'undefined' && typeof Intl.DateTimeFormat === 'function') {
      return new Intl.DateTimeFormat(resolveLocale(locale), options ?? { dateStyle: 'medium' }).format(date)
    }

    // Fallback for environments without Intl.DateTimeFormat.
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    switch (config.dateFormat) {
      case 'DD/MM/YYYY': return `${day}/${month}/${year}`;
      case 'MM/DD/YYYY': return `${month}/${day}/${year}`;
      case 'YYYY-MM-DD': return `${year}-${month}-${day}`;
      default: return date.toLocaleDateString();
    }
  },

  formatDateTime(value: string | Date, locale?: string, options?: Intl.DateTimeFormatOptions) {
    if (!value) return '';
    const date = new Date(value);

    if (typeof Intl !== 'undefined' && typeof Intl.DateTimeFormat === 'function') {
      return new Intl.DateTimeFormat(resolveLocale(locale), options ?? { dateStyle: 'medium', timeStyle: 'short' }).format(date)
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    switch (config.dateFormat) {
      case 'DD/MM/YYYY': return `${day}/${month}/${year} ${hours}:${minutes}`;
      case 'MM/DD/YYYY': return `${month}/${day}/${year} ${hours}:${minutes}`;
      case 'YYYY-MM-DD': return `${year}-${month}-${day} ${hours}:${minutes}`;
      default: return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
    }
  },

  formatNumber(value: number) {
    const locale = config.numberFormat === '#.###,##' ? 'de-DE' : 'en-US';
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: config.decimalPrecision,
      maximumFractionDigits: config.decimalPrecision,
    }).format(value);
  }
};
