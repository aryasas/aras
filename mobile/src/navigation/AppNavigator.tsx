// claude-opus-4-7
// ARC mobile navigator: single stack. Bottom tab bar is rendered by MobileShell
// per screen (floating glass), so no Tab.Navigator is used here.
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Linking, View } from 'react-native';

import { useAuthStore } from '../store/useAuthStore';
import { LoginScreen } from '../screens/LoginScreen';
import { AppHomeScreen } from '../screens/AppHomeScreen';
import { AppsListScreen } from '../screens/AppsListScreen';
import { AppMenuScreen } from '../screens/AppMenuScreen';
import { ResourceListScreen } from '../screens/ResourceListScreen';
import { ResourceFormScreen } from '../screens/ResourceFormScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { PosScreen } from '../screens/PosScreen';
import ErrorBoundary from '../components/ErrorBoundary';
import { ToastOverlay } from '../components/ToastOverlay';

const Stack = createStackNavigator();
const linking = {
  prefixes: ['aras://', 'https://app.aras.id'],
  config: {
    screens: {
      AppHome: '',
      AppsList: 'apps',
      AppMenu: 'apps/:appName',
      ResourceList: 'r/:resourceName',
      ResourceForm: 'r/:resourceName/:id',
      Settings: 'settings',
      Pos: 'pos',
    },
  },
};

void Linking;

export default function AppNavigator() {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => { checkAuth(); }, []);

  return (
    <View style={{ flex: 1 }}>
      <NavigationContainer linking={linking}>
        {!isAuthenticated ? (
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="Login" component={LoginScreen} />
          </Stack.Navigator>
        ) : (
          <ErrorBoundary>
            <Stack.Navigator screenOptions={{ headerShown: false }}>
              <Stack.Screen name="AppHome" component={AppHomeScreen} />
              <Stack.Screen name="AppsList" component={AppsListScreen} />
              <Stack.Screen name="AppMenu" component={AppMenuScreen} />
              <Stack.Screen name="ResourceList" component={ResourceListScreen} />
              <Stack.Screen name="ResourceForm" component={ResourceFormScreen} />
              <Stack.Screen name="Settings" component={SettingsScreen} />
              <Stack.Screen name="Pos" component={PosScreen} />
            </Stack.Navigator>
          </ErrorBoundary>
        )}
      </NavigationContainer>
      <ToastOverlay />
    </View>
  );
}
