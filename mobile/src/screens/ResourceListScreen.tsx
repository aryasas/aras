// claude-opus-4-7
// ARC mobile resource list: dense rows with mono ID, primary "New" action LEFT.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, SafeAreaView, ActivityIndicator, TextInput } from 'react-native';
import { Search, Plus, ChevronLeft, ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';

const C = theme.arc.light;

export const ResourceListScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle } = route.params;
  const [data, setData] = useState<any[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => { fetchAll(); }, [resourceName]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const clean = resourceName.replace(/\//g, '_');
      const [m, d] = await Promise.all([api.get(`/metadata/${resourceName}`), api.get(`/${clean}`)]);
      setMetadata(m.data);
      setData(Array.isArray(d.data.items) ? d.data.items : Array.isArray(d.data) ? d.data : []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const primary = metadata?.primary_field || 'name';

  const renderItem = ({ item }: { item: any }) => {
    const title = item[primary] || item.name || item.id;
    return (
      <TouchableOpacity
        style={s.row}
        activeOpacity={0.7}
        onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, id: item.id, metadata })}
      >
        <View style={{ flex: 1 }}>
          <Text style={s.title}>{title}</Text>
          <Text style={s.id}>#{item.id}</Text>
        </View>
        <ChevronRight size={14} color={C.text3} />
      </TouchableOpacity>
    );
  };

  const filtered = data.filter((it) => JSON.stringify(it).toLowerCase().includes(search.toLowerCase()));

  if (loading && \!metadata) return <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>;

  return (
    <SafeAreaView style={s.root}>
      <View style={s.header}>
        <View style={s.headerTop}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={s.iconBtn}>
            <ChevronLeft size={20} color={C.text} />
          </TouchableOpacity>
          <View style={{ flex: 1 }}>
            <Text style={s.idTop}><Text style={s.idBold}>res</Text>/{resourceName}</Text>
            <Text style={s.h1}>{resourceTitle}</Text>
          </View>
        </View>

        <View style={s.actionBar}>
          <TouchableOpacity
            style={s.btnPrimary}
            activeOpacity={0.85}
            onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, metadata })}
          >
            <Plus size={14} color={theme.arc.accentInk} />
            <Text style={s.btnPrimaryText}>New</Text>
          </TouchableOpacity>
          <View style={s.searchWrap}>
            <Search size={14} color={C.text3} />
            <TextInput
              style={s.searchInput}
              placeholder="Search"
              placeholderTextColor={C.text3}
              value={search}
              onChangeText={setSearch}
            />
          </View>
        </View>
      </View>

      <FlatList
        data={filtered}
        keyExtractor={(i) => String(i.id)}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={s.sep} />}
        refreshing={loading}
        onRefresh={fetchAll}
        ListEmptyComponent={<View style={s.empty}><Text style={s.emptyText}>No records</Text></View>}
        contentContainerStyle={{ paddingBottom: 24 }}
      />
    </SafeAreaView>
  );
};

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  header: { padding: 14, paddingTop: 20, backgroundColor: C.surface, borderBottomWidth: 1, borderBottomColor: C.line },
  headerTop: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  iconBtn: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 8 },
  idTop: { fontFamily: 'Menlo', fontSize: 11, color: C.text3 },
  idBold: { color: C.text, fontWeight: '700' },
  h1: { ...theme.typography.h3, color: C.text, marginTop: 2 },
  actionBar: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12 },
  btnPrimary: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 32, paddingHorizontal: 12, borderRadius: 8, backgroundColor: theme.arc.accent },
  btnPrimaryText: { color: theme.arc.accentInk, fontSize: 13, fontWeight: '600' },
  searchWrap: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6, height: 32, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1, borderColor: C.line, backgroundColor: C.bg },
  searchInput: { flex: 1, color: C.text, fontSize: 13, padding: 0, fontFamily: 'PlusJakartaSans_400Regular' },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 18, paddingVertical: 12, backgroundColor: C.surface },
  title: { ...theme.typography.bodyStrong, color: C.text },
  id: { fontFamily: 'Menlo', fontSize: 11, color: C.text3, marginTop: 2 },
  sep: { height: 1, backgroundColor: C.line, marginLeft: 18 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: C.bg },
  empty: { padding: 40, alignItems: 'center' },
  emptyText: { color: C.text3, fontSize: 13 },
});
