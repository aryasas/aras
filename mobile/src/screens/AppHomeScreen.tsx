// claude-sonnet-4-6
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Linking } from 'react-native';
import { Bell, ChevronRight, Package } from 'lucide-react-native';
import * as LucideIcons from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell, Avatar } from '../components/MobileShell';
import { useAuthStore } from '../store/useAuthStore';
import api from '../lib/api';
import { getStoredValue } from '../lib/storage';
import { OfflineBanner } from '../components/OfflineBanner';

const C = theme.arc.dark;

// claude-sonnet-4-6
const resolveIcon = (name: string) => {
  if (!name) return LucideIcons.Package;
  const normalized = name.charAt(0).toUpperCase() + name.slice(1);
  return (LucideIcons as any)[normalized] || LucideIcons.Package;
};

// claude-sonnet-4-6
function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Morning';
  if (h < 17) return 'Afternoon';
  return 'Evening';
}

// claude-sonnet-4-6
export const AppHomeScreen = ({ navigation }: any) => {
  const { user } = useAuthStore();
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [workspaceUrl, setWorkspaceUrl] = useState('');
  const firstName = (user?.name || user?.username || 'there').split(' ')[0];
  const initials = firstName.slice(0, 2).toUpperCase();

  // claude-sonnet-4-6
  useEffect(() => { fetchDashboard(); }, []);

  // claude-sonnet-4-6
  useEffect(() => {
    let mounted = true;

    const loadWorkspaceUrl = async () => {
      const storedWorkspaceUrl = await getStoredValue('aras_workspace_url');
      if (mounted && storedWorkspaceUrl) {
        setWorkspaceUrl(storedWorkspaceUrl);
      }
    };

    loadWorkspaceUrl();

    return () => {
      mounted = false;
    };
  }, []);

  // claude-sonnet-4-6
  const fetchDashboard = async () => {
    try {
      setOffline(false);
      const [sidebarResponse] = await Promise.all([
        api.get('/sidebar'),
        api.get('/dashboard/summary').catch((error) => {
          if (error?.response?.status === 404) return null;
          throw error;
        }),
      ]);
      setApps((sidebarResponse.data as any[]).filter((item: any) => item.type === 'app'));
    } catch (error) {
      console.error('Failed to fetch dashboard data', error);
      if ((error as any)?.code === 'ERR_NETWORK' || (error as any)?.message?.includes('Network Error')) {
        setOffline(true);
        return;
      }
      setApps([]);
    } finally {
      setLoading(false);
    }
  };

  // claude-sonnet-4-6
  const openApp = (app: any) => {
    navigation.navigate('AppMenu', { appName: app.name, appLabel: app.label });
  };

  // claude-sonnet-4-6
  const openWebApp = async () => {
    await Linking.openURL(workspaceUrl || 'https://app.aras.id');
  };

  const now = new Date();
  const dateLabel = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).toUpperCase().replace(',', ' ·');
  const topApps = apps.slice(0, 4);
  const quickApps = apps.slice(0, 6);

  const right = (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
      <Bell size={17} color={C.text3} />
      <Avatar initials={initials} size={26} />
    </View>
  );

  if (loading) {
    return (
      <MobileShell active="home" title="Home" headerRight={right} navigation={navigation}>
        <View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View>
      </MobileShell>
    );
  }

  return (
    <MobileShell
      active="home"
      title="Home"
      headerRight={right}
      navigation={navigation}
    >
      <ScrollView contentContainerStyle={{ padding: 18, paddingBottom: 110 }} showsVerticalScrollIndicator={false}>
        <OfflineBanner visible={offline} onRetry={fetchDashboard} />
        <Text style={s.kicker}>{dateLabel}</Text>
        <Text style={s.h1}>{getGreeting()}, {firstName}.</Text>
        <Text style={s.h1sub}>{apps.length} apps available</Text>

        {apps.length === 0 ? (
          <View style={s.emptyState}>
            <Package size={40} color={C.text3} strokeWidth={1.2} />
            <Text style={s.emptyTitle}>No apps installed</Text>
            <Text style={s.emptyBody}>Contact your administrator to enable apps for your account.</Text>
            <TouchableOpacity style={s.webButton} activeOpacity={0.85} onPress={openWebApp}>
              <Text style={s.webButtonText}>Go to web app →</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {topApps.length > 0 && (
          <View style={s.appGrid}>
            {topApps.map((app) => {
              const Icon = resolveIcon(app.icon);
              return (
                <TouchableOpacity key={app.name} style={s.appTile} activeOpacity={0.75} onPress={() => openApp(app)}>
                  <View style={s.tileTop}>
                    <View style={s.iconWrap}>
                      <Icon size={20} color={theme.arc.accent} strokeWidth={1.8} />
                    </View>
                    <Text style={s.arrow}>-&gt;</Text>
                  </View>
                  <Text style={s.tileLabel} numberOfLines={2}>{app.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
            )}

            <View style={s.sectHead}>
              <Text style={s.sectNum}>01</Text>
              <Text style={s.sectTitle}>Quick Access</Text>
              <View style={{ flex: 1 }} />
              <Text style={s.sectMeta}>{quickApps.length}</Text>
            </View>

            <View style={s.quickCard}>
              {quickApps.length === 0 ? (
                <View style={s.emptyRow}>
                  <Text style={s.emptyText}>No apps available</Text>
                </View>
              ) : quickApps.map((app, idx) => {
                const Icon = resolveIcon(app.icon);
                return (
                  <TouchableOpacity
                    key={app.name}
                    style={[s.quickRow, idx !== quickApps.length - 1 && s.rowBorder]}
                    activeOpacity={0.75}
                    onPress={() => openApp(app)}
                  >
                    <View style={s.quickLeft}>
                      <View style={s.quickIconBox}>
                        <Icon size={18} color={theme.arc.accent} strokeWidth={1.8} />
                      </View>
                      <Text style={s.quickLabel} numberOfLines={1}>{app.label}</Text>
                    </View>
                    <ChevronRight size={18} color={C.text3} />
                  </TouchableOpacity>
                );
              })}
            </View>
          </>
        )}
      </ScrollView>
    </MobileShell>
  );
};

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  kicker: { fontFamily: 'Menlo', fontSize: 11, letterSpacing: 1.5, color: C.text3 },
  h1: { color: C.text, fontSize: 28, fontWeight: '700', letterSpacing: -0.4, marginTop: 6 },
  h1sub: { color: C.text3, fontSize: 22, fontWeight: '500', letterSpacing: -0.3, marginTop: 2, marginBottom: 18 },
  appGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 22 },
  appTile: {
    width: '48.5%',
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    minHeight: 110,
    justifyContent: 'space-between',
  },
  tileTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  iconWrap: {
    width: 38,
    height: 38,
    borderRadius: 8,
    backgroundColor: 'rgba(232,155,108,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrow: { color: theme.arc.accent, fontSize: 15, fontWeight: '700', fontFamily: 'Menlo' },
  tileLabel: { color: C.text, fontSize: 14, fontWeight: '700', marginTop: 12 },
  sectHead: { flexDirection: 'row', alignItems: 'baseline', gap: 8, marginTop: 10, marginBottom: 12 },
  sectNum: { fontFamily: 'Menlo', fontSize: 11, color: C.text3 },
  sectTitle: { color: C.text, fontSize: 16, fontWeight: '700' },
  sectMeta: { color: C.text3, fontSize: 11.5 },
  quickCard: { borderWidth: 1, borderColor: C.line, borderRadius: 8, backgroundColor: C.surface, overflow: 'hidden' },
  quickRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 14 },
  rowBorder: { borderBottomWidth: 1, borderBottomColor: C.line },
  quickLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  quickIconBox: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: C.surface2,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  quickLabel: { color: C.text, fontSize: 14.5, fontWeight: '700', flex: 1 },
  emptyRow: { padding: 16 },
  emptyText: { color: C.text3, fontSize: 13 },
  emptyState: { alignItems: 'center', padding: 40, gap: 12 },
  emptyTitle: { color: C.text, fontSize: 16, fontWeight: '700' },
  emptyBody: { color: C.text3, fontSize: 13, textAlign: 'center' },
  webButton: {
    height: 36,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  webButtonText: { color: C.text, fontSize: 13, fontWeight: '700' },
});
