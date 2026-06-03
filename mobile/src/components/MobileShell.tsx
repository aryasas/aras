// claude-opus-4-7
// ARC mobile shell: top bar (ArcMark + centered title + headerRight) and
// floating 5-tab bottom bar with rounded glass surface.
import React, { ReactNode } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Home, Box, Inbox, MessageSquare, BarChart3 } from 'lucide-react-native';
import { theme } from '../lib/theme';

const C = theme.arc.dark;

export function ArcMark() {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
      <View
        style={{
          width: 18, height: 10, borderTopLeftRadius: 10, borderTopRightRadius: 10,
          borderWidth: 2, borderBottomWidth: 0, borderColor: theme.arc.accent,
        }}
      />
      <Text style={{ fontFamily: 'Menlo', fontSize: 13, fontWeight: '700', color: C.text, letterSpacing: 1 }}>ARC</Text>
    </View>
  );
}

interface ShellProps {
  active: 'home' | 'items' | 'inbox' | 'threads' | 'you';
  title?: string;
  headerRight?: ReactNode;
  hideTopBar?: boolean;
  onTabPress?: (tab: string) => void;
  navigation?: any;
  children: ReactNode;
}

const TABS = [
  { key: 'home', label: 'Home', Icon: Home },
  { key: 'items', label: 'Items', Icon: Box },
  { key: 'inbox', label: 'Inbox', Icon: Inbox },
  { key: 'threads', label: 'Threads', Icon: MessageSquare },
  { key: 'you', label: 'You', Icon: BarChart3 },
] as const;

const TAB_ROUTES: Partial<Record<string, string>> = {
  home: 'AppHome',
  items: 'AppsList',
  you: 'Settings',
};

export function MobileShell({ active, title, headerRight, hideTopBar, onTabPress, navigation, children }: ShellProps) {
  const handleTabPress = (key: string) => {
    if (onTabPress) { onTabPress(key); return; }
    if (!navigation || key === active) return;
    const route = TAB_ROUTES[key];
    if (route) navigation.navigate(route);
  };

  return (
    <SafeAreaView style={s.root}>
      <StatusBar barStyle="light-content" backgroundColor={C.bg} />
      {!hideTopBar && (
        <View style={s.topBar}>
          <View style={s.topSide}><ArcMark /></View>
          <Text style={s.topTitle} numberOfLines={1}>{title || ''}</Text>
          <View style={[s.topSide, { justifyContent: 'flex-end' }]}>{headerRight}</View>
        </View>
      )}
      <View style={s.body}>{children}</View>
      <View style={s.tabBarOuter} pointerEvents="box-none">
        <View style={s.tabBar}>
          {TABS.map(({ key, label, Icon }) => {
            const isActive = active === key;
            return (
              <TouchableOpacity
                key={key}
                style={s.tab}
                activeOpacity={0.7}
                onPress={() => handleTabPress(key)}
              >
                <View style={[s.tabIconWrap, isActive && s.tabIconWrapActive]}>
                  <Icon size={18} color={isActive ? C.text : C.text3} strokeWidth={isActive ? 2.2 : 1.7} />
                </View>
                <Text style={[s.tabLabel, isActive && s.tabLabelActive]}>{label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  topBar: { height: 44, paddingHorizontal: 16, flexDirection: 'row', alignItems: 'center', gap: 8 },
  topSide: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 },
  topTitle: { color: C.text2, fontSize: 14, fontWeight: '500', textAlign: 'center' },
  body: { flex: 1 },
  tabBarOuter: { position: 'absolute', left: 12, right: 12, bottom: 14, alignItems: 'center' },
  tabBar: {
    flexDirection: 'row',
    width: '100%',
    backgroundColor: 'rgba(22,27,35,0.82)',
    borderRadius: 24,
    paddingVertical: 8,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: C.line,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.35,
    shadowRadius: 24,
    elevation: 12,
  },
  tab: { flex: 1, alignItems: 'center', gap: 2, paddingVertical: 2 },
  tabIconWrap: { width: 38, height: 26, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  tabIconWrapActive: { backgroundColor: C.surface2, borderWidth: 1, borderColor: C.line2 },
  tabLabel: { fontSize: 10.5, color: C.text3, fontWeight: '500' },
  tabLabelActive: { color: C.text },
});

// ARC atoms (shared)
export function StatusGlyph({ value }: { value: any }) {
  const v = String(value || '').toLowerCase();
  let glyph = '○';
  let color: string = C.text3;
  if (/(in[_\s-]?progress|progress|active|working)/.test(v)) { glyph = '◐'; color = theme.arc.accent; }
  else if (/(review|pending|awaiting)/.test(v)) { glyph = '△'; color = theme.arc.warn; }
  else if (/(released|approved|done|complete)/.test(v)) { glyph = '●'; color = '#7CD27F'; }
  else if (/(blocked|cancel|reject|fail)/.test(v)) { glyph = '✕'; color = theme.arc.danger; }
  return <Text style={{ color, fontSize: 12, fontFamily: 'Menlo' }}>{glyph}</Text>;
}

export function MonoId({ prefix = 'ARC', code }: { prefix?: string; code: string | number }) {
  return (
    <Text style={{ fontFamily: 'Menlo', fontSize: 11.5 }}>
      <Text style={{ color: theme.arc.accent, fontWeight: '700' }}>{prefix}</Text>
      <Text style={{ color: C.text3 }}> · </Text>
      <Text style={{ color: C.text, fontWeight: '700' }}>{code}</Text>
    </Text>
  );
}

export function Avatar({ initials, size = 24, color }: { initials: string; size?: number; color?: string }) {
  const bg = color || theme.arc.accent;
  return (
    <View style={{
      width: size, height: size, borderRadius: size / 2,
      backgroundColor: 'rgba(232,155,108,0.18)',
      borderWidth: 1, borderColor: bg,
      alignItems: 'center', justifyContent: 'center',
    }}>
      <Text style={{ color: bg, fontSize: size * 0.4, fontWeight: '700', fontFamily: 'Menlo' }}>{initials}</Text>
    </View>
  );
}
