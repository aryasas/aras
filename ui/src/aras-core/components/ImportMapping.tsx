import React, { useState, useEffect, useMemo } from 'react';
import { Download, AlertCircle, Check, X } from 'lucide-react';
import Combobox from './Combobox';
import { useAras } from '../hooks/useAras'; // Assuming useAras for notify

interface ResourceField {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

interface ImportMappingProps {
  csvHeaders: string[];
  csvData: string[][]; // New prop for the full CSV data
  resourceFields: ResourceField[]; // Changed to ResourceField[] to get required/type
  onImport: (validatedData: any[], importAll: boolean) => void; // Changed onConfirm to onImport
  onCancel: () => void;
}

interface ValidatedRow {
  originalIndex: number;
  data: Record<string, any>;
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
  const [showValidationErrors, setShowValidationErrors] = useState(false); // To toggle error display
  const { notify } = useAras();

  // Extract required and numeric fields from resourceFields
  const requiredFields = useMemo(() => 
    resourceFields.filter(f => f.required).map(f => f.name)
  , [resourceFields]);

  const numericFields = useMemo(() => 
    resourceFields.filter(f => ['number', 'currency', 'float', 'integer'].includes(f.type)).map(f => f.name)
  , [resourceFields]);

  useEffect(() => {
    // Reset validation step if csvHeaders or resourceFields change
    setValidationStep('mapping');
    setMapping({});
    setValidatedRows([]);
  }, [csvHeaders, resourceFields]);



    setValidatedRows([]);
  }, [csvHeaders, resourceFields]);

  const runValidation = () => {
    const newValidatedRows: ValidatedRow[] = [];
    let validCount = 0;

    csvData.slice(1).forEach((row, rowIndex) => { // Skip header row
      const rowData: Record<string, any> = {};
      const rowErrors: Record<string, string> = {};
      let rowIsValid = true;

      csvHeaders.forEach((csvHeader, colIndex) => {
        const mappedField = mapping[csvHeader];
        if (mappedField) {
          let value: any = row[colIndex];

          // Required field validation
          if (requiredFields.includes(mappedField) && (!value || String(value).trim() === '')) {
            rowErrors[mappedField] = `Required field missing`;
            rowIsValid = false;
          }

          // Numeric field validation
          if (numericFields.includes(mappedField) && value && isNaN(Number(value))) {
            rowErrors[mappedField] = `Must be a number`;
            rowIsValid = false;
          }
          
          // Type conversion for numbers
          if (numericFields.includes(mappedField) && value && !isNaN(Number(value))) {
            value = Number(value);
          }

          rowData[mappedField] = value;
        }
      });

      if (rowIsValid) {
        validCount++;
      }

      newValidatedRows.push({
        originalIndex: rowIndex + 1, // +1 for 0-based index, +1 for skipping header
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
      // Prioritize exact matches with resourceFields.name
      const exactMatchHeader = csvHeaders.find(header => 
        header.toLowerCase() === rField.name.toLowerCase()
      );
      if (exactMatchHeader) {
        newMap[exactMatchHeader] = rField.name;
        return;
      }

      // Then try fuzzy matching with resourceFields.label
      const fuzzyMatchHeader = csvHeaders.find(header =>
        header.toLowerCase().replace(/[^a-z0-9]/g, '') === rField.label.toLowerCase().replace(/[^a-z0-9]/g, '')
      );
      if (fuzzyMatchHeader) {
        newMap[fuzzyMatchHeader] = rField.name;
        return;
      }
    });
    setMapping(newMap);
    // After auto-mapping, immediately move to validation preview.
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
            <p className="text-sm text-slate-500">Map your CSV columns to the database fields.</p>
            <button 
              onClick={autoMap}
              className="text-xs font-bold text-indigo-600 hover:underline"
            >
              Auto-Match Fields
            </button>
          </div>

          <div className="space-y-2 max-h-[calc(100vh-300px)] overflow-auto pr-2">
            {csvHeaders.map(header => (
              <div key={header} className="flex items-center gap-4 bg-white p-3 rounded-2xl border border-slate-200">
                <div className="flex-1">
                  <span className="text-xs font-bold text-slate-400 uppercase block mb-1">CSV Column</span>
                  <span className="text-sm font-medium text-slate-700">{header}</span>
                </div>
                
                <div className="flex-shrink-0">
                  <Download size={16} className="text-slate-300" />
                </div>

                <div className="flex-1">
                  <span className="text-xs font-bold text-slate-400 uppercase block mb-1">Target Field</span>
                  <Combobox 
                    options={fieldOptions}
                    value={mapping[header] || ''}
                    onChange={(val) => handleMap(header, val)}
                    placeholder="(Ignore Column)"
                  />
                </div>
              </div>
            ))}
          </div>

          {Object.keys(mapping).length === 0 && (
            <div className="flex items-center gap-2 p-3 bg-amber-50 text-amber-700 rounded-xl border border-amber-100">
              <AlertCircle size={18} />
              <span className="text-xs font-medium">No fields mapped yet. Rows will be ignored.</span>
            </div>
          )}
        </div>

        <div className="mt-auto p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-3">
          <button 
            onClick={onCancel}
            className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-white rounded-xl transition-all"
          >
            Cancel
          </button>
          <button 
            onClick={runValidation} // Changed to runValidation
            disabled={Object.keys(mapping).length === 0}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
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
          <h2 className="text-lg font-bold text-slate-800">Validation Preview</h2>
          <p className="text-sm text-slate-500">
            {totalValidRows} valid rows, {totalErrorRows} rows with errors.
          </p>

          {totalErrorRows > 0 && (
            <div className="flex items-center justify-between p-3 bg-rose-50 text-rose-700 rounded-xl border border-rose-100">
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

          <div className="flex-1 overflow-auto rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 sticky top-0">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">#</th>
                  {mappedResourceFields.map(field => (
                    <th key={field.name} className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      {field.label} {field.required && <span className="text-rose-500">*</span>}
                    </th>
                  ))}
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-200">
                {validatedRows.map(row => (
                  <tr key={row.originalIndex} className={row.isValid ? '' : 'bg-rose-50/50'}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-slate-900">
                      {row.originalIndex}
                    </td>
                    {mappedResourceFields.map(field => (
                      <td key={field.name} className="px-4 py-2 whitespace-nowrap text-sm text-slate-700">
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

        <div className="mt-auto p-6 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-3">
          <button
            onClick={() => setValidationStep('mapping')}
            className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-white rounded-xl transition-all"
          >
            <X size={18} className="inline-block mr-1" /> Fix & Re-upload
          </button>
          {totalValidRows > 0 && (
            <button
              onClick={() => onImport(validatedRows.filter(r => r.isValid).map(r => r.data), false)}
              className="px-4 py-2 text-sm font-bold text-amber-600 bg-amber-50 hover:bg-amber-100 rounded-xl transition-all border border-amber-100 shadow-sm"
            >
              Import Valid Rows ({totalValidRows})
            </button>
          )}
          <button
            onClick={() => onImport(validatedRows.map(r => r.data), true)}
            disabled={validatedRows.length === 0}
            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl text-sm font-bold hover:bg-indigo-700 transition-all shadow-md shadow-indigo-100 disabled:opacity-50"
          >
            <Check size={18} />
            <span>Import All ({validatedRows.length})</span>
          </button>
        </div>
      </div>
    );
  }
  return null; // Should not reach here
};

