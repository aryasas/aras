// claude-opus-4-7
// ARC mobile list: search pill + filter chips + grouped sections with status
// glyph + ARC mono-id rows.
import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, FlatList } from 'react-native';
import { Search, Filter, Plus, ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell, MonoId, Avatar, StatusGlyph } from '../components/MobileShell';
import api from '../lib/api';

const C = theme.arc.dark;

const FILTERS = ['Open', 'Mine', 'Parts', 'Changes', 'M4 program', 'Last 7d'];

export const ResourceListScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle } = route.params;
  const [data, setData] = useState<any[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; auth: boolean } | null>(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('Open');

  useEffect(() => { fetchAll(); }, [resourceName]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [m, d] = await Promise.all([api.get(`/metadata/${resourceName}`), api.get(`/${resourceName}`)]);
      setMetadata(m.data);
      setData(Array.isArray(d.data.items) ? d.data.items : Array.isArray(d.data) ? d.data : []);
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 401 || status === 403) {
        setError({ message: 'Your session does not have access to this resource. Sign in again or switch workspace.', auth: true });
      } else {
        setError({ message: e?.message || 'Unable to load records.', auth: false });
      }
    }
    finally { setLoading(false); }
  };

  const primary = metadata?.primary_field || 'name';
  const prefix = (resourceName.split('/').pop() || 'ARC').toUpperCase().slice(0, 3);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return data.filter((it) => !q || JSON.stringify(it).toLowerCase().includes(q));
  }, [data, search]);

  const groups = useMemo(() => {
    const map = new Map<string, any[]>();
    filtered.forEach((it) => {
      const k = String(it.status ?? it.state ?? 'all');
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(it);
    });
    return Array.from(map.entries()).map(([k, items]) => ({ key: k, label: k.replace(/_/g, ' ').toUpperCase(), items }));
  }, [filtered]);

  const right = (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
      <Filter size={17} color={C.text3} />
      <TouchableOpacity onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, metadata })}>
        <Plus size={19} color={C.text2} />
      </TouchableOpacity>
    </View>
  );

  const renderRow = (item: any) => {
    const rev = item.revision || item.rev;
    const ownerInit = (item.owner_name || item.owner || 'NA').slice(0, 2).toUpperCase();
    const cls = item.classification || item.category || metadata?.label || resourceTitle;
    const updated = item.updated_at ? formatAgo(item.updated_at) : '';
    return (
      <TouchableOpacity
        key={item.id}
        style={s.row}
        activeOpacity={0.7}
        onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, id: item.id, metadata })}
      >
        <View style={{ paddingTop: 3 }}><StatusGlyph value={item.status ?? item.state} /></View>
        <View style={{ flex: 1, gap: 4 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <MonoId prefix={prefix} code={item.code || item.number || item.id} />
            {rev && <Text style={s.rev}>rev {rev}</Text>}
          </View>
          <Text style={s.title} numberOfLines={1}>{item[primary] || item.name || `#${item.id}`}</Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
            <Avatar initials={ownerInit} size={18} />
            <Text style={s.meta}>{cls}{updated ? ` · ${updated}` : ''}</Text>
          </View>
        </View>
        <ChevronRight size={15} color={C.text3} />
      </TouchableOpacity>
    );
  };

  if (loading && !metadata) {
    return <MobileShell active="items" title="Items" headerRight={right}><View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View></MobileShell>;
  }

  if (error && (error.auth || !metadata)) {
    return (
      <MobileShell active="items" title={resourceTitle || 'Items'} headerRight={right} onTabPress={(t) => { if (t === 'home') navigation.navigate('AppHome'); }}>
        <View style={s.errorBox}>
          <Text style={s.errorTitle}>{error.auth ? 'Access denied' : 'Could not load records'}</Text>
          <Text style={s.errorText}>{error.message}</Text>
          <TouchableOpacity style={s.retryButton} onPress={fetchAll} activeOpacity={0.8}>
            <Text style={s.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </MobileShell>
    );
  }

  return (
    <MobileShell active="items" title={resourceTitle || 'Items'} headerRight={right} onTabPress={(t) => { if (t === 'home') navigation.navigate('AppHome'); }}>
      <View style={{ paddingHorizontal: 16, paddingTop: 4 }}>
        <View style={s.searchPill}>
          <Search size={14} color={C.text3} />
          <TextInput
            value={search}
            onChangeText={setSearch}
            placeholder="Find by ID, name, or owner"
            placeholderTextColor={C.text3}
            style={s.searchInput}
          />
          <View style={s.kbd}><Text style={s.kbdText}>⌘K</Text></View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}>
          {FILTERS.map((f) => {
            const active = f === filter;
            return (
              <TouchableOpacity key={f} onPress={() => setFilter(f)} activeOpacity={0.7} style={[s.chip, active && s.chipActive]}>
                <Text style={[s.chipText, active && s.chipTextActive]}>{f}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      <FlatList
        data={groups}
        keyExtractor={(g) => g.key}
        refreshing={loading}
        onRefresh={fetchAll}
        contentContainerStyle={{ paddingBottom: 110 }}
        ListHeaderComponent={error ? (
          <View style={s.inlineError}>
            <Text style={s.inlineErrorText}>{error.message}</Text>
          </View>
        ) : null}
        ListEmptyComponent={<View style={s.empty}><Text style={s.emptyText}>No records</Text></View>}
        renderItem={({ item: g }) => (
          <View>
            <View style={s.groupHead}>
              <StatusGlyph value={g.key} />
              <Text style={s.groupLabel}>{g.label}</Text>
              <Text style={s.groupCount}>· {g.items.length}</Text>
            </View>
            {g.items.map(renderRow)}
          </View>
        )}
      />
    </MobileShell>
  );
};

function formatAgo(iso: string): string {
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const m = Math.floor(diff / 60000);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const days = Math.floor(h / 24);
  return `${days}d`;
}

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  searchPill: { flexDirection: 'row', alignItems: 'center', gap: 8, height: 40, paddingHorizontal: 14, borderRadius: 999, backgroundColor: C.surface, borderWidth: 1, borderColor: C.line },
  searchInput: { flex: 1, color: C.text, fontSize: 13.5, padding: 0, fontFamily: 'PlusJakartaSans_400Regular' },
  kbd: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, backgroundColor: C.surface2, borderWidth: 1, borderColor: C.line },
  kbdText: { color: C.text3, fontSize: 10, fontFamily: 'Menlo', fontWeight: '700' },
  chips: { gap: 8, paddingVertical: 14 },
  chip: { height: 32, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1, borderColor: C.line, justifyContent: 'center' },
  chipActive: { borderColor: theme.arc.accent },
  chipText: { color: C.text3, fontSize: 12.5, fontWeight: '500' },
  chipTextActive: { color: theme.arc.accent, fontWeight: '700' },
  groupHead: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 16, paddingTop: 18, paddingBottom: 8, borderTopWidth: 1, borderTopColor: C.line, marginTop: 6 },
  groupLabel: { color: C.text3, fontSize: 11, fontWeight: '700', letterSpacing: 1.2, fontFamily: 'Menlo' },
  groupCount: { color: C.text3, fontSize: 11, fontFamily: 'Menlo' },
  row: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, paddingHorizontal: 16, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: C.line },
  title: { color: C.text, fontSize: 15.5, fontWeight: '600' },
  rev: { color: C.text3, fontSize: 11, fontFamily: 'Menlo' },
  meta: { color: C.text3, fontSize: 11.5 },
  empty: { padding: 40, alignItems: 'center' },
  emptyText: { color: C.text3, fontSize: 13 },
  errorBox: { margin: 16, padding: 18, borderRadius: 12, borderWidth: 1, borderColor: '#7f1d1d', backgroundColor: '#2a1214' },
  errorTitle: { color: '#fecaca', fontSize: 15, fontWeight: '700' },
  errorText: { color: C.text2, fontSize: 13, lineHeight: 19, marginTop: 8 },
  retryButton: { alignSelf: 'flex-start', height: 34, paddingHorizontal: 14, borderRadius: 8, backgroundColor: theme.arc.accent, justifyContent: 'center', marginTop: 14 },
  retryText: { color: theme.arc.accentInk, fontSize: 13, fontWeight: '700' },
  inlineError: { marginHorizontal: 16, marginTop: 12, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: '#7f1d1d', backgroundColor: '#2a1214' },
  inlineErrorText: { color: '#fecaca', fontSize: 12.5 },
});
