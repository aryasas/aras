import React, { useState, useEffect, useMemo } from 'react';
import { Download, AlertCircle, Check, Loader2, X } from 'lucide-react';
import Combobox from './Combobox';
import api from '../../lib/api';
import { cleanResourcePath } from '../../lib/resourceUtils';
import { useLanguage } from '../../context/LanguageContext';

interface ResourceField {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

interface ImportMappingProps {
  csvHeaders: string[];
  csvData: string[][];
  resourceFields: ResourceField[];
  file?: File | null;
  resourceApiPath?: string;
  onImport: (validatedData: Array<Record<string, string | number>>, importAll: boolean) => void;
  onCancel: () => void;
}

interface ValidatedRow {
  originalIndex: number;
  data: Record<string, string | number>;
  errors: string[];
  isValid: boolean;
}

interface PreviewResponse {
  total: number;
  valid: number;
  invalid: number;
  rows?: Array<{
    row?: number;
    ok?: boolean;
    errors?: unknown[];
    data?: Record<string, string | number>;
  }>;
  sample?: Array<{
    row?: number;
    ok?: boolean;
    errors?: unknown[];
    data?: Record<string, string | number>;
  }>;
}

const getPreviewErrorMessage = (error: unknown): string => {
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    error.response &&
    typeof error.response === 'object' &&
    'data' in error.response &&
    error.response.data &&
    typeof error.response.data === 'object'
  ) {
    const data = error.response.data as { detail?: string; message?: string; error?: string };
    return data.detail || data.message || data.error || 'Request failed';
  }
  if (error instanceof Error && error.message) return error.message;
  return 'Request failed';
};

const normalizePreviewErrors = (errors: unknown[] | undefined): string[] => {
  if (!Array.isArray(errors)) return [];
  return errors
    .map((entry) => {
      if (typeof entry === 'string') return entry;
      if (entry && typeof entry === 'object') {
        const typedEntry = entry as { message?: string; detail?: string; error?: string };
        return typedEntry.message || typedEntry.detail || typedEntry.error || '';
      }
      return '';
    })
    .filter((entry): entry is string => Boolean(entry));
};

const normalizePreviewRows = (
  response: PreviewResponse,
  fallbackRows: ValidatedRow[],
): ValidatedRow[] => {
  const sourceRows = response.rows && response.rows.length > 0
    ? response.rows
    : (response.sample || []);

  if (sourceRows.length === 0) return fallbackRows;

  return sourceRows.map((row, index) => ({
    originalIndex: typeof row.row === 'number' ? row.row : index + 1,
    data: row.data || {},
    errors: normalizePreviewErrors(row.errors),
    isValid: Boolean(row.ok),
  }));
};

export const ImportMapping: React.FC<ImportMappingProps> = ({
  csvHeaders,
  csvData,
  resourceFields,
  file,
  resourceApiPath,
  onImport,
  onCancel
}) => {
  const { t } = useLanguage();
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [validationStep, setValidationStep] = useState<'mapping' | 'preview'>('mapping');
  const [validatedRows, setValidatedRows] = useState<ValidatedRow[]>([]);
  const [showValidationErrors, setShowValidationErrors] = useState(false);
  const [previewCounts, setPreviewCounts] = useState({ total: 0, valid: 0, invalid: 0 });
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const requiredFields = useMemo(() =>
    resourceFields.filter(f => f.required).map(f => f.name)
  , [resourceFields]);

  const numericFields = useMemo(() =>
    resourceFields.filter(f => ['number', 'currency', 'float', 'integer'].includes(f.type)).map(f => f.name)
  , [resourceFields]);

  useEffect(() => {
    setValidationStep('mapping');
    setMapping({});
    setValidatedRows([]);
    setShowValidationErrors(false);
    setPreviewCounts({ total: 0, valid: 0, invalid: 0 });
    setPreviewError(null);
  }, [csvHeaders, resourceFields]);

  const runClientValidation = (activeMapping: Record<string, string>) => {
    const newValidatedRows: ValidatedRow[] = [];

    csvData.slice(1).forEach((row, rowIndex) => {
      const rowData: Record<string, string | number> = {};
      const rowErrors: string[] = [];
      let rowIsValid = true;

      csvHeaders.forEach((csvHeader, colIndex) => {
        const mappedField = activeMapping[csvHeader];
        if (mappedField) {
          let value: string | number = row[colIndex];

          if (requiredFields.includes(mappedField) && (!value || String(value).trim() === '')) {
            rowErrors.push(t('importMapping.requiredFieldMissing', 'Required field missing'));
            rowIsValid = false;
          }

          if (numericFields.includes(mappedField) && value && isNaN(Number(value))) {
            rowErrors.push(t('importMapping.mustBeNumber', 'Must be a number'));
            rowIsValid = false;
          }

          if (numericFields.includes(mappedField) && value && !isNaN(Number(value))) {
            value = Number(value);
          }

          rowData[mappedField] = value;
        }
      });

      newValidatedRows.push({
        originalIndex: rowIndex + 1,
        data: rowData,
        errors: rowErrors,
        isValid: rowIsValid,
      });
    });

    setValidatedRows(newValidatedRows);
    setPreviewCounts({
      total: newValidatedRows.length,
      valid: newValidatedRows.filter((row) => row.isValid).length,
      invalid: newValidatedRows.filter((row) => !row.isValid).length,
    });
    setPreviewError(null);
    setShowValidationErrors(newValidatedRows.some((row) => !row.isValid));
    setValidationStep('preview');
  };

  const runValidation = async (activeMapping: Record<string, string> = mapping) => {
    if (!file || !resourceApiPath) {
      runClientValidation(activeMapping);
      return;
    }

    setIsPreviewing(true);
    setPreviewError(null);

    const fallbackRows = csvData.slice(1).map((row, rowIndex) => {
      const rowData: Record<string, string | number> = {};
      csvHeaders.forEach((csvHeader, colIndex) => {
        const mappedField = activeMapping[csvHeader];
        if (!mappedField) return;
        rowData[mappedField] = row[colIndex];
      });
      return {
        originalIndex: rowIndex + 1,
        data: rowData,
        errors: [],
        isValid: true,
      };
    });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<PreviewResponse>(
        `/${cleanResourcePath(resourceApiPath)}/import/preview`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          params: { mapping: JSON.stringify(activeMapping) },
        },
      );

      setValidatedRows(normalizePreviewRows(response.data, fallbackRows));
      setPreviewCounts({
        total: response.data.total || 0,
        valid: response.data.valid || 0,
        invalid: response.data.invalid || 0,
      });
      setShowValidationErrors((response.data.invalid || 0) > 0);
      setValidationStep('preview');
    } catch (error) {
      setValidatedRows([]);
      setPreviewCounts({ total: 0, valid: 0, invalid: 0 });
      setPreviewError(getPreviewErrorMessage(error));
      setValidationStep('preview');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleMap = (csvHeader: string, modelField: string) => {
    setMapping(prev => {
      const newMap = { ...prev };
      if (modelField === '') {
        delete newMap[csvHeader];
      } else {
        newMap[csvHeader] = modelField;
      }
      return newMap;
    });
  };

  const autoMap = async () => {
    const newMap: Record<string, string> = {};
    resourceFields.forEach(rField => {
      const exactMatchHeader = csvHeaders.find(header =>
        header.toLowerCase() === rField.name.toLowerCase()
      );
      if (exactMatchHeader) {
        newMap[exactMatchHeader] = rField.name;
        return;
      }

      const fuzzyMatchHeader = csvHeaders.find(header =>
        header.toLowerCase().replace(/[^a-z0-9]/g, '') === rField.label.toLowerCase().replace(/[^a-z0-9]/g, '')
      );
      if (fuzzyMatchHeader) {
        newMap[fuzzyMatchHeader] = rField.name;
        return;
      }
    });
    setMapping(newMap);
    await runValidation(newMap);
  };

  const fieldOptions = resourceFields.map(f => ({ label: f.label, value: f.name }));

  const mappedResourceFields = useMemo(() => {
    const mappedNames = new Set(Object.values(mapping));
    return resourceFields.filter(f => mappedNames.has(f.name));
  }, [mapping, resourceFields]);

  const totalValidRows = previewCounts.valid;
  const totalErrorRows = previewCounts.invalid;
  const totalRows = previewCounts.total;

  if (validationStep === 'mapping') {
    return (
      <div className="flex flex-col h-full">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[var(--aras-muted)]">{t('importMapping.mapColumns', 'Map your file columns to the database fields.')}</p>
            <button
              onClick={autoMap}
              className="text-xs font-bold text-[var(--aras-accent)] hover:underline"
            >
              {t('importMapping.autoMatch', 'Auto-Match Fields')}
            </button>
          </div>

          <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-auto pr-2">
            {csvHeaders.map(header => (
              <div key={header} className="flex items-center gap-4 bg-[var(--aras-panel)] p-3 rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)]">
                <div className="flex-1">
                  <span className="text-xs font-bold text-[var(--aras-muted)] uppercase block mb-1">{t('importMapping.sourceColumn', 'Source Column')}</span>
                  <span className="text-sm font-medium text-[var(--aras-text)]">{header}</span>
                </div>

                <div className="flex-shrink-0">
                  <Download size={16} className="text-[var(--aras-muted)]" />
                </div>

                <div className="flex-1">
                  <span className="text-xs font-bold text-[var(--aras-muted)] uppercase block mb-1">{t('importMapping.targetField', 'Target Field')}</span>
                  <Combobox
                    options={fieldOptions}
                    value={mapping[header] || ''}
                    onChange={(val) => handleMap(header, val == null ? '' : String(val))}
                    placeholder={t('importMapping.ignoreColumn', '(Ignore Column)')}
                  />
                </div>
              </div>
            ))}
          </div>

          {Object.keys(mapping).length === 0 && (
            <div className="flex items-center gap-2 p-3 bg-amber-50 text-amber-700 rounded-[var(--aras-radius)] border border-amber-100">
              <AlertCircle size={18} />
              <span className="text-xs font-medium">{t('importMapping.noFieldsMapped', 'No fields mapped yet. Rows will be ignored.')}</span>
            </div>
          )}
        </div>

        <div className="mt-auto p-6 border-t border-[var(--aras-border)] bg-[var(--aras-panel-soft)] flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-bold text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] rounded-[var(--aras-radius)] transition-all"
          >
            {t('common.cancel', 'Cancel')}
          </button>
          <button
            onClick={() => { void runValidation(); }}
            disabled={Object.keys(mapping).length === 0 || isPreviewing}
            className="flex items-center gap-2 px-6 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] text-sm font-bold hover:brightness-110 transition-all shadow-md disabled:opacity-50"
          >
            {isPreviewing ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
            <span>{isPreviewing ? t('importMapping.validating', 'Validating...') : t('importMapping.validate', 'Validate')}</span>
          </button>
        </div>
      </div>
    );
  } else if (validationStep === 'preview') {
    return (
      <div className="flex flex-col h-full">
        <div className="p-6 space-y-4 flex-1 overflow-hidden">
          <h2 className="text-lg font-bold text-[var(--aras-text)]">{t('importMapping.validationPreview', 'Validation Preview')}</h2>
          <p className="text-sm text-[var(--aras-muted)]">
            {t('importMapping.counts', 'Total: {total} · Valid: {valid} · Invalid: {invalid}')
              .replace('{total}', String(totalRows))
              .replace('{valid}', String(totalValidRows))
              .replace('{invalid}', String(totalErrorRows))}
          </p>

          {previewError && (
            <div className="flex items-center gap-2 p-3 bg-rose-50 text-rose-700 rounded-[var(--aras-radius)] border border-rose-100">
              <AlertCircle size={18} />
              <span className="text-xs font-medium">{previewError}</span>
            </div>
          )}

          {totalErrorRows > 0 && (
            <div className="flex items-center justify-between p-3 bg-rose-50 text-rose-700 rounded-[var(--aras-radius)] border border-rose-100">
              <div className="flex items-center gap-2">
                <AlertCircle size={18} />
                <span className="text-xs font-medium">{t('importMapping.someRowsContainErrors', 'Some rows contain errors.')}</span>
              </div>
              <button
                onClick={() => setShowValidationErrors(!showValidationErrors)}
                className="text-xs font-bold text-rose-600 hover:underline"
              >
                {showValidationErrors
                  ? t('importMapping.hideErrors', 'Hide Errors')
                  : t('importMapping.showErrors', 'Show Errors')}
              </button>
            </div>
          )}

          <div className="flex-1 overflow-auto rounded-[var(--aras-radius)] border border-[var(--aras-border)]">
            <table className="min-w-full divide-y divide-[var(--aras-border)]">
              <thead className="bg-[var(--aras-panel-soft)] sticky top-0">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">{t('importMapping.rowNumber', '#')}</th>
                  {mappedResourceFields.map(field => (
                    <th key={field.name} className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">
                      {field.label} {field.required && <span className="text-rose-500">*</span>}
                    </th>
                  ))}
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">{t('importMapping.status', 'Status')}</th>
                </tr>
              </thead>
              <tbody className="bg-[var(--aras-panel)] divide-y divide-[var(--aras-border)]">
                {validatedRows.map(row => (
                  <tr key={row.originalIndex} className={row.isValid ? '' : 'bg-rose-50/50'}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-[var(--aras-text)]">
                      {row.originalIndex}
                    </td>
                    {mappedResourceFields.map(field => (
                      <td key={field.name} className="px-4 py-2 whitespace-nowrap text-sm text-[var(--aras-text)]">
                        {String(row.data[field.name] ?? '')}
                      </td>
                    ))}
                    <td className="px-4 py-2 text-sm text-[var(--aras-text)]">
                      {row.isValid ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-emerald-100 text-emerald-800">
                          {t('importMapping.valid', 'Valid')}
                        </span>
                      ) : (
                        <div className="space-y-2">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-rose-100 text-rose-800">
                            {t('importMapping.error', 'Error')}
                          </span>
                          {showValidationErrors && row.errors.length > 0 && (
                            <div className="space-y-1">
                              {row.errors.map((errorMessage, errorIndex) => (
                                <p key={`${row.originalIndex}-${errorIndex}`} className="text-[10px] text-rose-500">
                                  {errorMessage}
                                </p>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-auto p-6 border-t border-[var(--aras-border)] bg-[var(--aras-panel-soft)] flex items-center justify-end gap-3">
          <button
            onClick={() => setValidationStep('mapping')}
            className="px-4 py-2 text-sm font-bold text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] rounded-[var(--aras-radius)] transition-all"
          >
            <X size={18} className="inline-block mr-1" /> {t('importMapping.fixAndReupload', 'Fix & Re-upload')}
          </button>
          <button
            onClick={() => onImport(validatedRows.map(r => r.data), true)}
            disabled={validatedRows.length === 0 || totalErrorRows > 0 || Boolean(previewError)}
            className="flex items-center gap-2 px-6 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] text-sm font-bold hover:brightness-110 transition-all shadow-md disabled:opacity-50"
          >
            <Check size={18} />
            <span>{t('importMapping.importAll', 'Import All ({count})').replace('{count}', String(totalRows || validatedRows.length))}</span>
          </button>
        </div>
      </div>
    );
  }
  return null;
};
