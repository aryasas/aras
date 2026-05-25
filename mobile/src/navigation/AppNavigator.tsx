// claude-opus-4-7
// ARC mobile navigator: single stack. Bottom tab bar is rendered by MobileShell
// per screen (floating glass), so no Tab.Navigator is used here.
import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

import { useAuthStore } from '../store/useAuthStore';
import { LoginScreen } from '../screens/LoginScreen';
import { AppHomeScreen } from '../screens/AppHomeScreen';
import { AppMenuScreen } from '../screens/AppMenuScreen';
import { ResourceListScreen } from '../screens/ResourceListScreen';
import { ResourceFormScreen } from '../screens/ResourceFormScreen';
import { SettingsScreen } from '../screens/SettingsScreen';

const Stack = createStackNavigator();

export default function AppNavigator() {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => { checkAuth(); }, []);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : (
          <>
            <Stack.Screen name="AppHome" component={AppHomeScreen} />
            <Stack.Screen name="AppMenu" component={AppMenuScreen} />
            <Stack.Screen name="ResourceList" component={ResourceListScreen} />
            <Stack.Screen name="ResourceForm" component={ResourceFormScreen} />
            <Stack.Screen name="Settings" component={SettingsScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
