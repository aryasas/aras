// claude-sonnet-4-6
import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Switch,
  Modal,
  FlatList,
  RefreshControl,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { ChevronLeft, Check, Search, Trash2, X } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell } from '../components/MobileShell';
import api from '../lib/api';
import { useToastStore } from '../lib/toast';
import { haptic } from '../lib/haptics';

const C = theme.arc.dark;

type FieldMeta = {
  name: string;
  label?: string;
  ui_type?: string;
  type?: string;
  form_hidden?: boolean;
  readonly?: boolean;
  required?: boolean;
  target_resource?: string;
  primary_field?: string;
  choices?: Array<string | { label?: string; value?: string | number | boolean }>;
  options?: Array<string | { label?: string; value?: string | number | boolean }>;
};

// claude-sonnet-4-6
export const ResourceFormScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle, id, metadata: initialMetadata } = route.params;
  const [metadata, setMetadata] = useState<any>(initialMetadata || null);
  const [form, setForm] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [offline, setOffline] = useState(false);
  const [lookupField, setLookupField] = useState<FieldMeta | null>(null);
  const [lookupQuery, setLookupQuery] = useState('');
  const [lookupResults, setLookupResults] = useState<any[]>([]);
  const [lookupLoading, setLookupLoading] = useState(false);
  const showToast = useToastStore((state) => state.show);

  // claude-sonnet-4-6
  useEffect(() => {
    load();
  }, [resourceName, id]);

  // claude-sonnet-4-6
  useEffect(() => {
    const unsubscribe = navigation.addListener('beforeRemove', (e: any) => {
      if (!isDirty || saving) return;
      e.preventDefault();
      Alert.alert(
        'Discard changes?',
        'You have unsaved changes. Leave without saving?',
        [
          { text: 'Keep editing', style: 'cancel' },
          { text: 'Discard', style: 'destructive', onPress: () => navigation.dispatch(e.data.action) },
        ]
      );
    });
    return unsubscribe;
  }, [navigation, isDirty, saving]);

  const fields = useMemo(
    () => ((metadata?.fields || []) as FieldMeta[]).filter((f) => f.form_hidden !== true && f.name !== 'id'),
    [metadata]
  );

  const fieldLabels = useMemo(() => {
    return fields.reduce<Record<string, string>>((acc, field) => {
      acc[field.name] = field.label || field.name.replace(/_/g, ' ');
      return acc;
    }, {});
  }, [fields]);

  const shellTitle = id == null ? `New ${resourceTitle || 'Item'}` : resourceTitle || 'Item';

  // claude-sonnet-4-6
  const closeLookupModal = () => {
    setLookupField(null);
    setLookupQuery('');
    setLookupResults([]);
    setLookupLoading(false);
  };

  // claude-sonnet-4-6
  const getLookupDisplayValue = (field: FieldMeta, item: any) => {
    const primaryField = field.primary_field;
    return item?.name || item?.title || (primaryField ? item?.[primaryField] : undefined) || item?.id;
  };

  // claude-sonnet-4-6
  const openLookupModal = (field: FieldMeta) => {
    if (!field.target_resource) return;
    setLookupField(field);
    setLookupQuery('');
    setLookupResults([]);
  };

  // claude-sonnet-4-6
  const selectLookupItem = (field: FieldMeta, item: any) => {
    const displayValue = getLookupDisplayValue(field, item);
    setForm((current: any) => ({
      ...current,
      [field.name]: item?.id,
      [`${field.name}_display`]: displayValue != null ? String(displayValue) : '',
    }));
    closeLookupModal();
  };

  // claude-sonnet-4-6
  const load = async () => {
    try {
      setLoading(true);
      setOffline(false);
      const requests = id
        ? [api.get(`/${resourceName}/metadata`), api.get(`/${resourceName}/${id}`)]
        : [api.get(`/${resourceName}/metadata`)];
      const [metaResponse, recordResponse] = await Promise.all(requests);
      setMetadata(metaResponse.data);
      setForm(id && recordResponse ? recordResponse.data || {} : {});
    } catch (error: any) {
      const isNetworkError = error?.code === 'ERR_NETWORK' || error?.message?.includes('Network Error');
      if (isNetworkError) {
        setOffline(true);
        return;
      }
      Alert.alert('Error', 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  // claude-sonnet-4-6
  const save = async () => {
    const missingFields = fields.filter((field) => {
      if (!field.required) return false;
      const value = form[field.name];
      return value === null || value === undefined || value === '';
    });

    if (missingFields.length > 0) {
      haptic.error();
      Alert.alert(
        'Required fields missing',
        missingFields.map((field) => field.label || field.name.replace(/_/g, ' ')).join(', ')
      );
      return;
    }

    try {
      setSaving(true);
      if (id) await api.patch(`/${resourceName}/${id}`, form);
      else await api.post(`/${resourceName}`, form);
      haptic.success();
      setIsDirty(false);
      showToast(id ? 'Changes saved' : `${resourceTitle || 'Record'} created`, 'success');
      navigation.goBack();
    } catch (e: any) {
      const detail = e?.response?.data?.detail;
      if (e?.response?.status === 422 && Array.isArray(detail)) {
        haptic.error();
        const messages = detail.map((item: any) => {
          const loc = Array.isArray(item?.loc) ? item.loc.filter(Boolean).slice(1).join('.') : '';
          const fieldName = loc || item?.loc?.[1] || item?.field || 'field';
          const label = fieldLabels[fieldName] || fieldName;
          return `${label}: ${item?.msg || 'Invalid value'}`;
        });
        Alert.alert('Validation error', messages.join('\n'));
        return;
      }

      if (e?.code === 'ERR_NETWORK' || e?.message?.includes('Network Error')) {
        Alert.alert('Offline', 'No internet connection. Your changes were not saved.');
        return;
      }

      Alert.alert('Error', typeof detail === 'string' ? detail : e?.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  // claude-sonnet-4-6
  const doDelete = async () => {
    try {
      await api.delete(`/${resourceName}/${id}`);
      showToast(`${resourceTitle || 'Record'} deleted`, 'success');
      navigation.goBack();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e?.message || 'Failed to delete');
    }
  };

  // claude-sonnet-4-6
  const confirmDelete = () => {
    Alert.alert('Delete', 'Are you sure?', [
      { text: 'Cancel' },
      { text: 'Delete', style: 'destructive', onPress: doDelete },
    ]);
  };

  // claude-sonnet-4-6
  const setField = (name: string, value: any) => {
    setIsDirty(true);
    setForm((current: any) => ({ ...current, [name]: value }));
  };

  // claude-sonnet-4-6
  const renderField = (field: FieldMeta) => {
    const type = (field.ui_type || field.type || 'text').toLowerCase();
    const value = form[field.name];
    const label = field.label || field.name.replace(/_/g, ' ');

    if (type === 'boolean') {
      return (
        <View key={field.name} style={s.fieldBlock}>
          <Text style={s.label}>{label}</Text>
          <View style={s.switchRow}>
            <Text style={s.switchValue}>{value ? 'Yes' : 'No'}</Text>
            <Switch
              value={Boolean(value)}
              onValueChange={(next) => setField(field.name, next)}
              thumbColor={value ? theme.arc.accent : C.text3}
              trackColor={{ false: C.line2, true: 'rgba(232,155,108,0.45)' }}
            />
          </View>
        </View>
      );
    }

    if (type === 'select') {
      const options = field.choices || field.options || [];
      return (
        <View key={field.name} style={s.fieldBlock}>
          <Text style={s.label}>{label}</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.optionRow}>
            {options.map((option: any) => {
              const optionValue = typeof option === 'object' ? option.value : option;
              const optionLabel = typeof option === 'object' ? option.label || option.value : option;
              const active = String(value ?? '') === String(optionValue ?? '');
              return (
                <TouchableOpacity
                  key={String(optionValue)}
                  style={[s.optionPill, active && s.optionPillActive]}
                  activeOpacity={0.75}
                  onPress={() => setField(field.name, optionValue)}
                >
                  <Text style={[s.optionText, active && s.optionTextActive]}>{String(optionLabel)}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
      );
    }

    const isTextarea = type === 'textarea';
    const isLookup = type === 'lookup';
    const lookupValue = form[`${field.name}_display`] || form[`${field.name}_name`] || value;
    const keyboardType = ['number', 'integer', 'float'].includes(type)
      ? 'numeric'
      : type === 'email'
        ? 'email-address'
        : 'default';

    return (
      <View key={field.name} style={s.fieldBlock}>
        <Text style={s.label}>{label}</Text>
        {isLookup && field.target_resource ? (
          <TouchableOpacity
            style={[s.lookupRow, field.readonly && s.lookupRowDisabled]}
            activeOpacity={field.readonly ? 1 : 0.8}
            onPress={() => !field.readonly && openLookupModal(field)}
            disabled={field.readonly}
          >
            <Text
              style={[
                s.lookupValue,
                !lookupValue && s.lookupPlaceholder,
              ]}
              numberOfLines={1}
            >
              {lookupValue != null && lookupValue !== '' ? String(lookupValue) : `Select ${label}`}
            </Text>
            <Search size={16} color={C.text3} />
          </TouchableOpacity>
        ) : (
          <TextInput
            value={(isLookup ? lookupValue : value) != null ? String(isLookup ? lookupValue : value) : ''}
            onChangeText={(next) => setField(field.name, next)}
            editable={!field.readonly}
            multiline={isTextarea}
            numberOfLines={isTextarea ? 4 : 1}
            keyboardType={keyboardType}
            placeholder={type === 'date' ? 'YYYY-MM-DD' : label}
            placeholderTextColor={C.text3}
            style={[s.input, isTextarea && s.textarea, isLookup && s.readonlyInput]}
          />
        )}
      </View>
    );
  };

  // claude-sonnet-4-6
  useEffect(() => {
    if (!lookupField?.target_resource) return;

    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        setLookupLoading(true);
        const response = await api.get(`/${lookupField.target_resource}/search?q=${encodeURIComponent(lookupQuery)}`);
        if (cancelled) return;
        const data = response.data;
        const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
        setLookupResults(items);
      } catch {
        if (!cancelled) setLookupResults([]);
      } finally {
        if (!cancelled) setLookupLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [lookupField, lookupQuery]);

  const headerRight = id ? (
    <TouchableOpacity style={s.deleteButton} onPress={confirmDelete} activeOpacity={0.75}>
      <Trash2 size={18} color={theme.arc.danger} />
    </TouchableOpacity>
  ) : null;

  if (loading) {
    return (
      <MobileShell active="items" title={shellTitle} headerRight={headerRight} navigation={navigation}>
        <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>
      </MobileShell>
    );
  }

  return (
    <MobileShell active="items" title={shellTitle} headerRight={headerRight} navigation={navigation}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView
          contentContainerStyle={s.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} colors={[theme.arc.accent]} tintColor={theme.arc.accent} />}
        >
          {offline ? (
            <View style={s.offlineBanner}>
              <Text style={s.offlineText}>Offline - pull to refresh</Text>
            </View>
          ) : null}

          <TouchableOpacity style={s.backButton} onPress={() => navigation.goBack()} activeOpacity={0.75}>
            <ChevronLeft size={18} color={C.text} />
            <Text style={s.backText}>Back</Text>
          </TouchableOpacity>

          <Text style={s.heading}>{id ? `Edit ${resourceTitle}` : `New ${resourceTitle}`}</Text>

          <View style={s.formStack}>
            {fields.map(renderField)}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>

      <View style={s.actionBar}>
        <TouchableOpacity style={s.saveButton} onPress={save} disabled={saving} activeOpacity={0.85}>
          {saving ? (
            <ActivityIndicator color={theme.arc.accentInk} />
          ) : (
            <>
              <Check size={16} color={theme.arc.accentInk} />
              <Text style={s.saveText}>{id ? 'Save Changes' : 'Create'}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      <Modal visible={Boolean(lookupField)} animationType="slide" onRequestClose={closeLookupModal}>
        <View style={s.lookupModal}>
          <TouchableOpacity style={s.lookupCloseButton} onPress={closeLookupModal} activeOpacity={0.75}>
            <X size={20} color={C.text} />
          </TouchableOpacity>

          <TextInput
            value={lookupQuery}
            onChangeText={setLookupQuery}
            placeholder="Search"
            placeholderTextColor={C.text3}
            autoCorrect={false}
            autoCapitalize="none"
            style={s.lookupSearchInput}
          />

          <FlatList
            data={lookupResults}
            keyExtractor={(item, index) => String(item?.id ?? index)}
            contentContainerStyle={s.lookupResults}
            ListEmptyComponent={lookupLoading ? (
              <View style={s.lookupEmpty}>
                <ActivityIndicator color={theme.arc.accent} />
              </View>
            ) : (
              <View style={s.lookupEmpty}>
                <Text style={s.lookupEmptyText}>No results</Text>
              </View>
            )}
            renderItem={({ item }) => {
              if (!lookupField) return null;
              const displayValue = getLookupDisplayValue(lookupField, item);
              return (
                <TouchableOpacity
                  style={s.lookupResultRow}
                  onPress={() => selectLookupItem(lookupField, item)}
                  activeOpacity={0.75}
                >
                  <Text style={s.lookupResultText} numberOfLines={1}>
                    {displayValue != null ? String(displayValue) : String(item?.id ?? '')}
                  </Text>
                </TouchableOpacity>
              );
            }}
          />
        </View>
      </Modal>
    </MobileShell>
  );
};

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16, paddingBottom: 150 },
  offlineBanner: {
    marginBottom: 16,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ca8a04',
    backgroundColor: '#1c1505',
  },
  offlineText: { color: '#fef08a', fontSize: 12.5, fontWeight: '600' },
  backButton: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 4, paddingVertical: 8, paddingRight: 10 },
  backText: { color: C.text, fontSize: 13.5, fontWeight: '600' },
  heading: { color: C.text, fontSize: 22, fontWeight: '700', marginTop: 4, marginBottom: 18 },
  formStack: { gap: 16 },
  fieldBlock: { gap: 7 },
  label: { color: C.text2, fontSize: 12.5, fontWeight: '700', textTransform: 'capitalize' },
  input: {
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: C.text,
    backgroundColor: C.surface,
    fontFamily: 'PlusJakartaSans_400Regular',
    fontSize: 13.5,
  },
  textarea: { minHeight: 104, textAlignVertical: 'top' },
  readonlyInput: { color: C.text3, backgroundColor: C.surface2 },
  lookupRow: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  lookupRowDisabled: { opacity: 0.7 },
  lookupValue: { flex: 1, color: C.text, fontSize: 13.5, fontWeight: '500' },
  lookupPlaceholder: { color: C.text3, fontWeight: '400' },
  switchRow: {
    height: 44,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    backgroundColor: C.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  switchValue: { color: C.text, fontSize: 13.5, fontWeight: '600' },
  optionRow: { gap: 8 },
  optionPill: {
    height: 34,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: C.line,
    justifyContent: 'center',
    backgroundColor: C.surface,
  },
  optionPillActive: { borderColor: theme.arc.accent, backgroundColor: 'rgba(232,155,108,0.14)' },
  optionText: { color: C.text3, fontSize: 12.5, fontWeight: '600' },
  optionTextActive: { color: theme.arc.accent },
  actionBar: { position: 'absolute', left: 12, right: 12, bottom: 90 },
  saveButton: {
    height: 46,
    borderRadius: 12,
    backgroundColor: theme.arc.accent,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 7,
  },
  saveText: { color: theme.arc.accentInk, fontSize: 14, fontWeight: '700' },
  deleteButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    backgroundColor: 'rgba(255,107,122,0.12)',
  },
  lookupModal: {
    flex: 1,
    backgroundColor: C.bg,
    padding: 16,
    paddingTop: 56,
  },
  lookupCloseButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.line,
    zIndex: 2,
  },
  lookupSearchInput: {
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    paddingRight: 44,
    color: C.text,
    backgroundColor: C.surface,
    fontFamily: 'PlusJakartaSans_400Regular',
    fontSize: 14,
  },
  lookupResults: { paddingTop: 14, paddingBottom: 24 },
  lookupResultRow: {
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  lookupResultText: { color: C.text, fontSize: 14, fontWeight: '500' },
  lookupEmpty: { paddingVertical: 32, alignItems: 'center' },
  lookupEmptyText: { color: C.text3, fontSize: 13 },
});
