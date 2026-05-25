import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, SafeAreaView, ActivityIndicator, TextInput } from 'react-native';
import { Search, Plus, ChevronLeft, MoreVertical } from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';
import { Card } from '../components/Card';
import { Button } from '../components/Button';

export const ResourceListScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle } = route.params;
  const [data, setData] = useState<any[]>([]);
  const [metadata, setMetadata] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchMetadataAndData();
  }, [resourceName]);

  const fetchMetadataAndData = async () => {
    try {
      setLoading(true);
      const cleanResource = resourceName.replace(/\//g, '_');
      const [metaRes, dataRes] = await Promise.all([
        api.get(`/metadata/${resourceName}`),
        api.get(`/${cleanResource}`)
      ]);
      setMetadata(metaRes.data);
      setData(Array.isArray(dataRes.data.items) ? dataRes.data.items : Array.isArray(dataRes.data) ? dataRes.data : []);
    } catch (err) {
      console.error('Failed to fetch resource data', err);
    } finally {
      setLoading(false);
    }
  };

  const getPrimaryField = () => {
    if (!metadata) return 'id';
    return metadata.primary_field || 'name';
  };

  const renderItem = ({ item }: { item: any }) => {
    const primaryField = getPrimaryField();
    const title = item[primaryField] || item.name || item.id;
    const subtitle = metadata?.fields?.find((f: any) => f.name !== primaryField && !f.form_hidden)?.name;

    return (
      <Card variant="outline" style={styles.itemCard}>
        <TouchableOpacity 
          style={styles.cardContent}
          onPress={() => navigation.navigate('ResourceForm', { 
            resourceName, 
            resourceTitle,
            id: item.id,
            metadata
          })}
        >
          <View style={styles.itemInfo}>
            <Text style={styles.itemTitle}>{title}</Text>
            {subtitle && item[subtitle] && (
              <Text style={styles.itemSubtitle}>{String(item[subtitle])}</Text>
            )}
            <Text style={styles.itemId}>#{item.id}</Text>
          </View>
          <MoreVertical size={20} color={theme.colors.textSecondary} />
        </TouchableOpacity>
      </Card>
    );
  };

  if (loading && !metadata) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <ChevronLeft size={24} color={theme.colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>{resourceTitle}</Text>
          <Button
            title="New"
            onPress={() => navigation.navigate('ResourceForm', { resourceName, resourceTitle, metadata })}
            size="small"
            icon={<Plus size={16} color={theme.colors.surface} />}
          />
        </View>

        <View style={styles.searchContainer}>
          <Search size={20} color={theme.colors.textSecondary} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder={`Search ${resourceTitle}...`}
            value={search}
            onChangeText={setSearch}
            placeholderTextColor={theme.colors.textSecondary}
          />
        </View>
      </View>

      <FlatList
        data={data.filter(item => 
          JSON.stringify(item).toLowerCase().includes(search.toLowerCase())
        )}
        renderItem={renderItem}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshing={loading}
        onRefresh={fetchMetadataAndData}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No records found</Text>
          </View>
        }
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
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  headerTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.md,
  },
  backButton: {
    padding: theme.spacing.xs,
  },
  title: {
    ...theme.typography.h2,
    color: theme.colors.text,
    flex: 1,
    marginLeft: theme.spacing.sm,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
    height: 44,
  },
  searchIcon: {
    marginRight: theme.spacing.sm,
  },
  searchInput: {
    flex: 1,
    ...theme.typography.body,
    color: theme.colors.text,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: theme.spacing.lg,
  },
  itemCard: {
    marginBottom: theme.spacing.md,
    padding: 0,
    overflow: 'hidden',
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.md,
  },
  itemInfo: {
    flex: 1,
  },
  itemTitle: {
    ...theme.typography.subtitle,
    color: theme.colors.text,
    fontWeight: '800',
  },
  itemSubtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
    marginTop: 2,
  },
  itemId: {
    ...theme.typography.caption,
    color: theme.colors.primary,
    marginTop: 4,
    fontWeight: '700',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: theme.spacing.xxl,
  },
  emptyText: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
});
