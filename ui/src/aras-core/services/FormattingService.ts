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
  currencySymbol: '$',
  language: 'en'
};

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
        currencySymbol: flat['currency_symbol'] || '$',
        language: flat['language_default'] || 'en'
      };
    } catch (err) {
      console.error('[FormattingService] Failed to load config:', err);
    }
  },

  getConfig() {
    return config;
  },

  formatCurrency(value: number) {
    const locale = config.numberFormat === '#.###,##' ? 'de-DE' : 'en-US';
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: config.decimalPrecision,
      maximumFractionDigits: config.decimalPrecision,
    }).format(value) + ' ' + config.currencySymbol;
  },

  formatDate(value: string | Date) {
    if (!value) return '';
    const date = new Date(value);
    
    // Simple replacement for common formats
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

  formatNumber(value: number) {
    const locale = config.numberFormat === '#.###,##' ? 'de-DE' : 'en-US';
    return new Intl.NumberFormat(locale, {
      minimumFractionDigits: config.decimalPrecision,
      maximumFractionDigits: config.decimalPrecision,
    }).format(value);
  }
};
