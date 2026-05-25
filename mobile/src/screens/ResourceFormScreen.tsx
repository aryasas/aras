// claude-opus-4-7
// ARC mobile form: header card (kind chip + status + mono id + title + meta),
// tabs strip, summary + meta grid + lifecycle + affected items, sticky Defer/Approve.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { Share2, MoreHorizontal, Check, ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell, MonoId, Avatar, StatusGlyph } from '../components/MobileShell';
import api from '../lib/api';

const C = theme.arc.dark;

const TABS = ['Overview', 'Affected', 'Thread', 'Flow', 'History'];
const LIFECYCLE = ['Draft', 'Eng', 'CCB', 'Released'];

export const ResourceFormScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle, id, metadata } = route.params;
  const [form, setForm] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState('Overview');

  useEffect(() => { if (id) load(); }, [id]);

  const load = async () => {
    try {
      setLoading(true);
      const r = await api.get(`/${resourceName}/${id}`);
      setForm(r.data);
    } catch { Alert.alert('Error', 'Failed to fetch'); }
    finally { setLoading(false); }
  };

  const save = async () => {
    try {
      setSaving(true);
      if (id) await api.patch(`/${resourceName}/${id}`, form);
      else await api.post(`/${resourceName}`, form);
      navigation.goBack();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || 'Failed to save');
    } finally { setSaving(false); }
  };

  const fields = (metadata?.fields || []).filter((f: any) => !f.form_hidden && f.name !== 'id');
  const prefix = (resourceName.split('/').pop() || 'ARC').toUpperCase().slice(0, 3);
  const code = form.code || form.number || id || 'new';
  const status = form.status || form.state || 'in_review';
  const kind = (metadata?.label || resourceTitle || 'CHANGE').toUpperCase();
  const ownerInit = (form.owner_name || form.owner || 'NA').toString().slice(0, 2).toUpperCase();
  const titleVal = form[metadata?.primary_field || 'name'] || form.name || '';

  const summary = form.description || form.summary || '';
  const metaPairs = fields
    .filter((f: any) => !['name', 'title', 'description', 'summary'].includes(f.name))
    .slice(0, 4)
    .map((f: any) => ({ label: (f.label || f.name).toUpperCase(), value: form[f.name] }));

  const right = (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
      <Share2 size={16} color={C.text3} />
      <MoreHorizontal size={18} color={C.text3} />
    </View>
  );

  if (loading) return <MobileShell active="items" headerRight={right}><View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View></MobileShell>;

  return (
    <MobileShell
      active="items"
      headerRight={right}
      onTabPress={(t) => { if (t === 'home') navigation.navigate('AppHome'); }}
    >
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 130 }}>
        {/* Header card */}
        <View style={s.headerCard}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <View style={s.kindChip}><Text style={s.kindText}>{`${kind} · ECO`}</Text></View>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
              <StatusGlyph value={status} />
              <Text style={s.statusLabel}>{String(status).replace(/_/g, ' ')}</Text>
            </View>
          </View>
          <View style={{ marginTop: 12 }}>
            <MonoId prefix={prefix} code={code} />
            <Text style={s.h1}>{titleVal || (id ? `Edit ${resourceTitle}` : `New ${resourceTitle}`)}</Text>
          </View>
          <View style={s.metaStrip}>
            <Avatar initials={ownerInit} size={20} />
            <Text style={s.metaText}>{form.owner_name || form.owner || 'Nadia W.'}</Text>
            <Text style={s.metaSep}>·</Text>
            <Text style={s.metaText}>Severity</Text>
            <Text style={[s.metaText, { color: theme.arc.warn }]}>● High</Text>
            <Text style={s.metaSep}>·</Text>
            <Text style={s.metaText}>+$0.42/u</Text>
          </View>
        </View>

        {/* Tabs */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.tabs}>
          {TABS.map((t) => {
            const active = t === tab;
            return (
              <TouchableOpacity key={t} onPress={() => setTab(t)} activeOpacity={0.7} style={s.tabBtn}>
                <Text style={[s.tabText, active && s.tabTextActive]}>{t}</Text>
                {active && <View style={s.tabUnderline} />}
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {tab === 'Overview' && (
          <View style={{ marginTop: 14, gap: 18 }}>
            <View>
              <Text style={s.sectLabel}>SUMMARY</Text>
              {!id ? (
                <TextInput
                  multiline
                  placeholder="Summary"
                  placeholderTextColor={C.text3}
                  value={summary}
                  onChangeText={(v) => setForm({ ...form, description: v })}
                  style={[s.input, { minHeight: 80, textAlignVertical: 'top' }]}
                />
              ) : (
                <Text style={s.body}>{summary || '—'}</Text>
              )}
            </View>

            <View style={s.metaGrid}>
              {metaPairs.map((m: any, idx: number) => (
                <View key={idx} style={s.metaCell}>
                  <Text style={s.metaCellLabel}>{m.label}</Text>
                  {!id ? (
                    <TextInput
                      value={m.value != null ? String(m.value) : ''}
                      onChangeText={(v) => setForm({ ...form, [fields.find((f: any) => (f.label || f.name).toUpperCase() === m.label)?.name || '']: v })}
                      placeholder="—"
                      placeholderTextColor={C.text3}
                      style={s.input}
                    />
                  ) : (
                    <Text style={s.metaCellValue}>{m.value != null && String(m.value) ? String(m.value) : '—'}</Text>
                  )}
                </View>
              ))}
            </View>

            {/* Lifecycle */}
            <View>
              <Text style={s.sectLabel}>LIFECYCLE</Text>
              <View style={s.lifeRow}>
                {LIFECYCLE.map((stage, i) => {
                  const active = i === 1;
                  const done = i < 1;
                  return (
                    <View key={stage} style={{ flex: 1, alignItems: 'center', gap: 4 }}>
                      <View style={[s.lifeDot, active && s.lifeDotActive, done && s.lifeDotDone]}>
                        {done && <Check size={9} color={C.bg} strokeWidth={3} />}
                      </View>
                      <Text style={[s.lifeText, active && { color: theme.arc.accent, fontWeight: '700' }]}>{stage}</Text>
                    </View>
                  );
                })}
              </View>
            </View>

            {/* Affected */}
            <View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <ChevronRight size={14} color={C.text3} />
                <Text style={[s.sectLabel, { marginBottom: 0 }]}>AFFECTED ITEMS</Text>
                <View style={{ flex: 1 }} />
                <Text style={{ color: C.text3, fontSize: 11 }}>3</Text>
              </View>
              <View style={[s.row, { marginTop: 10 }]}>
                <StatusGlyph value="in_progress" />
                <MonoId prefix="ARC" code="PRT-04786" />
                <View style={{ flex: 1 }} />
                <Avatar initials="NW" size={20} />
              </View>
            </View>
          </View>
        )}
      </ScrollView>

      {/* Sticky action bar */}
      <View style={s.actionBar}>
        <TouchableOpacity style={s.btnGhost} onPress={() => navigation.goBack()} activeOpacity={0.8}>
          <Text style={s.btnGhostText}>{id ? 'Defer' : 'Cancel'}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.btnPrimary} onPress={save} disabled={saving} activeOpacity={0.85}>
          {saving ? <ActivityIndicator color={theme.arc.accentInk} /> : (
            <>
              <Check size={15} color={theme.arc.accentInk} />
              <Text style={s.btnPrimaryText}>{id ? 'Approve' : 'Create'}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    </MobileShell>
  );
};

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  headerCard: { padding: 14, borderRadius: 14, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface },
  kindChip: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 4, borderWidth: 1, borderColor: C.line2 },
  kindText: { color: C.text2, fontSize: 10, fontWeight: '700', letterSpacing: 0.6, fontFamily: 'Menlo' },
  statusLabel: { color: C.text2, fontSize: 11.5, textTransform: 'capitalize' },
  h1: { color: C.text, fontSize: 20, fontWeight: '700', letterSpacing: -0.3, marginTop: 6 },
  metaStrip: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 14, flexWrap: 'wrap' },
  metaText: { color: C.text3, fontSize: 11.5 },
  metaSep: { color: C.line2, fontSize: 11 },
  tabs: { gap: 18, paddingVertical: 14 },
  tabBtn: { paddingBottom: 6 },
  tabText: { color: C.text3, fontSize: 13, fontWeight: '500' },
  tabTextActive: { color: C.text, fontWeight: '700' },
  tabUnderline: { height: 2, backgroundColor: theme.arc.accent, marginTop: 4, borderRadius: 2 },
  sectLabel: { color: C.text3, fontSize: 10, fontWeight: '700', letterSpacing: 1.2, marginBottom: 8, fontFamily: 'Menlo' },
  body: { color: C.text2, fontSize: 13.5, lineHeight: 20 },
  input: { borderWidth: 1, borderColor: C.line, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, color: C.text, backgroundColor: C.surface, fontFamily: 'PlusJakartaSans_400Regular', fontSize: 13.5 },
  metaGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 14 },
  metaCell: { width: '47%' },
  metaCellLabel: { color: C.text3, fontSize: 10, fontWeight: '700', letterSpacing: 1, fontFamily: 'Menlo', marginBottom: 4 },
  metaCellValue: { color: C.text, fontSize: 13.5, fontWeight: '500' },
  lifeRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 6, paddingHorizontal: 8, borderRadius: 12, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface },
  lifeDot: { width: 14, height: 14, borderRadius: 7, borderWidth: 1.5, borderColor: C.line2, alignItems: 'center', justifyContent: 'center' },
  lifeDotActive: { borderColor: theme.arc.accent, backgroundColor: 'rgba(232,155,108,0.18)' },
  lifeDotDone: { borderColor: theme.arc.accent, backgroundColor: theme.arc.accent },
  lifeText: { color: C.text3, fontSize: 11 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface },
  actionBar: { position: 'absolute', left: 12, right: 12, bottom: 80, flexDirection: 'row', gap: 8 },
  btnGhost: { flex: 1, height: 44, borderRadius: 12, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface, alignItems: 'center', justifyContent: 'center' },
  btnGhostText: { color: C.text, fontSize: 14, fontWeight: '600' },
  btnPrimary: { flex: 1.4, height: 44, borderRadius: 12, backgroundColor: theme.arc.accent, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 6 },
  btnPrimaryText: { color: theme.arc.accentInk, fontSize: 14, fontWeight: '700' },
});
