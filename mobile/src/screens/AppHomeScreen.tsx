// claude-opus-4-7
// ARC mobile app home: dense file-tree list of apps with mono IDs.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';
import * as LucideIcons from 'lucide-react-native';
import { ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';

const C = theme.arc.light;
const resolveIcon = (name: string) => (LucideIcons as any)[name] || LucideIcons.Package;

export const AppHomeScreen = ({ navigation }: any) => {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/sidebar')
      .then((r) => setApps(r.data.filter((i: any) => i.type === 'app')))
      .catch((e) => console.error('apps fetch', e))
      .finally(() => setLoading(false));
  }, []);

  const renderItem = ({ item }: { item: any }) => {
    const Icon = resolveIcon(item.icon);
    const count = item.sub_apps?.length || 0;
    return (
      <TouchableOpacity
        style={s.row}
        onPress={() => navigation.navigate('AppMenu', { appName: item.name, appLabel: item.label })}
        activeOpacity={0.7}
      >
        <View style={s.iconWrap}>
          <Icon size={16} color={theme.arc.accent} />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={s.label}>{item.label}</Text>
          <Text style={s.id}><Text style={s.idBold}>app</Text>/{item.name}</Text>
        </View>
        <Text style={s.count}>{count}</Text>
        <ChevronRight size={14} color={C.text3} />
      </TouchableOpacity>
    );
  };

  if (loading) return <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>;

  return (
    <SafeAreaView style={s.root}>
      <View style={s.header}>
        <Text style={s.idTop}><Text style={s.idBold}>arc</Text>/apps</Text>
        <Text style={s.title}>Applications</Text>
        <Text style={s.subtitle}>{apps.length} apps available</Text>
      </View>
      <FlatList
        data={apps}
        renderItem={renderItem}
        keyExtractor={(i) => i.name}
        ItemSeparatorComponent={() => <View style={s.sep} />}
        contentContainerStyle={{ paddingBottom: 24 }}
      />
    </SafeAreaView>
  );
};

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  header: { padding: 18, paddingTop: 24 },
  idTop: { fontFamily: 'Menlo', fontSize: 11, color: C.text3 },
  idBold: { color: C.text, fontWeight: '700' },
  title: { ...theme.typography.h1, color: C.text, marginTop: 4 },
  subtitle: { ...theme.typography.body, color: C.text2, marginTop: 2 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: C.bg },
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 18, paddingVertical: 12, backgroundColor: C.surface },
  iconWrap: { width: 32, height: 32, borderRadius: 8, alignItems: 'center', justifyContent: 'center', backgroundColor: C.bg2, borderWidth: 1, borderColor: C.line },
  label: { ...theme.typography.bodyStrong, color: C.text },
  id: { fontFamily: 'Menlo', fontSize: 11, color: C.text3, marginTop: 2 },
  count: { fontFamily: 'Menlo', fontSize: 11, color: C.text3, marginRight: 4 },
  sep: { height: 1, backgroundColor: C.line, marginLeft: 62 },
});
