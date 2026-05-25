import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, SafeAreaView, ActivityIndicator } from 'react-native';
import * as LucideIcons from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';
import { Card } from '../components/Card';

const resolveIcon = (name: string) => {
  const Icon = (LucideIcons as any)[name] || LucideIcons.Package;
  return Icon;
};

export const AppHomeScreen = ({ navigation }: any) => {
  const [apps, setApps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApps();
  }, []);

  const fetchApps = async () => {
    try {
      const response = await api.get('/sidebar');
      setApps(response.data.filter((item: any) => item.type === 'app'));
    } catch (err) {
      console.error('Failed to fetch apps', err);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: any }) => {
    const Icon = resolveIcon(item.icon);
    return (
      <TouchableOpacity 
        style={styles.appCardContainer}
        onPress={() => navigation.navigate('AppMenu', { appName: item.name, appLabel: item.label })}
      >
        <Card style={styles.appCard} variant="elevated">
          <View style={[styles.iconContainer, { backgroundColor: theme.colors.primary + '10' }]}>
            <Icon size={32} color={theme.colors.primary} />
          </View>
          <Text style={styles.appLabel}>{item.label}</Text>
          <Text style={styles.appDescription}>{item.sub_apps?.length || 0} Modules</Text>
        </Card>
      </TouchableOpacity>
    );
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
        <Text style={styles.title}>Applications</Text>
        <Text style={styles.subtitle}>Select an app to continue</Text>
      </View>
      <FlatList
        data={apps}
        renderItem={renderItem}
        keyExtractor={(item) => item.name}
        numColumns={2}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    padding: theme.spacing.lg,
    paddingTop: theme.spacing.xl,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: theme.spacing.md,
  },
  appCardContainer: {
    width: '50%',
    padding: theme.spacing.sm,
  },
  appCard: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.xl,
    height: 160,
  },
  iconContainer: {
    padding: theme.spacing.md,
    borderRadius: theme.borderRadius.lg,
    marginBottom: theme.spacing.md,
  },
  appLabel: {
    ...theme.typography.subtitle,
    color: theme.colors.text,
    textAlign: 'center',
  },
  appDescription: {
    ...theme.typography.caption,
    color: theme.colors.textSecondary,
    marginTop: 4,
  },
});
