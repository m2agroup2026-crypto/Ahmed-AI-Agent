import { Image, View } from "react-native";
import { brandAssets, brandBackgrounds } from "../../../packages/presentation/brand";
import { usePreferences } from "./preferences";

const sources = {
  light: require("../assets/brand/aqlith-logo-light.png"),
  dark: require("../assets/brand/aqlith-logo-dark.png"),
};

export function BrandLogo() {
  const { dark } = usePreferences();
  const tone = dark ? "dark" : "light";
  const asset = brandAssets[tone];
  return <View style={{ backgroundColor: brandBackgrounds[tone], borderRadius: 12, padding: 10, alignSelf: "stretch", marginBottom: 12 }}>
    <Image source={sources[tone]} accessibilityLabel="AQLITH" accessible resizeMode="contain"
      style={{ width: "100%", aspectRatio: asset.width / asset.height, maxHeight: 96 }} />
  </View>;
}
