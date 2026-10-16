import { DarkTheme, DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { useMemo } from "react";
import { useState } from "react";

import type { LessonSummary } from "@contracts/tutor";
import { TutorApi } from "./src/api/client";
import { HomeScreen } from "./src/screens/HomeScreen";
import { LoginScreen } from "./src/screens/LoginScreen";
import { TutorSessionScreen } from "./src/screens/TutorSessionScreen";
import { PracticeScreen } from "./src/screens/PracticeScreen";
import { VoiceScreen } from "./src/screens/VoiceScreen";
import { PreferenceControls, PreferencesProvider, usePreferences } from "./src/preferences";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { useFonts } from "expo-font";
import { ActivityIndicator, Text } from "react-native";
import { cairoFonts } from "./src/typography";

type RootStackParamList = {
  Home: undefined;
  Voice: undefined;
  Session: { lesson: LessonSummary; question?: string };
  Practice: {
    subjectCode: LessonSummary["subject_code"];
    curriculumVersion: string;
    lessonId?: string;
    skillCode?: string;
  };
};
const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  const [loaded, error] = useFonts(cairoFonts);
  if (error) return <SafeAreaProvider><Text accessibilityRole="alert">تعذر تحميل خط Cairo. / Cairo could not be loaded.</Text></SafeAreaProvider>;
  if (!loaded) return <ActivityIndicator accessibilityLabel="تحميل الخط / Loading font" />;
  return <SafeAreaProvider><PreferencesProvider><AppContent /></PreferencesProvider></SafeAreaProvider>;
}

function AppContent() {
  const { theme, dark, rtl } = usePreferences();
  // Authenticate on the device; public Expo variables are bundled into the app.
  const [token, setToken] = useState("");
  const api = useMemo(() => new TutorApi(token), [token]);

  if (!token) {
    return <><StatusBar style={dark ? "light" : "dark"} /><PreferenceControls /><LoginScreen onLogin={setToken} /></>;
  }

  return (
    <><PreferenceControls /><NavigationContainer direction={rtl ? "rtl" : "ltr"} theme={{ ...(dark ? DarkTheme : DefaultTheme), colors: {
      ...(dark ? DarkTheme : DefaultTheme).colors, background: theme.colors.background, card: theme.colors.surface,
      text: theme.colors.text, primary: theme.colors.primary, border: theme.colors.border,
    } }}>
      <StatusBar style={dark ? "light" : "dark"} />
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Home">
          {({ navigation }) => (
            <HomeScreen
              api={api}
              onOpenVoice={() => navigation.navigate("Voice")}
              onOpenLesson={(lesson) => navigation.navigate("Session", { lesson })}
              onOpenPractice={(recommendation) =>
                navigation.navigate("Practice", {
                  subjectCode: recommendation.subject_code,
                  curriculumVersion: recommendation.curriculum_version,
                  lessonId: recommendation.question.lesson_id,
                  skillCode: recommendation.skill_code ?? undefined,
                })
              }
            />
          )}
        </Stack.Screen>
        <Stack.Screen name="Voice">
          {({ navigation }) => <VoiceScreen api={api} onHome={() => navigation.navigate("Home")}
            onLesson={(lesson, question) => navigation.navigate("Session", { lesson, question })}
            onPractice={item => navigation.navigate("Practice", { subjectCode: item.subject_code,
              curriculumVersion: item.curriculum_version, lessonId: item.question.lesson_id, skillCode: item.skill_code ?? undefined })} />}
        </Stack.Screen>
        <Stack.Screen name="Session">
          {({ route, navigation }) => (
            <TutorSessionScreen
              api={api}
              lesson={route.params.lesson}
              initialQuestion={route.params.question}
              onBack={() => navigation.goBack()}
              onPractice={() =>
                navigation.navigate("Practice", {
                  subjectCode: route.params.lesson.subject_code,
                  curriculumVersion: route.params.lesson.curriculum_version,
                  lessonId: route.params.lesson.id,
                })
              }
            />
          )}
        </Stack.Screen>
        <Stack.Screen name="Practice">
          {({ route, navigation }) => (
            <PracticeScreen
              api={api}
              subjectCode={route.params.subjectCode}
              curriculumVersion={route.params.curriculumVersion}
              lessonId={route.params.lessonId}
              skillCode={route.params.skillCode}
              onBack={() => navigation.goBack()}
            />
          )}
        </Stack.Screen>
      </Stack.Navigator>
    </NavigationContainer></>
  );
}
