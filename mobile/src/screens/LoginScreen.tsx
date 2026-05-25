import React, { useState } from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, SafeAreaView, Alert } from 'react-native';
import { Mail, Lock, LogIn } from 'lucide-react-native';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { theme } from '../lib/theme';
import { useAuthStore } from '../store/useAuthStore';

export const LoginScreen = () => {
  const login = useAuthStore((state) => state.login);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Error', 'Please enter both username and password');
      return;
    }
    setIsLoading(true);
    try {
      await login(username, password);
    } catch (err: any) {
      Alert.alert('Login Failed', err.message || 'Please check your credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.title}>Welcome Back</Text>
            <Text style={styles.subtitle}>Sign in to your Aras Dashboard</Text>
          </View>

          <View style={styles.form}>
            <Input
              label="Username"
              placeholder="Enter your username"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              leftIcon={<Mail size={20} color={theme.colors.textSecondary} />}
            />
            
            <Input
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              leftIcon={<Lock size={20} color={theme.colors.textSecondary} />}
            />

            <Button
              title="Sign In"
              onPress={handleLogin}
              isLoading={isLoading}
              style={styles.loginButton}
              icon={<LogIn size={20} color={theme.colors.surface} />}
            />
            
            <Button
              title="Forgot Password?"
              variant="outline"
              onPress={() => {}}
              style={styles.forgotButton}
            />
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    padding: theme.spacing.xl,
  },
  header: {
    marginBottom: theme.spacing.xxl,
  },
  title: {
    ...theme.typography.h1,
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
  },
  subtitle: {
    ...theme.typography.body,
    color: theme.colors.textSecondary,
  },
  form: {
    width: '100%',
  },
  loginButton: {
    marginTop: theme.spacing.lg,
  },
  forgotButton: {
    marginTop: theme.spacing.md,
    borderWidth: 0,
  },
});
