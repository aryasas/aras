import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, SafeAreaView, ActivityIndicator, Alert } from 'react-native';
import { ChevronLeft, Save, Trash2 } from 'lucide-react-native';
import { theme } from '../lib/theme';
import api from '../lib/api';
import { Input } from '../components/Input';
import { Button } from '../components/Button';

export const ResourceFormScreen = ({ route, navigation }: any) => {
  const { resourceName, resourceTitle, id, metadata } = route.params;
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      fetchRecord();
    }
  }, [id]);

  const fetchRecord = async () => {
    try {
      setLoading(true);
      const cleanResource = resourceName.replace(/\//g, '_');
      const response = await api.get(`/${cleanResource}/${id}`);
      setFormData(response.data);
    } catch (err) {
      console.error('Failed to fetch record', err);
      Alert.alert('Error', 'Failed to fetch record details');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const cleanResource = resourceName.replace(/\//g, '_');
      const apiPath = `/${cleanResource}`;
      if (id) {
        await api.patch(`${apiPath}/${id}`, formData);
        Alert.alert('Success', 'Record updated successfully');
      } else {
        await api.post(apiPath, formData);
        Alert.alert('Success', 'Record created successfully');
      }
      navigation.goBack();
    } catch (err: any) {
      console.error('Failed to save record', err);
      Alert.alert('Error', err.response?.data?.detail || 'Failed to save record');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    Alert.alert(
      'Confirm Delete',
      'Are you sure you want to delete this record?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              const cleanResource = resourceName.replace(/\//g, '_');
              await api.delete(`/${cleanResource}/${id}`);
              navigation.goBack();
            } catch (err) {
              Alert.alert('Error', 'Failed to delete record');
            }
          }
        }
      ]
    );
  };

  const renderFields = () => {
    if (!metadata?.fields) return null;

    return metadata.fields
      .filter((f: any) => !f.form_hidden && f.name !== 'id')
      .map((field: any) => (
        <Input
          key={field.name}
          label={field.label || field.name}
          placeholder={`Enter ${field.label || field.name}`}
          value={formData[field.name] ? String(formData[field.name]) : ''}
          onChangeText={(val) => setFormData({ ...formData, [field.name]: val })}
          keyboardType={field.type === 'number' || field.type === 'currency' ? 'numeric' : 'default'}
        />
      ));
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
        <Text style={styles.title}>{id ? `Edit ${resourceTitle}` : `New ${resourceTitle}`}</Text>
        {id && (
          <TouchableOpacity onPress={handleDelete} style={styles.deleteButton}>
            <Trash2 size={22} color={theme.colors.error} />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.formCard}>
          {renderFields()}
        </View>

        <Button
          title={id ? "Update Record" : "Create Record"}
          onPress={handleSave}
          isLoading={saving}
          style={styles.saveButton}
          icon={<Save size={20} color={theme.colors.surface} />}
        />
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
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  backButton: {
    padding: theme.spacing.xs,
  },
  title: {
    ...theme.typography.h3,
    color: theme.colors.text,
    flex: 1,
    marginLeft: theme.spacing.md,
  },
  deleteButton: {
    padding: theme.spacing.sm,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: theme.spacing.lg,
  },
  formCard: {
    backgroundColor: theme.colors.surface,
    padding: theme.spacing.lg,
    borderRadius: theme.borderRadius.lg,
    ...theme.shadows.sm,
    marginBottom: theme.spacing.xl,
  },
  saveButton: {
    marginBottom: theme.spacing.xxl,
  },
});
