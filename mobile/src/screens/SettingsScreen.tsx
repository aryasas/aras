// claude-sonnet-4-6
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Modal, TextInput, Linking, Alert } from 'react-native';
// @ts-ignore Expo provides this package at runtime after install/hoist.
import Constants from 'expo-constants';
import { User, Bell, Shield, CircleHelp, LogOut, ChevronRight, Languages } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { useAuthStore } from '../store/useAuthStore';
import { useLanguage } from '../context/LanguageContext';
import { MobileShell } from '../components/MobileShell';
import api from '../lib/api';
import { useToastStore } from '../lib/toast';
import { getStoredValue } from '../lib/storage';

const C = theme.arc.dark;
const workspaceUrlKey = 'aras_workspace_url';

// claude-sonnet-4-6
export const SettingsScreen = ({ navigation }: any) => {
  const { user, logout } = useAuthStore();
  const { lang, setLang, t } = useLanguage();
  const showToast = useToastStore((state) => state.show);
  const [profileVisible, setProfileVisible] = useState(false);
  const [comingSoonVisible, setComingSoonVisible] = useState(false);
  const [fullName, setFullName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [workspaceUrl, setWorkspaceUrl] = useState('');

  // claude-sonnet-4-6
  useEffect(() => {
    setFullName(user?.name || '');
    setEmail(user?.email || '');
  }, [user?.name, user?.email]);

  // claude-sonnet-4-6
  useEffect(() => {
    let mounted = true;

    const loadWorkspaceUrl = async () => {
      const storedWorkspaceUrl = await getStoredValue(workspaceUrlKey);
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
  const handleLogout = async () => {
    Alert.alert(
      'Sign out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign out', style: 'destructive', onPress: async () => { try { await logout('manual'); } catch {} } },
      ]
    );
  };

  // claude-sonnet-4-6
  const saveProfile = async () => {
    try {
      await api.put('/auth/me', { name: fullName.trim(), email: email.trim() });
      useAuthStore.setState((s) => ({
        user: s.user ? { ...s.user, name: fullName.trim(), email: email.trim() } : s.user,
      }));
      showToast('Profile updated', 'success');
      setProfileVisible(false);
    } catch (error: any) {
      showToast(error?.message || 'Failed to update profile', 'error');
    }
  };

  // claude-sonnet-4-6
  const openSupport = async () => {
    await Linking.openURL('mailto:support@aras.id');
  };

  const version = Constants.expoConfig?.version || '1.0.0';
  const initialsSource = (user?.name || user?.username || 'User').trim();
  const initials = initialsSource
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0] || '')
    .join('')
    .toUpperCase()
    .slice(0, 2) || 'U';

  const menuItems = [
    { title: 'Profile', icon: User, onPress: () => setProfileVisible(true) },
    { title: 'Notifications', icon: Bell, onPress: () => setComingSoonVisible(true) },
    { title: 'Privacy & Security', icon: Shield, onPress: () => setComingSoonVisible(true) },
    { title: 'Help & Support', icon: CircleHelp, onPress: openSupport },
  ];

  return (
    <MobileShell active="you" title="Settings" navigation={navigation}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{initials}</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user?.name || user?.username || 'User'}</Text>
            <Text style={styles.profileEmail}>{user?.email || 'user@example.com'}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('lang.label')}</Text>
          <View style={styles.sectionCard}>
            <View style={styles.langRow}>
              <View style={styles.menuItemLeft}>
                <Languages size={20} color={C.text3} />
                <Text style={styles.menuItemTitle}>{t('lang.label')}</Text>
              </View>
              <View style={styles.langButtons}>
                <TouchableOpacity
                  onPress={() => setLang('en')}
                  style={[styles.langButton, lang === 'en' && styles.langButtonActive]}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.langButtonText, lang === 'en' && styles.langButtonTextActive]}>EN</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => setLang('id')}
                  style={[styles.langButton, lang === 'id' && styles.langButtonActive]}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.langButtonText, lang === 'id' && styles.langButtonTextActive]}>ID</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>General</Text>
          <View style={styles.sectionCard}>
            {menuItems.map((item, index) => {
              const Icon = item.icon;
              return (
                <TouchableOpacity
                  key={item.title}
                  style={[styles.menuItem, index !== menuItems.length - 1 && styles.menuItemBorder]}
                  onPress={item.onPress}
                  activeOpacity={0.8}
                >
                  <View style={styles.menuItemLeft}>
                    <Icon size={20} color={C.text3} />
                    <Text style={styles.menuItemTitle}>{item.title}</Text>
                  </View>
                  <ChevronRight size={20} color={C.text3} />
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} activeOpacity={0.85}>
          <LogOut size={20} color={theme.arc.danger} />
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <View style={styles.versionRow}>
            <Text style={styles.versionLabel}>Version</Text>
            <Text style={styles.versionValue}>{version}</Text>
          </View>
          <Text style={styles.workspaceLabel}>Workspace URL</Text>
          <Text style={styles.workspaceValue}>{workspaceUrl || 'not set'}</Text>
        </View>
      </ScrollView>

      <Modal visible={profileVisible} transparent animationType="fade" onRequestClose={() => setProfileVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Profile</Text>
            <Text style={styles.modalText}>Update your display name.</Text>
            <TextInput
              value={fullName}
              onChangeText={setFullName}
              placeholder="Full name"
              placeholderTextColor={C.text3}
              style={styles.modalInput}
            />
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="Email"
              placeholderTextColor={C.text3}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              style={styles.modalInput}
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalButtonSecondary} onPress={() => setProfileVisible(false)} activeOpacity={0.8}>
                <Text style={styles.modalButtonSecondaryText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.modalButtonPrimary} onPress={saveProfile} activeOpacity={0.85}>
                <Text style={styles.modalButtonPrimaryText}>Save</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={comingSoonVisible} transparent animationType="fade" onRequestClose={() => setComingSoonVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Coming soon</Text>
            <Text style={styles.modalText}>This section is not available yet.</Text>
            <TouchableOpacity
              style={[styles.modalButtonPrimary, { alignSelf: 'stretch' }]}
              onPress={() => setComingSoonVisible(false)}
              activeOpacity={0.85}
            >
              <Text style={styles.modalButtonPrimaryText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </MobileShell>
  );
};

const styles = StyleSheet.create({
  content: {
    padding: 16,
    paddingBottom: 120,
  },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    marginBottom: 22,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.surface,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: theme.arc.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  avatarText: {
    color: theme.arc.accentInk,
    fontSize: 15,
    fontWeight: '700',
    fontFamily: 'Menlo',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    color: C.text,
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 2,
  },
  profileEmail: {
    color: C.text2,
    fontSize: 13,
  },
  section: {
    marginBottom: 22,
  },
  sectionTitle: {
    color: C.text3,
    marginBottom: 8,
    marginLeft: 4,
    letterSpacing: 1.2,
    fontSize: 11,
    fontWeight: '700',
    fontFamily: 'Menlo',
    textTransform: 'uppercase',
  },
  sectionCard: {
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 12,
    backgroundColor: C.surface,
    overflow: 'hidden',
  },
  langRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  langButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  langButton: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: C.line,
  },
  langButtonActive: {
    backgroundColor: theme.arc.accent,
    borderColor: theme.arc.accent,
  },
  langButtonText: {
    color: C.text3,
    fontSize: 11,
    fontWeight: '700',
    fontFamily: 'Menlo',
  },
  langButtonTextActive: {
    color: theme.arc.accentInk,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: C.line,
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  menuItemTitle: {
    color: C.text,
    fontSize: 14.5,
    fontWeight: '700',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 14,
    borderWidth: 1,
    borderColor: theme.arc.danger,
    borderRadius: 12,
    marginBottom: 18,
    backgroundColor: C.surface,
  },
  logoutText: {
    color: theme.arc.danger,
    fontSize: 14,
    fontWeight: '700',
  },
  footer: {
    gap: 6,
    paddingTop: 6,
  },
  versionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  versionLabel: {
    color: C.text3,
    fontSize: 11,
    fontFamily: 'Menlo',
    textTransform: 'uppercase',
    letterSpacing: 1.2,
  },
  versionValue: {
    color: C.text,
    fontSize: 11,
    fontFamily: 'Menlo',
  },
  workspaceLabel: {
    color: C.text3,
    fontSize: 11,
    fontFamily: 'Menlo',
    textTransform: 'uppercase',
    letterSpacing: 1.2,
  },
  workspaceValue: {
    color: C.text2,
    fontSize: 11,
    fontFamily: 'Menlo',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  modalCard: {
    width: '100%',
    maxWidth: 420,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: C.line,
    backgroundColor: C.bg,
    padding: 18,
    gap: 10,
  },
  modalTitle: {
    color: C.text,
    fontSize: 18,
    fontWeight: '700',
  },
  modalText: {
    color: C.text2,
    fontSize: 13,
    lineHeight: 19,
  },
  modalInput: {
    height: 42,
    borderWidth: 1,
    borderColor: C.line,
    borderRadius: 8,
    paddingHorizontal: 12,
    color: C.text,
    backgroundColor: C.surface,
    fontSize: 14,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 10,
    marginTop: 4,
  },
  modalButtonSecondary: {
    height: 38,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.line,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.surface,
  },
  modalButtonSecondaryText: {
    color: C.text,
    fontSize: 13,
    fontWeight: '700',
  },
  modalButtonPrimary: {
    height: 38,
    paddingHorizontal: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: theme.arc.accent,
  },
  modalButtonPrimaryText: {
    color: theme.arc.accentInk,
    fontSize: 13,
    fontWeight: '700',
  },
});
