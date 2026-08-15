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
import { RegistrationScreen } from '../screens/RegistrationScreen';
import { ItemDetailScreen } from '../screens/ItemDetailScreen';

import { Colors, Radius } from '../theme';
import { RootStackParamList, TabParamList } from '../types';
import { useUserStore } from '../store/userStore';

const Tab = createBottomTabNavigator<TabParamList>();
const Stack = createStackNavigator<RootStackParamList>();

const TAB_ICONS: Record<string, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }> = {
  Home: { active: 'home', inactive: 'home-outline' },
  Wardrobe: { active: 'shirt', inactive: 'shirt-outline' },
  OutfitBuilder: { active: 'layers', inactive: 'layers-outline' },
  AIStyle: { active: 'sparkles', inactive: 'sparkles-outline' },
  Profile: { active: 'person', inactive: 'person-outline' },
};

const TAB_LABELS: Record<string, string> = {
  Home: 'Ana Sayfa',
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
        tabBarBackground: () => <View style={styles.tabBarBg} />,
        tabBarActiveTintColor: Colors.goldLight,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarIcon: ({ focused, color }) => {
          const icons = TAB_ICONS[route.name];
          const iconName = focused ? icons.active : icons.inactive;
          if (route.name === 'AIStyle') {
            return (
              <View style={[styles.aiTabIcon, focused && styles.aiTabIconActive]}>
                <Ionicons name={iconName} size={20} color={focused ? Colors.background : Colors.textMuted} />
              </View>
            );
          }
          return <Ionicons name={iconName} size={21} color={color} />;
        },
        tabBarLabel: ({ color }) =>
          route.name === 'AIStyle' ? null : <Text style={[styles.tabLabel, { color }]}>{TAB_LABELS[route.name]}</Text>,
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
  const registered = useUserStore((s) => s.registered);

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: Colors.background },
      }}
    >
      {!registered ? (
        <Stack.Screen name="Registration" component={RegistrationScreen} />
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
    fontWeight: '700',
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
