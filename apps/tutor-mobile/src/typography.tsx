import { StyleSheet, Text as NativeText, TextInput as NativeTextInput, type TextProps, type TextInputProps } from "react-native";

// Static, licensed fonts work consistently in Expo Go and native builds.
export const cairoFonts = {
  CairoRegular: require("../assets/fonts/cairo/Cairo_400Regular.ttf"),
  CairoSemiBold: require("../assets/fonts/cairo/Cairo_600SemiBold.ttf"),
  CairoBold: require("../assets/fonts/cairo/Cairo_700Bold.ttf"),
  CairoExtraBold: require("../assets/fonts/cairo/Cairo_800ExtraBold.ttf"),
};
function family(weight: unknown) {
  const value = weight === "bold" ? 700 : Number(weight) || 400;
  return value >= 800 ? "CairoExtraBold" : value >= 700 ? "CairoBold" : value >= 500 ? "CairoSemiBold" : "CairoRegular";
}
// Cairo includes Arabic and Latin; platform fallback supplies unsupported math glyphs.
// Direction and official content strings remain the caller's responsibility.
export function Text({ style, ...props }: TextProps) {
  return <NativeText {...props} style={[style, { fontFamily: family(StyleSheet.flatten(style)?.fontWeight), fontWeight: "normal" }]} />;
}
export function TextInput({ style, ...props }: TextInputProps) {
  return <NativeTextInput {...props} style={[style, { fontFamily: family(StyleSheet.flatten(style)?.fontWeight), fontWeight: "normal" }]} />;
}
