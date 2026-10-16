import Image from "next/image";
import { brandAssets } from "../../../packages/presentation/brand";

export function BrandLogo() {
  return <span className="brand-logo" role="img" aria-label="AQLITH">
    <Image className="brand-logo-light" src={`/brand/${brandAssets.light.file}`} width={brandAssets.light.width}
      height={brandAssets.light.height} alt="" unoptimized loading="eager" />
    <Image className="brand-logo-dark" src={`/brand/${brandAssets.dark.file}`} width={brandAssets.dark.width}
      height={brandAssets.dark.height} alt="" unoptimized loading="eager" />
  </span>;
}
