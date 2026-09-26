import { NavigationContainer } from "@react-navigation/native";
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

type RootStackParamList = {
  Home: undefined;
  Session: { lesson: LessonSummary };
  Practice: {
    subjectCode: LessonSummary["subject_code"];
    curriculumVersion: string;
    lessonId?: string;
    skillCode?: string;
  };
};
const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  // Authentication UI is intentionally supplied by the shared Nexora identity flow.
  // The shell receives a token through the environment until the login screen lands.
  const [token, setToken] = useState(process.env.EXPO_PUBLIC_ACCESS_TOKEN ?? "");
  const api = useMemo(() => new TutorApi(token), [token]);

  if (!token) {
    return <LoginScreen onLogin={setToken} />;
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Home">
          {({ navigation }) => (
            <HomeScreen
              api={api}
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
        <Stack.Screen name="Session">
          {({ route, navigation }) => (
            <TutorSessionScreen
              api={api}
              lesson={route.params.lesson}
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
    </NavigationContainer>
  );
}
