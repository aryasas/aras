import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, Settings as SettingsIcon } from 'lucide-react-native';

import { theme } from '../lib/theme';
import { useAuthStore } from '../store/useAuthStore';

// Screens
import { LoginScreen } from '../screens/LoginScreen';
import { AppHomeScreen } from '../screens/AppHomeScreen';
import { AppMenuScreen } from '../screens/AppMenuScreen';
import { ResourceListScreen } from '../screens/ResourceListScreen';
import { ResourceFormScreen } from '../screens/ResourceFormScreen';
import { SettingsScreen } from '../screens/SettingsScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const HomeStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="AppHome" component={AppHomeScreen} />
    <Stack.Screen name="AppMenu" component={AppMenuScreen} />
    <Stack.Screen name="ResourceList" component={ResourceListScreen} />
    <Stack.Screen name="ResourceForm" component={ResourceFormScreen} />
  </Stack.Navigator>
);

const MainTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          ...theme.typography.caption,
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeStack}
        options={{
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarIcon: ({ color, size }) => <SettingsIcon size={size} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
};

export default function AppNavigator() {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : (
          <Stack.Screen name="Main" component={MainTabs} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
