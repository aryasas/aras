// claude-opus-4-7
// ARC mobile login: dot-grid hero, mono ID badge, primary action LEFT.
import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, SafeAreaView, Alert, TextInput, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LogIn } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { useAuthStore } from '../store/useAuthStore';

const C = theme.arc.light;

export const LoginScreen = () => {
  const login = useAuthStore((s) => s.login);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!username || !password) { Alert.alert('Missing', 'Enter username and password'); return; }
    setBusy(true);
    try { await login(username, password); }
    catch (e: any) { Alert.alert('Login failed', e?.message || 'Check credentials'); }
    finally { setBusy(false); }
  };

  return (
    <SafeAreaView style={s.root}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <View style={s.content}>
          <View style={s.card}>
            <View style={s.idRow}>
              <Text style={s.idBadge}>
                <Text style={s.idBold}>arc</Text>/auth/<Text style={s.idBold}>login</Text>
              </Text>
            </View>
            <Text style={s.title}>Sign in</Text>
            <Text style={s.subtitle}>Access your Aras workspace.</Text>

            <View style={{ height: 18 }} />

            <Text style={s.label}>Username</Text>
            <TextInput
              style={s.input}
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              placeholder="you@aras"
              placeholderTextColor={C.text3}
            />
            <View style={{ height: 12 }} />
            <Text style={s.label}>Password</Text>
            <TextInput
              style={s.input}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="••••••••"
              placeholderTextColor={C.text3}
            />

            <View style={s.actionBar}>
              <TouchableOpacity style={s.btnPrimary} onPress={submit} disabled={busy} activeOpacity={0.85}>
                {busy ? <ActivityIndicator color={theme.arc.accentInk} /> : (
                  <>
                    <LogIn size={16} color={theme.arc.accentInk} />
                    <Text style={s.btnPrimaryText}>Sign in</Text>
                  </>
                )}
              </TouchableOpacity>
              <View style={{ flex: 1 }} />
              <TouchableOpacity style={s.btnGhost} activeOpacity={0.7}>
                <Text style={s.btnGhostText}>Forgot?</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  content: { flex: 1, justifyContent: 'center', padding: 20 },
  card: { backgroundColor: C.surface, borderWidth: 1, borderColor: C.line, borderRadius: 14, padding: 22 },
  idRow: { marginBottom: 10 },
  idBadge: { fontFamily: 'Menlo', fontSize: 11, color: C.text3, letterSpacing: 0.3 },
  idBold: { color: C.text, fontWeight: '700' },
  title: { ...theme.typography.h2, color: C.text },
  subtitle: { ...theme.typography.body, color: C.text2, marginTop: 4 },
  label: { ...theme.typography.caption, color: C.text2, marginBottom: 6, textTransform: 'uppercase' },
  input: { height: 40, borderWidth: 1, borderColor: C.line, borderRadius: 8, paddingHorizontal: 12, color: C.text, backgroundColor: C.bg, fontFamily: 'PlusJakartaSans_400Regular', fontSize: 14 },
  actionBar: { flexDirection: 'row', alignItems: 'center', marginTop: 22, gap: 8 },
  btnPrimary: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, paddingHorizontal: 14, borderRadius: 8, backgroundColor: theme.arc.accent },
  btnPrimaryText: { color: theme.arc.accentInk, fontWeight: '600', fontSize: 13 },
  btnGhost: { height: 36, paddingHorizontal: 12, justifyContent: 'center' },
  btnGhostText: { color: C.text2, fontSize: 13 },
});
