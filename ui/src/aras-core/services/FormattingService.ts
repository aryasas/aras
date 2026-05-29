import api from '../../lib/api';

export interface RegionalConfig {
  dateFormat: string;
  numberFormat: string;
  decimalPrecision: number;
  currencySymbol: string;
  language: string;
}

interface SettingRow {
  key: string;
  value: string;
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
      const response = await api.post('/sys_settings/query', {
        filters: [{ field: 'key', op: 'ilike', value: 'core.' }]
      });
      
      const settingsMap: Record<string, string> = {};
      const rows = Array.isArray(response.data.items) ? response.data.items as SettingRow[] : [];
      rows.forEach((s) => {
        settingsMap[s.key] = s.value;
      });

      config = {
        dateFormat: settingsMap['core.date_format'] || 'YYYY-MM-DD',
        numberFormat: settingsMap['core.number_format'] || '#,###.##',
        decimalPrecision: parseInt(settingsMap['core.decimal_precision'] || '2'),
        currencySymbol: settingsMap['core.currency_symbol'] || '$',
        language: settingsMap['core.language_default'] || 'en'
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
