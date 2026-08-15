import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { View, Text, StyleSheet } from 'react-native';

import { HomeScreen } from '../screens/HomeScreen';
import { WardrobeScreen } from '../screens/WardrobeScreen';
import { OutfitBuilderScreen } from '../screens/OutfitBuilderScreen';
import { AIStyleScreen } from '../screens/AIStyleScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { AddItemScreen } from '../screens/AddItemScreen';

import { Colors, Radius, Typography } from '../theme';
import { RootStackParamList, TabParamList } from '../types';

const Tab = createBottomTabNavigator<TabParamList>();
const Stack = createStackNavigator<RootStackParamList>();

const TAB_ICONS: Record<string, { active: string; inactive: string }> = {
  Home: { active: 'home', inactive: 'home-outline' },
  Wardrobe: { active: 'shirt', inactive: 'shirt-outline' },
  OutfitBuilder: { active: 'layers', inactive: 'layers-outline' },
  AIStyle: { active: 'sparkles', inactive: 'sparkles-outline' },
  Profile: { active: 'person', inactive: 'person-outline' },
};

const TAB_LABELS: Record<string, string> = {
  Home: 'Home',
  Wardrobe: 'Wardrobe',
  OutfitBuilder: 'Builder',
  AIStyle: 'AI Style',
  Profile: 'Profile',
};

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarBackground: () => <View style={styles.tabBarBg} />,
        tabBarShowLabel: true,
        tabBarActiveTintColor: Colors.gold,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarLabelStyle: styles.tabLabel,
        tabBarIcon: ({ focused, color, size }) => {
          const icons = TAB_ICONS[route.name];
          const iconName = focused ? icons.active : icons.inactive;

          if (route.name === 'AIStyle') {
            return (
              <View style={[styles.aiTabIcon, focused && styles.aiTabIconActive]}>
                <Ionicons name={iconName as any} size={20} color={focused ? Colors.background : Colors.textMuted} />
              </View>
            );
          }

          return <Ionicons name={iconName as any} size={22} color={color} />;
        },
        tabBarLabel: ({ focused, color }) => {
          const label = TAB_LABELS[route.name];
          if (route.name === 'AIStyle') return null;
          return <Text style={[styles.tabLabel, { color }]}>{label}</Text>;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Wardrobe" component={WardrobeScreen} />
      <Tab.Screen name="OutfitBuilder" component={OutfitBuilderScreen} />
      <Tab.Screen name="AIStyle" component={AIStyleScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export function AppNavigator() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: Colors.background },
      }}
    >
      <Stack.Screen name="MainTabs" component={MainTabs} />
      <Stack.Screen
        name="AddItem"
        component={AddItemScreen}
        options={{ presentation: 'modal' }}
      />
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: Colors.surface,
    borderTopColor: Colors.border,
    borderTopWidth: 1,
    height: 80,
    paddingBottom: 12,
    paddingTop: 8,
  },
  tabBarBg: {
    flex: 1,
    backgroundColor: Colors.surface,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
  },
  aiTabIcon: {
    width: 44,
    height: 44,
    borderRadius: Radius.full,
    backgroundColor: Colors.surfaceElevated,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  aiTabIconActive: {
    backgroundColor: Colors.gold,
    borderColor: Colors.gold,
  },
});
