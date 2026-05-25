// claude-opus-4-7
// ARC mobile home: greeting + stat tiles + Awaiting you + Pinned strip.
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Bell, ChevronRight } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { MobileShell, MonoId, Avatar, StatusGlyph } from '../components/MobileShell';
import api from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';

const C = theme.arc.dark;

const STATS = [
  { label: 'In your inbox', value: '5', sub: '+2 today', highlight: true },
  { label: 'Changes you own', value: '12', sub: '4 awaiting' },
  { label: 'Items released wk', value: '23', sub: '+11 vs. last' },
  { label: 'Build readiness', value: '94%', sub: 'M4 program', accent: true },
];

const AWAITING = [
  { tag: 'CHANGE', code: 'ECO-00471', title: 'Approve material swap — bracket L', avatar: 'NW', ago: '11m' },
  { tag: 'REVIEW', code: 'ASM-00214', title: 'Engineering review — M4 transmission', avatar: 'AS', ago: '2h' },
  { tag: 'SIGN',   code: 'DOC-09812', title: 'Sign-off supplier qual report', avatar: 'LP', ago: '3h' },
];

const PINNED = [
  { code: 'PRT-04812', status: 'in_progress' },
  { code: 'ASM-00214', status: 'in_review' },
];

export const AppHomeScreen = ({ navigation }: any) => {
  const { user } = useAuthStore();
  const [sidebar, setSidebar] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const firstName = (user?.full_name || user?.username || 'there').split(' ')[0];
  const initials = firstName.slice(0, 2).toUpperCase();

  useEffect(() => {
    api.get('/sidebar').then((r) => setSidebar(r.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const now = new Date();
  const dateLabel = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).toUpperCase().replace(',', ' ·');

  const right = (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
      <Bell size={17} color={C.text3} />
      <Avatar initials={initials} size={26} />
    </View>
  );

  if (loading) return <MobileShell active="home" title="Home" headerRight={right}><View style={s.centered}><ActivityIndicator color={theme.arc.accent} /></View></MobileShell>;

  return (
    <MobileShell
      active="home"
      title="Home"
      headerRight={right}
      onTabPress={(t) => handleTab(t, navigation, sidebar)}
    >
      <ScrollView contentContainerStyle={{ padding: 18, paddingBottom: 110 }} showsVerticalScrollIndicator={false}>
        <Text style={s.kicker}>{dateLabel}</Text>
        <Text style={s.h1}>Morning, {firstName}.</Text>
        <Text style={s.h1sub}>Five things need you.</Text>

        <View style={s.statGrid}>
          {STATS.map((st) => (
            <View key={st.label} style={[s.statCard, st.highlight && s.statCardHi]}>
              <Text style={s.statLabel}>{st.label}</Text>
              <Text style={[s.statValue, st.accent && { color: theme.arc.accent }]}>{st.value}</Text>
              <Text style={s.statSub}>{st.sub}</Text>
            </View>
          ))}
        </View>

        <View style={s.sectHead}>
          <Text style={s.sectNum}>01</Text>
          <Text style={s.sectTitle}>Awaiting you</Text>
          <View style={{ flex: 1 }} />
          <Text style={s.sectMeta}>5 · 2 high</Text>
        </View>

        <View style={{ gap: 8 }}>
          {AWAITING.map((it, idx) => (
            <TouchableOpacity key={it.code} style={[s.awCard, idx === 0 && s.awCardActive]} activeOpacity={0.8}>
              <Avatar initials={it.avatar} size={28} />
              <View style={{ flex: 1, gap: 4 }}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                  <View style={s.tag}><Text style={s.tagText}>{it.tag}</Text></View>
                  <MonoId code={it.code} />
                </View>
                <Text style={s.awTitle}>{it.title}</Text>
              </View>
              <Text style={s.awAgo}>{it.ago}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={s.seeAll} activeOpacity={0.7}>
          <Text style={s.seeAllText}>See all 5 · </Text>
          <ChevronRight size={14} color={C.text2} />
        </TouchableOpacity>

        <View style={s.sectHead}>
          <Text style={s.sectNum}>02</Text>
          <Text style={s.sectTitle}>Pinned</Text>
          <View style={{ flex: 1 }} />
          <Text style={s.sectMeta}>Swipe →</Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
          {PINNED.map((p) => (
            <View key={p.code} style={s.pinCard}>
              <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
                <MonoId code={p.code} />
                <StatusGlyph value={p.status} />
              </View>
            </View>
          ))}
        </ScrollView>
      </ScrollView>
    </MobileShell>
  );
};

function handleTab(tab: string, navigation: any, sidebar: any[]) {
  if (tab === 'home') return;
  if (tab === 'items') {
    const firstApp = sidebar.find((a) => a.type === 'app') || sidebar[0];
    if (firstApp) navigation.navigate('AppMenu', { appName: firstApp.name, appLabel: firstApp.label });
  }
}

const s = StyleSheet.create({
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  kicker: { fontFamily: 'Menlo', fontSize: 11, letterSpacing: 1.5, color: C.text3 },
  h1: { color: C.text, fontSize: 28, fontWeight: '700', letterSpacing: -0.4, marginTop: 6 },
  h1sub: { color: C.text3, fontSize: 22, fontWeight: '500', letterSpacing: -0.3, marginTop: 2, marginBottom: 18 },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 22 },
  statCard: { width: '48.5%', padding: 14, borderRadius: 14, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface, minHeight: 96 },
  statCardHi: { backgroundColor: 'rgba(232,155,108,0.10)', borderColor: 'rgba(232,155,108,0.35)' },
  statLabel: { color: C.text2, fontSize: 12.5, fontWeight: '500' },
  statValue: { color: C.text, fontSize: 28, fontWeight: '700', marginTop: 6, letterSpacing: -0.5 },
  statSub: { color: C.text3, fontSize: 11.5, marginTop: 4 },
  sectHead: { flexDirection: 'row', alignItems: 'baseline', gap: 8, marginTop: 10, marginBottom: 12 },
  sectNum: { fontFamily: 'Menlo', fontSize: 11, color: C.text3 },
  sectTitle: { color: C.text, fontSize: 16, fontWeight: '700' },
  sectMeta: { color: C.text3, fontSize: 11.5 },
  awCard: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 12, borderRadius: 12, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface },
  awCardActive: { borderLeftWidth: 2, borderLeftColor: theme.arc.accent, borderColor: 'rgba(232,155,108,0.45)' },
  tag: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, borderWidth: 1, borderColor: C.line2 },
  tagText: { color: C.text2, fontSize: 10, fontWeight: '700', letterSpacing: 0.6, fontFamily: 'Menlo' },
  awTitle: { color: C.text, fontSize: 14, fontWeight: '500' },
  awAgo: { color: C.text3, fontSize: 11, fontFamily: 'Menlo' },
  seeAll: { alignSelf: 'center', flexDirection: 'row', alignItems: 'center', marginTop: 14, marginBottom: 18 },
  seeAllText: { color: C.text2, fontSize: 13.5, fontWeight: '600' },
  pinCard: { width: 200, padding: 12, borderRadius: 12, borderWidth: 1, borderColor: C.line, backgroundColor: C.surface },
});
