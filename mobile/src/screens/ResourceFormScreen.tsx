// claude-opus-4-7
// ARC mobile resource form: stacked inputs, primary Save action LEFT in sticky action bar.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert, TextInput } from 'react-native';
import { ChevronLeft, Save, Trash2 } from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';

const C = theme.arc.light;

export const ResourceFormScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle, id, metadata } = route.params;
  const [form, setForm] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => { if (id) load(); }, [id]);

  const load = async () => {
    try {
      setLoading(true);
      const clean = resourceName.replace(/\//g, '_');
      const r = await api.get(`/${clean}/${id}`);
      setForm(r.data);
    } catch (e) { Alert.alert('Error', 'Failed to fetch'); }
    finally { setLoading(false); }
  };

  const save = async () => {
    try {
      setSaving(true);
      const clean = resourceName.replace(/\//g, '_');
      if (id) await api.patch(`/${clean}/${id}`, form);
      else await api.post(`/${clean}`, form);
      navigation.goBack();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to save');
    } finally { setSaving(false); }
  };

  const del = () => {
    Alert.alert('Delete?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: async () => {
        try {
          const clean = resourceName.replace(/\//g, '_');
          await api.delete(`/${clean}/${id}`);
          navigation.goBack();
        } catch { Alert.alert('Error', 'Failed to delete'); }
      }},
    ]);
  };

  const fields = (metadata?.fields || []).filter((f: any) => \!f.form_hidden && f.name \!== 'id');

  if (loading) return <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>;

  return (
    <SafeAreaView style={s.root}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.iconBtn}>
          <ChevronLeft size={20} color={C.text} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.idTop}><Text style={s.idBold}>res</Text>/{resourceName}{id ? `/${id}` : '/new'}</Text>
          <Text style={s.h1}>{id ? `Edit ${resourceTitle}` : `New ${resourceTitle}`}</Text>
        </View>
        {id && (
          <TouchableOpacity onPress={del} style={s.iconBtn}>
            <Trash2 size={18} color={theme.arc.danger} />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView contentContainerStyle={s.content}>
        {fields.map((f: any) => (
          <View key={f.name} style={s.fieldWrap}>
            <Text style={s.label}>{(f.label || f.name).toUpperCase()}</Text>
            <TextInput
              style={s.input}
              value={form[f.name] \!= null ? String(form[f.name]) : ''}
              onChangeText={(v) => setForm({ ...form, [f.name]: v })}
              keyboardType={f.type === 'number' || f.type === 'currency' ? 'numeric' : 'default'}
              placeholder={`Enter ${f.label || f.name}`}
              placeholderTextColor={C.text3}
            />
          </View>
        ))}
      </ScrollView>

      <View style={s.actionBar}>
        <TouchableOpacity style={s.btnPrimary} onPress={save} disabled={saving} activeOpacity={0.85}>
          {saving ? <ActivityIndicator color={theme.arc.accentInk} /> : (
            <>
              <Save size={14} color={theme.arc.accentInk} />
              <Text style={s.btnPrimaryText}>{id ? 'Update' : 'Create'}</Text>
            </>
          )}
        </TouchableOpacity>
        <View style={{ flex: 1 }} />
        <TouchableOpacity style={s.btnGhost} onPress={() => navigation.goBack()} activeOpacity={0.7}>
          <Text style={s.btnGhostText}>Cancel</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 14, paddingTop: 20, backgroundColor: C.surface, borderBottomWidth: 1, borderBottomColor: C.line },
  iconBtn: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 8 },
  idTop: { fontFamily: 'Menlo', fontSize: 11, color: C.text3 },
  idBold: { color: C.text, fontWeight: '700' },
  h1: { ...theme.typography.h3, color: C.text, marginTop: 2 },
  content: { padding: 18, paddingBottom: 80 },
  fieldWrap: { marginBottom: 14 },
  label: { ...theme.typography.caption, color: C.text2, marginBottom: 6 },
  input: { height: 40, borderWidth: 1, borderColor: C.line, borderRadius: 8, paddingHorizontal: 12, color: C.text, backgroundColor: C.surface, fontFamily: 'PlusJakartaSans_400Regular', fontSize: 14 },
  actionBar: { position: 'absolute', left: 0, right: 0, bottom: 0, flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, paddingBottom: 20, backgroundColor: C.surface, borderTopWidth: 1, borderTopColor: C.line },
  btnPrimary: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, paddingHorizontal: 14, borderRadius: 8, backgroundColor: theme.arc.accent },
  btnPrimaryText: { color: theme.arc.accentInk, fontWeight: '600', fontSize: 13 },
  btnGhost: { height: 36, paddingHorizontal: 14, justifyContent: 'center' },
  btnGhostText: { color: C.text2, fontSize: 13 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: C.bg },
});
