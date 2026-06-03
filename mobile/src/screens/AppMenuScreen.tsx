// claude-sonnet-4-6
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import * as LucideIcons from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';
import { ChevronRight } from 'lucide-react-native';
import { MobileShell } from '../components/MobileShell';
import { haptic } from '../lib/haptics';

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

// claude-sonnet-4-6
const resolveIcon = (name: string) => {
  const Icon = (LucideIcons as any)[name] || LucideIcons.Package;
  return Icon;
};

// claude-sonnet-4-6
export const AppMenuScreen = ({ route, navigation }: any) => {
  const { appName, appLabel } = route.params;
  const [menu, setMenu] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // claude-sonnet-4-6
  useEffect(() => {
    fetchMenu();
  }, [appName]);

  // claude-sonnet-4-6
  const fetchMenu = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/app-menu/${appName}`);
      setMenu(response.data);
    } catch (err) {
      console.error('Failed to fetch menu', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <MobileShell active="items" title={appLabel} navigation={navigation}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.loadingCard}>
            {[...Array(4)].map((_, index) => (
              <SkeletonRow key={index} />
            ))}
          </View>
        </ScrollView>
      </MobileShell>
    );
  }

  return (
    <MobileShell active="items" title={appLabel} navigation={navigation}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Direct menu items — handle both grouped and flat shapes */}
        {(() => {
          const entries: any[] = menu?.menu || [];
          const groups: Array<{ label: string; items: any[] }> = [];

          // Partition: group entries have `items[]`, flat entries have `name` directly
          const flatItems: any[] = [];
          for (const entry of entries) {
            if (entry.type === 'group' || Array.isArray(entry.items)) {
              groups.push(entry);
            } else {
              flatItems.push(entry);
            }
          }
          if (flatItems.length > 0) groups.push({ label: appLabel, items: flatItems });

          return groups.map((group, idx) => (
            <View key={idx} style={styles.group}>
              <Text style={styles.groupTitle}>{(group.label || '').toUpperCase()}</Text>
              <View style={styles.menuCard}>
                {(group.items || []).map((item: any, itemIdx: number) => {
                  const Icon = resolveIcon(item.icon);
                  return (
                    <TouchableOpacity
                      key={itemIdx}
                      style={[
                        styles.menuItem,
                        itemIdx !== group.items.length - 1 && styles.itemBorder,
                        item.type === 'link' && styles.menuItemHighlight,
                      ]}
                      onPress={() => {
                        haptic.light();
                        if (item.type === 'link' || (item.path && item.path.includes('/pos'))) {
                          if (item.path && item.path.includes('/pos')) {
                            navigation.navigate('Pos', { sessionId: null, sessionMode: 'sales', sessionLabel: item.label || 'POS' });
                            return;
                          }
                        }
                        navigation.navigate('ResourceList', {
                          resourceName: item.name,
                          resourceTitle: item.label
                        });
                      }}
                    >
                      <View style={styles.itemLeft}>
                        <View style={[styles.iconBox, item.type === 'link' && styles.iconBoxHighlight]}>
                          <Icon size={18} color={item.type === 'link' ? theme.arc.accentInk : theme.arc.accent} />
                        </View>
                        <Text style={[styles.itemLabel, item.type === 'link' && styles.itemLabelHighlight]}>{item.label}</Text>
                      </View>
                      <ChevronRight size={18} color={item.type === 'link' ? theme.arc.accent : C.text3} />
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>
          ));
        })()}

        {/* Sub-apps (e.g. party, notes, web under a parent) */}
        {menu?.sub_apps?.length > 0 && (
          <View style={styles.group}>
            <Text style={styles.groupTitle}>MODULES</Text>
            <View style={styles.menuCard}>
              {menu.sub_apps.map((sub: any, idx: number) => {
                const Icon = resolveIcon(sub.icon);
                return (
                  <TouchableOpacity
                    key={sub.name}
                    style={[styles.menuItem, idx !== menu.sub_apps.length - 1 && styles.itemBorder]}
                    onPress={() => {
                      haptic.light();
                      navigation.navigate('AppMenu', {
                        appName: sub.name,
                        appLabel: sub.label
                      });
                    }}
                  >
                    <View style={styles.itemLeft}>
                      <View style={styles.iconBox}>
                        <Icon size={18} color={theme.arc.accent} />
                      </View>
                      <Text style={styles.itemLabel}>{sub.label}</Text>
                    </View>
                    <ChevronRight size={18} color={C.text3} />
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        )}
      </ScrollView>
    </MobileShell>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: 16,
    paddingBottom: 110,
  },
  loadingCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 12,
    overflow: 'hidden',
  },
  group: {
    marginBottom: 22,
  },
  groupTitle: {
    color: C.text3,
    marginBottom: 8,
    marginLeft: 4,
    letterSpacing: 1.2,
    fontSize: 11,
    fontWeight: '700',
    fontFamily: 'Menlo',
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 12,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  itemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  itemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    backgroundColor: C.surface2,
  },
  itemLabel: {
    color: C.text,
    fontSize: 14.5,
    fontWeight: '700',
  },
  itemLabelHighlight: {
    color: theme.arc.accent,
  },
  menuItemHighlight: {
    backgroundColor: 'rgba(232,155,108,0.07)',
  },
  iconBoxHighlight: {
    backgroundColor: theme.arc.accent,
  },
});
