// claude-opus-4-7
// ARC mobile login: dot-grid hero, mono ID badge, primary action LEFT.
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Switch,
  Vibration,
} from 'react-native';
import { TextInput as RNTextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LogIn } from 'lucide-react-native';
import { theme } from '../lib/theme';
import { useAuthStore } from '../store/useAuthStore';
import { getStoredValue, setStoredValue } from '../lib/storage';
import { setApiBaseUrl } from '../lib/apiBaseUrl';

const C = theme.arc.light;
const workspaceUrlKey = 'aras_workspace_url';

export const LoginScreen = () => {
  const login = useAuthStore((s) => s.login);
  const usernameRef = useRef<RNTextInput>(null);
  const passwordRef = useRef<RNTextInput>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [workspaceUrl, setWorkspaceUrl] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [busy, setBusy] = useState(false);

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

  const submit = async () => {
    if (!username || !password) { Alert.alert('Missing', 'Enter username and password'); return; }
    if (!workspaceUrl.trim()) { Alert.alert('Missing', 'Enter your workspace URL'); return; }
    setBusy(true);
    try {
      const raw = workspaceUrl.trim();
      // claude-sonnet-4-6
      // IP addresses or localhost with a port are local — use http to avoid cert errors.
      const isLocal = /^(localhost|127\.|192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/i.test(raw.replace(/^https?:\/\//i, ''));
      const normalizedUrl = !/^https?:\/\//i.test(raw)
        ? `${isLocal ? 'http' : 'https'}://${raw}`
        : raw;

      setWorkspaceUrl(normalizedUrl);
      await setApiBaseUrl(normalizedUrl);
      await login(username, password, rememberMe);
      await setStoredValue(workspaceUrlKey, normalizedUrl);
    }
    catch (e: any) { Vibration.vibrate(200); Alert.alert('Login failed', e?.message || 'Check credentials'); }
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

            <Text style={s.label}>Workspace URL</Text>
            <TextInput
              style={s.input}
              value={workspaceUrl}
              onChangeText={setWorkspaceUrl}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
              textContentType="URL"
              autoComplete="url"
              returnKeyType="next"
              onSubmitEditing={() => usernameRef.current?.focus()}
              placeholder="https://yourcompany.aras.id"
              placeholderTextColor={C.text3}
            />
            <View style={{ height: 12 }} />
            <Text style={s.label}>Username</Text>
            <TextInput
              style={s.input}
              ref={usernameRef}
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              textContentType="username"
              autoComplete="username"
              returnKeyType="next"
              onSubmitEditing={() => passwordRef.current?.focus()}
              placeholder="you@aras"
              placeholderTextColor={C.text3}
            />
            <View style={{ height: 12 }} />
            <Text style={s.label}>Password</Text>
            <TextInput
              style={s.input}
              ref={passwordRef}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              textContentType="password"
              autoComplete="current-password"
              returnKeyType="go"
              onSubmitEditing={submit}
              placeholder="••••••••"
              placeholderTextColor={C.text3}
            />

            <View style={s.rememberRow}>
              <Text style={s.rememberLabel}>Remember me</Text>
              <Switch
                value={rememberMe}
                onValueChange={setRememberMe}
                trackColor={{ false: C.line, true: theme.arc.accent }}
                thumbColor={rememberMe ? theme.arc.accentInk : C.text3}
              />
            </View>

            <View style={s.actionBar}>
              <TouchableOpacity style={s.btnPrimary} onPress={submit} disabled={busy} activeOpacity={0.85}>
                {busy ? <ActivityIndicator color={theme.arc.accentInk} /> : (
                  <>
                    <LogIn size={16} color={theme.arc.accentInk} />
                    <Text style={s.btnPrimaryText}>Sign in</Text>
                  </>
                )}
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
  rememberRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 14 },
  rememberLabel: { ...theme.typography.body, color: C.text2 },
  actionBar: { flexDirection: 'row', alignItems: 'center', marginTop: 22, gap: 8 },
  btnPrimary: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, paddingHorizontal: 14, borderRadius: 8, backgroundColor: theme.arc.accent },
  btnPrimaryText: { color: theme.arc.accentInk, fontWeight: '600', fontSize: 13 },
});
