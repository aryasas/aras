import React, { useState, useEffect, useMemo } from 'react';
import { Download, AlertCircle, Check, X } from 'lucide-react';
import Combobox from './Combobox';

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
  onImport: (validatedData: Array<Record<string, string | number>>, importAll: boolean) => void;
  onCancel: () => void;
}

interface ValidatedRow {
  originalIndex: number;
  data: Record<string, string | number>;
  errors: Record<string, string>;
  isValid: boolean;
}

export const ImportMapping: React.FC<ImportMappingProps> = ({
  csvHeaders,
  csvData,
  resourceFields,
  onImport,
  onCancel
}) => {
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [validationStep, setValidationStep] = useState<'mapping' | 'preview'>('mapping');
  const [validatedRows, setValidatedRows] = useState<ValidatedRow[]>([]);
  const [showValidationErrors, setShowValidationErrors] = useState(false);

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
  }, [csvHeaders, resourceFields]);

  const runValidation = () => {
    const newValidatedRows: ValidatedRow[] = [];

    csvData.slice(1).forEach((row, rowIndex) => {
      const rowData: Record<string, string | number> = {};
      const rowErrors: Record<string, string> = {};
      let rowIsValid = true;

      csvHeaders.forEach((csvHeader, colIndex) => {
        const mappedField = mapping[csvHeader];
        if (mappedField) {
          let value: string | number = row[colIndex];

          if (requiredFields.includes(mappedField) && (!value || String(value).trim() === '')) {
            rowErrors[mappedField] = `Required field missing`;
            rowIsValid = false;
          }

          if (numericFields.includes(mappedField) && value && isNaN(Number(value))) {
            rowErrors[mappedField] = `Must be a number`;
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
    setValidationStep('preview');
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

  const autoMap = () => {
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
    runValidation();
  };

  const fieldOptions = resourceFields.map(f => ({ label: f.label, value: f.name }));

  const mappedResourceFields = useMemo(() => {
    const mappedNames = new Set(Object.values(mapping));
    return resourceFields.filter(f => mappedNames.has(f.name));
  }, [mapping, resourceFields]);

  const totalValidRows = validatedRows.filter(row => row.isValid).length;
  const totalErrorRows = validatedRows.length - totalValidRows;

  if (validationStep === 'mapping') {
    return (
      <div className="flex flex-col h-full">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[var(--aras-muted)]">Map your CSV columns to the database fields.</p>
            <button
              onClick={autoMap}
              className="text-xs font-bold text-[var(--aras-accent)] hover:underline"
            >
              Auto-Match Fields
            </button>
          </div>

          <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-auto pr-2">
            {csvHeaders.map(header => (
              <div key={header} className="flex items-center gap-4 bg-[var(--aras-panel)] p-3 rounded-[var(--aras-radius-lg)] border border-[var(--aras-border)]">
                <div className="flex-1">
                  <span className="text-xs font-bold text-[var(--aras-muted)] uppercase block mb-1">CSV Column</span>
                  <span className="text-sm font-medium text-[var(--aras-text)]">{header}</span>
                </div>

                <div className="flex-shrink-0">
                  <Download size={16} className="text-[var(--aras-muted)]" />
                </div>

                <div className="flex-1">
                  <span className="text-xs font-bold text-[var(--aras-muted)] uppercase block mb-1">Target Field</span>
                  <Combobox
                    options={fieldOptions}
                    value={mapping[header] || ''}
                    onChange={(val) => handleMap(header, val == null ? '' : String(val))}
                    placeholder="(Ignore Column)"
                  />
                </div>
              </div>
            ))}
          </div>

          {Object.keys(mapping).length === 0 && (
            <div className="flex items-center gap-2 p-3 bg-amber-50 text-amber-700 rounded-[var(--aras-radius)] border border-amber-100">
              <AlertCircle size={18} />
              <span className="text-xs font-medium">No fields mapped yet. Rows will be ignored.</span>
            </div>
          )}
        </div>

        <div className="mt-auto p-6 border-t border-[var(--aras-border)] bg-[var(--aras-panel-soft)] flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-bold text-[var(--aras-muted)] hover:bg-[var(--aras-panel)] rounded-[var(--aras-radius)] transition-all"
          >
            Cancel
          </button>
          <button
            onClick={runValidation}
            disabled={Object.keys(mapping).length === 0}
            className="flex items-center gap-2 px-6 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] text-sm font-bold hover:brightness-110 transition-all shadow-md disabled:opacity-50"
          >
            <Check size={18} />
            <span>Validate</span>
          </button>
        </div>
      </div>
    );
  } else if (validationStep === 'preview') {
    return (
      <div className="flex flex-col h-full">
        <div className="p-6 space-y-4 flex-1 overflow-hidden">
          <h2 className="text-lg font-bold text-[var(--aras-text)]">Validation Preview</h2>
          <p className="text-sm text-[var(--aras-muted)]">
            {totalValidRows} valid rows, {totalErrorRows} rows with errors.
          </p>

          {totalErrorRows > 0 && (
            <div className="flex items-center justify-between p-3 bg-rose-50 text-rose-700 rounded-[var(--aras-radius)] border border-rose-100">
              <div className="flex items-center gap-2">
                <AlertCircle size={18} />
                <span className="text-xs font-medium">Some rows contain errors.</span>
              </div>
              <button
                onClick={() => setShowValidationErrors(!showValidationErrors)}
                className="text-xs font-bold text-rose-600 hover:underline"
              >
                {showValidationErrors ? 'Hide Errors' : 'Show Errors'}
              </button>
            </div>
          )}

          <div className="flex-1 overflow-auto rounded-[var(--aras-radius)] border border-[var(--aras-border)]">
            <table className="min-w-full divide-y divide-[var(--aras-border)]">
              <thead className="bg-[var(--aras-panel-soft)] sticky top-0">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">#</th>
                  {mappedResourceFields.map(field => (
                    <th key={field.name} className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">
                      {field.label} {field.required && <span className="text-rose-500">*</span>}
                    </th>
                  ))}
                  <th className="px-4 py-2 text-left text-xs font-medium text-[var(--aras-muted)] uppercase tracking-wider">Status</th>
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
                        {showValidationErrors && row.errors[field.name] && (
                          <p className="text-[10px] text-rose-500">{row.errors[field.name]}</p>
                        )}
                      </td>
                    ))}
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      {row.isValid ? (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-emerald-100 text-emerald-800">
                          Valid
                        </span>
                      ) : (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-rose-100 text-rose-800">
                          Error
                        </span>
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
            <X size={18} className="inline-block mr-1" /> Fix & Re-upload
          </button>
          {totalValidRows > 0 && (
            <button
              onClick={() => onImport(validatedRows.filter(r => r.isValid).map(r => r.data), false)}
              className="px-4 py-2 text-sm font-bold text-amber-600 bg-amber-50 hover:bg-amber-100 rounded-[var(--aras-radius)] transition-all border border-amber-100 shadow-sm"
            >
              Import Valid Rows ({totalValidRows})
            </button>
          )}
          <button
            onClick={() => onImport(validatedRows.map(r => r.data), true)}
            disabled={validatedRows.length === 0}
            className="flex items-center gap-2 px-6 py-2 bg-[var(--aras-accent)] text-white rounded-[var(--aras-radius)] text-sm font-bold hover:brightness-110 transition-all shadow-md disabled:opacity-50"
          >
            <Check size={18} />
            <span>Import All ({validatedRows.length})</span>
          </button>
        </div>
      </div>
    );
  }
  return null;
};
