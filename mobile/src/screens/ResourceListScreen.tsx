// claude-sonnet-4-6
// ARC mobile list: search pill + filter chips + grouped sections with status
// glyph + ARC mono-id rows.
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, TouchableOpacity, ActivityIndicator, FlatList } from 'react-native';
import { Search, Filter, Plus, ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell, MonoId, Avatar, StatusGlyph } from '../components/MobileShell';
import api from '../lib/api';
import { OfflineBanner } from '../components/OfflineBanner';

const C = theme.arc.dark;

// claude-sonnet-4-6
const SkeletonRow = () => (
  <View style={{ flexDirection: 'row', gap: 12, padding: 16, borderBottomWidth: 1, borderBottomColor: C.line }}>
    <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: C.surface2, marginTop: 4 }} />
    <View style={{ flex: 1, gap: 8 }}>
      <View style={{ height: 11, width: '40%', borderRadius: 4, backgroundColor: C.surface2 }} />
      <View style={{ height: 15, width: '75%', borderRadius: 4, backgroundColor: C.surface2 }} />
      <View style={{ height: 11, width: '55%', borderRadius: 4, backgroundColor: C.surface2 }} />
    </View>
  </View>
);

type FilterChip = {
  field: string;
  value: any;
  label: any;
};

// claude-sonnet-4-6
export const ResourceListScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle } = route.params;
  const [data, setData] = useState<any[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ message: string; auth: boolean; offline?: boolean } | null>(null);
  const [search, setSearch] = useState('');
  const [searchDebounce, setSearchDebounce] = useState('');
  const [filter, setFilter] = useState<{ field: string; value: any } | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const didMountFilterRef = useRef(false);
  const didMountSearchRef = useRef(false);

  // claude-sonnet-4-6
  useEffect(() => {
    fetchPage(1, true, filter);
  }, [resourceName]);

  // claude-sonnet-4-6
  useEffect(() => {
    if (!didMountFilterRef.current) {
      didMountFilterRef.current = true;
      return;
    }

    setPage(1);
    setHasMore(true);
    setData([]);
    fetchPage(1, true, filter);
  }, [filter]);

  // claude-sonnet-4-6
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchDebounce(search);
    }, 400);

    return () => clearTimeout(timer);
  }, [search]);

  // claude-sonnet-4-6
  useEffect(() => {
    if (!didMountSearchRef.current) {
      didMountSearchRef.current = true;
      return;
    }

    setPage(1);
    setHasMore(true);
    setData([]);
    fetchPage(1, true, filter);
  }, [searchDebounce]);

  // claude-sonnet-4-6
  const fetchPage = async (targetPage = 1, replace = targetPage === 1, activeFilter: { field: string; value: any } | null = null) => {
    try {
      setLoading(true);
      setError(null);
      const filtersParam = activeFilter
        ? `&filters=${encodeURIComponent(JSON.stringify([{ field: activeFilter.field, op: '=', value: activeFilter.value }]))}`
        : '';
      const searchParam = searchDebounce ? `&search=${encodeURIComponent(searchDebounce)}` : '';
      const [m, d] = await Promise.all([
        metadata && !replace ? Promise.resolve({ data: metadata }) : api.get(`/metadata/${resourceName}`),
        api.get(`/${resourceName}?page=${targetPage}&page_size=25${filtersParam}${searchParam}`),
      ]);
      const items = Array.isArray(d.data.items) ? d.data.items : [];
      setMetadata(m.data);
      setData((current) => replace ? items : [...current, ...items]);
      setPage(targetPage);
      setHasMore(items.length === 25);
    } catch (e: any) {
      const status = e?.response?.status;
      const isNetworkError = e?.code === 'ERR_NETWORK' || e?.message?.includes('Network Error');
      if (status === 401 || status === 403) {
        setError({ message: 'Your session does not have access to this resource. Sign in again or switch workspace.', auth: true });
      } else if (isNetworkError) {
        setError({ message: 'No internet connection. Pull down to retry.', auth: false, offline: true });
      } else {
        setError({ message: e?.message || 'Unable to load records.', auth: false });
      }
    } finally {
      setLoading(false);
    }
  };

  // claude-sonnet-4-6
  const refresh = () => {
    setPage(1);
    setHasMore(true);
    setData([]);
    fetchPage(1, true, filter);
  };

  // claude-sonnet-4-6
  const fetchMore = () => {
    if (hasMore && !loading) {
      fetchPage(page + 1, false, filter);
    }
  };

  const primary = metadata?.primary_field || 'name';
  const prefix = (resourceName.split('/').pop() || 'ARC').toUpperCase().slice(0, 3);
  const visibleData = data;

  const filterChips = useMemo<FilterChip[]>(() => {
    return (metadata?.fields || [])
      .filter((field: any) => Array.isArray(field.choices) && field.choices.length > 0)
      .flatMap((field: any) => field.choices.map((choice: any) => ({
        field: field.name,
        value: typeof choice === 'object' ? choice.value : choice,
        label: typeof choice === 'object' ? choice.label || choice.value : choice,
      })));
  }, [metadata]);

  const groups = useMemo(() => {
    const map = new Map<string, any[]>();
    visibleData.forEach((it) => {
      const k = String(it.status ?? it.state ?? 'all');
      if (!map.has(k)) map.set(k, []);
      map.get(k)!.push(it);
    });
    return Array.from(map.entries()).map(([k, items]) => ({ key: k, label: k.replace(/_/g, ' ').toUpperCase(), items }));
  }, [visibleData]);

  const right = (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
      <Filter size={17} color={C.text3} />
      <TouchableOpacity onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, metadata })}>
        <Plus size={19} color={C.text2} />
      </TouchableOpacity>
    </View>
  );

  // claude-sonnet-4-6
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

  if (loading && page === 1 && data.length === 0) {
    return (
      <MobileShell active="items" title={resourceTitle || 'Items'} headerRight={right} navigation={navigation}>
        <View style={s.skeletonWrap}>
          {[...Array(6)].map((_, i) => <SkeletonRow key={i} />)}
        </View>
      </MobileShell>
    );
  }

  if (error && (error.auth || (!error.offline && !metadata))) {
    return (
      <MobileShell active="items" title={resourceTitle || 'Items'} headerRight={right} navigation={navigation}>
        <View style={s.errorBox}>
          <Text style={s.errorTitle}>{error.auth ? 'Access denied' : 'Could not load records'}</Text>
          <Text style={s.errorText}>{error.message}</Text>
          <TouchableOpacity style={s.retryButton} onPress={refresh} activeOpacity={0.8}>
            <Text style={s.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </MobileShell>
    );
  }

  return (
    <MobileShell active="items" title={resourceTitle || 'Items'} headerRight={right} navigation={navigation}>
      <View style={{ paddingHorizontal: 16, paddingTop: 4 }}>
        <OfflineBanner visible={Boolean(error?.offline)} onRetry={refresh} />
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

        {filterChips.length > 0 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.chips}>
            {filterChips.map((f) => {
              const active = filter?.field === f.field && filter?.value === f.value;
              return (
                <TouchableOpacity
                  key={`${f.field}:${String(f.value)}`}
                  onPress={() => setFilter(active ? null : { field: f.field, value: f.value })}
                  activeOpacity={0.7}
                  style={[s.chip, active && s.chipActive]}
                >
                  <Text style={[s.chipText, active && s.chipTextActive]}>{String(f.label)}</Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        )}
      </View>

      <FlatList
        data={groups}
        keyExtractor={(g) => g.key}
        refreshing={loading}
        onRefresh={refresh}
        onEndReached={fetchMore}
        onEndReachedThreshold={0.3}
        contentContainerStyle={{ paddingBottom: 110 }}
        ListHeaderComponent={error && !error.offline ? (
          <View style={[s.inlineError, error.offline && s.inlineOfflineError]}>
            <Text style={s.inlineErrorText}>{error.message}</Text>
          </View>
        ) : null}
        ListEmptyComponent={(
          <View style={s.empty}>
            <Text style={s.emptyText}>No {resourceTitle || 'records'} yet</Text>
            <TouchableOpacity
              style={s.emptyButton}
              onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, metadata })}
              activeOpacity={0.85}
            >
              <Text style={s.emptyButtonText}>Create first {resourceTitle || 'record'}</Text>
            </TouchableOpacity>
          </View>
        )}
        ListFooterComponent={loading && page > 1 ? <ActivityIndicator color={theme.arc.accent} /> : null}
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

// claude-sonnet-4-6
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
  skeletonWrap: { paddingTop: 8 },
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
  emptyText: { color: C.text3, fontSize: 13, textAlign: 'center' },
  emptyButton: { height: 36, paddingHorizontal: 16, borderRadius: 8, backgroundColor: theme.arc.accent, justifyContent: 'center', marginTop: 16 },
  emptyButtonText: { color: theme.arc.accentInk, fontSize: 13, fontWeight: '700' },
  errorBox: { margin: 16, padding: 18, borderRadius: 12, borderWidth: 1, borderColor: '#7f1d1d', backgroundColor: '#2a1214' },
  errorTitle: { color: '#fecaca', fontSize: 15, fontWeight: '700' },
  errorText: { color: C.text2, fontSize: 13, lineHeight: 19, marginTop: 8 },
  retryButton: { alignSelf: 'flex-start', height: 34, paddingHorizontal: 14, borderRadius: 8, backgroundColor: theme.arc.accent, justifyContent: 'center', marginTop: 14 },
  retryText: { color: theme.arc.accentInk, fontSize: 13, fontWeight: '700' },
  inlineError: { marginHorizontal: 16, marginTop: 12, padding: 12, borderRadius: 10, borderWidth: 1, borderColor: '#7f1d1d', backgroundColor: '#2a1214' },
  inlineOfflineError: { borderColor: '#ca8a04', backgroundColor: '#1c1505' },
  inlineErrorText: { color: '#fecaca', fontSize: 12.5 },
});
