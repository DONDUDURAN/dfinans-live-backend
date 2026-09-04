import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import { Text, View, StyleSheet } from 'react-native';

import { HomeScreen } from '../screens/HomeScreen';
import { WardrobeScreen } from '../screens/WardrobeScreen';
import { OutfitBuilderScreen } from '../screens/OutfitBuilderScreen';
import { AIStyleScreen } from '../screens/AIStyleScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { AddItemScreen } from '../screens/AddItemScreen';
import { AuthScreen } from '../screens/AuthScreen';
import { ItemDetailScreen } from '../screens/ItemDetailScreen';

import { Colors } from '../theme';
import { RootStackParamList, TabParamList } from '../types';
import { useUserStore } from '../store/userStore';

const Tab = createBottomTabNavigator<TabParamList>();
const Stack = createStackNavigator<RootStackParamList>();

const TAB_ICONS: Record<string, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }> = {
  Home: { active: 'home', inactive: 'home-outline' },
  Wardrobe: { active: 'shirt', inactive: 'shirt-outline' },
  OutfitBuilder: { active: 'layers', inactive: 'layers-outline' },
  AIStyle: { active: 'body', inactive: 'body-outline' },
  Profile: { active: 'person', inactive: 'person-outline' },
};

const TAB_LABELS: Record<string, string> = {
  Home: 'Sanal İkiz',
  Wardrobe: 'Gardırop',
  OutfitBuilder: 'Stil',
  AIStyle: 'Kabin',
  Profile: 'Profil',
};

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: styles.tabBar,
        tabBarItemStyle: styles.tabBarItem,
        tabBarBackground: () => <View style={styles.tabBarBg} />,
        tabBarActiveTintColor: Colors.goldLight,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarIcon: ({ focused, color }) => {
          const icons = TAB_ICONS[route.name];
          const iconName = focused ? icons.active : icons.inactive;
          return <Ionicons name={iconName} size={21} color={color} />;
        },
        tabBarLabel: ({ color }) =>
          <Text
            style={[styles.tabLabel, { color }]}
            numberOfLines={1}
            adjustsFontSizeToFit
            minimumFontScale={0.88}
          >
            {TAB_LABELS[route.name]}
          </Text>,
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="AIStyle" component={AIStyleScreen} />
      <Tab.Screen name="Wardrobe" component={WardrobeScreen} />
      <Tab.Screen name="OutfitBuilder" component={OutfitBuilderScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export function AppNavigator() {
  const isAuthenticated = useUserStore((s) => s.isAuthenticated);

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: Colors.background },
      }}
    >
      {!isAuthenticated ? (
        <Stack.Screen name="Auth" component={AuthScreen} />
      ) : (
        <>
          <Stack.Screen name="MainTabs" component={MainTabs} />
          <Stack.Screen name="AddItem" component={AddItemScreen} options={{ presentation: 'modal' }} />
          <Stack.Screen name="ItemDetail" component={ItemDetailScreen} options={{ presentation: 'card' }} />
        </>
      )}
    </Stack.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: Colors.surface,
    borderTopColor: Colors.border,
    borderTopWidth: StyleSheet.hairlineWidth,
    height: 76,
    paddingBottom: 14,
    paddingTop: 10,
  },
  tabBarBg: {
    flex: 1,
    backgroundColor: Colors.surface,
  },
  tabBarItem: {
    paddingHorizontal: 2,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.2,
    textTransform: 'none',
    textAlign: 'center',
    includeFontPadding: false,
  },
});
