import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { brandAssets } from "../../packages/presentation/brand.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
for (const asset of Object.values(brandAssets)) test(`approved PNG integrity: ${asset.file}`, () => {
  for (const directory of ["apps/tutor-mobile/assets/brand", "apps/tutor-web/public/brand"]) {
    const bytes = readFileSync(path.join(root, directory, asset.file));
    assert.equal(bytes.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.equal(bytes.readUInt32BE(16), asset.width);
    assert.equal(bytes.readUInt32BE(20), asset.height);
    assert.equal(createHash("sha256").update(bytes).digest("hex"), asset.sha256);
  }
});

test("Expo icon configuration resolves to the original square PNG", () => {
  const { expo } = JSON.parse(readFileSync(path.join(root, "apps/tutor-mobile/app.json")));
  const icon = readFileSync(path.resolve(root, "apps/tutor-mobile", expo.icon));
  assert.equal(createHash("sha256").update(icon).digest("hex"), brandAssets.icon.sha256);
  assert.equal(icon.readUInt32BE(16), icon.readUInt32BE(20));
  assert.equal(expo.userInterfaceStyle, "automatic");
});
