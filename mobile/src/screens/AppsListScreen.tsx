// claude-sonnet-4-6
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl,
} from 'react-native';
import * as LucideIcons from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell } from '../components/MobileShell';
import api from '../lib/api';

const C = theme.arc.dark;

const resolveIcon = (name: string) => {
  if (!name) return LucideIcons.Package;
  const normalized = name.charAt(0).toUpperCase() + name.slice(1);
  return (LucideIcons as any)[normalized] || LucideIcons.Package;
};

export const AppsListScreen = ({ navigation }: any) => {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchApps = useCallback(async () => {
    try {
      const r = await api.get('/sidebar');
      setApps((r.data as any[]).filter((item: any) => item.type === 'app'));
    } catch (e) {
      console.error('Failed to fetch apps', e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchApps(); }, [fetchApps]);

  const onRefresh = () => { setRefreshing(true); fetchApps(); };

  const openApp = (app: any) => {
    navigation.navigate('AppMenu', { appName: app.name, appLabel: app.label });
  };

  if (loading) {
    return (
      <MobileShell active="items" title="Apps" navigation={navigation}>
        <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>
      </MobileShell>
    );
  }

  // Separate root apps from sub-apps, group by parent
  const rootApps = apps.filter((a) => !a.parent_name);
  const subAppsByParent: Record<string, any[]> = {};
  apps.filter((a) => a.parent_name).forEach((a) => {
    if (!subAppsByParent[a.parent_name]) subAppsByParent[a.parent_name] = [];
    subAppsByParent[a.parent_name].push(a);
  });

  return (
    <MobileShell active="items" title="Apps" navigation={navigation}>
      <ScrollView
        contentContainerStyle={s.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.arc.accent} />}
      >
        <Text style={s.heading}>All Applications</Text>
        <View style={s.grid}>
          {rootApps.map((app) => {
            const Icon = resolveIcon(app.icon);
            const subs = subAppsByParent[app.name] || [];
            return (
              <TouchableOpacity
                key={app.name}
                style={s.card}
                activeOpacity={0.75}
                onPress={() => openApp(app)}
              >
                <View style={s.iconWrap}>
                  <Icon size={22} color={theme.arc.accent} strokeWidth={1.8} />
                </View>
                <Text style={s.cardLabel} numberOfLines={2}>{app.label}</Text>
                {subs.length > 0 && (
                  <Text style={s.subCount}>{subs.length} module{subs.length > 1 ? 's' : ''}</Text>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>
    </MobileShell>
  );
};

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 18, paddingBottom: 110 },
  heading: { color: C.text, fontSize: 22, fontWeight: '700', letterSpacing: -0.3, marginBottom: 16 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  card: {
    width: '47%',
    backgroundColor: C.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: C.line,
    padding: 16,
    minHeight: 110,
    justifyContent: 'space-between',
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: 'rgba(232,155,108,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  cardLabel: { color: C.text, fontSize: 14, fontWeight: '600', flex: 1 },
  subCount: { color: C.text3, fontSize: 11, fontFamily: 'Menlo', marginTop: 6 },
});
