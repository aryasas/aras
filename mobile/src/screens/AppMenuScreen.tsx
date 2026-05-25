import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';
import * as LucideIcons from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';
import { Card } from '../components/Card';
import { ChevronRight, ChevronLeft } from 'lucide-react-native';

const resolveIcon = (name: string) => {
  const Icon = (LucideIcons as any)[name] || LucideIcons.Package;
  return Icon;
};

export const AppMenuScreen = ({ route, navigation }: any) => {
  const { appName, appLabel } = route.params;
  const [menu, setMenu] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMenu();
  }, [appName]);

  const fetchMenu = async () => {
    try {
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
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <ChevronLeft size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <View>
          <Text style={styles.title}>{appLabel}</Text>
          <Text style={styles.subtitle}>Select a module</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {menu?.menu?.map((group: any, idx: number) => (
          <View key={idx} style={styles.group}>
            <Text style={styles.groupTitle}>{group.label.toUpperCase()}</Text>
            <Card variant="outline" style={styles.menuCard}>
              {group.items?.map((item: any, itemIdx: number) => {
                const Icon = resolveIcon(item.icon);
                return (
                  <TouchableOpacity
                    key={itemIdx}
                    style={[styles.menuItem, itemIdx !== group.items.length - 1 && styles.itemBorder]}
                    onPress={() => navigation.navigate('ResourceList', { 
                      resourceName: item.name, 
                      resourceTitle: item.label 
                    })}
                  >
                    <View style={styles.itemLeft}>
                      <View style={[styles.iconBox, { backgroundColor: theme.colors.background }]}>
                        <Icon size={18} color={theme.colors.primary} />
                      </View>
                      <Text style={styles.itemLabel}>{item.label}</Text>
                    </View>
                    <ChevronRight size={18} color={theme.colors.textSecondary} />
                  </TouchableOpacity>
                );
              })}
            </Card>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.lg,
    paddingTop: theme.spacing.xl,
  },
  backButton: {
    marginRight: theme.spacing.md,
    padding: theme.spacing.xs,
  },
  title: {
    ...theme.typography.h2,
    color: theme.colors.text,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: theme.spacing.lg,
  },
  group: {
    marginBottom: theme.spacing.xl,
  },
  groupTitle: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginBottom: theme.spacing.sm,
    marginLeft: theme.spacing.xs,
    letterSpacing: 1,
    fontWeight: '800',
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: theme.spacing.md,
  },
  itemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  itemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: theme.borderRadius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: theme.spacing.md,
  },
  itemLabel: {
    ...theme.typography.subtitle,
    color: theme.colors.text,
  },
});
