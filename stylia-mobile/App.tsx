import 'react-native-gesture-handler';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { AppNavigator } from './src/navigation/AppNavigator';
import { Colors } from './src/theme';
import { useUserStore } from './src/store/userStore';

// Resolves to true once Zustand has read persisted state from AsyncStorage.
// Prevents the registration screen from flashing on returning users.
function useHydrated() {
  const [hydrated, setHydrated] = React.useState(useUserStore.persist.hasHydrated());
  React.useEffect(() => {
    const unsub = useUserStore.persist.onFinishHydration(() => setHydrated(true));
    setHydrated(useUserStore.persist.hasHydrated());
    return unsub;
  }, []);
  return hydrated;
}

export default function App() {
  const hydrated = useHydrated();

  if (!hydrated) {
    return (
      <SafeAreaProvider>
        <StatusBar style="light" backgroundColor={Colors.background} />
        <View style={{ flex: 1, backgroundColor: Colors.background, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator size="small" color={Colors.gold} />
        </View>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer
        theme={{
          dark: true,
          colors: {
            primary: Colors.gold,
            background: Colors.background,
            card: Colors.surface,
            text: Colors.textPrimary,
            border: Colors.border,
            notification: Colors.gold,
          },
        }}
      >
        <StatusBar style="light" backgroundColor={Colors.background} />
        <AppNavigator />
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
