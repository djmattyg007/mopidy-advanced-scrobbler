import fs from "fs";
import globby from "globby";
import path from "path";

import { svgIconPipeline } from "./code/svg-sanitation";
import { convertKebabToPascal } from "./code/utils";

process.chdir(path.dirname(__dirname));

const mdi = "node_modules/@mdi/svg/svg";

const svgPaths: [string, string][] = [
  ["delete", `${mdi}/delete-forever.svg`],
  ["edit", `${mdi}/pencil.svg`],
  ["refresh", `${mdi}/refresh.svg`],
  ["scrobble", `${mdi}/upload.svg`],
  ["scrobble-all", `${mdi}/auto-upload.svg`],
  ["skip-backward", `${mdi}/skip-backward.svg`],
  ["step-backward", `${mdi}/step-backward.svg`],
  ["step-forward", `${mdi}/step-forward.svg`],
  ["theme-auto", `${mdi}/brightness-auto.svg`],
  ["theme-dark", `${mdi}/brightness-1.svg`],
  ["theme-light", `${mdi}/brightness-5.svg`],
  ["tick", `${mdi}/check.svg`],
];

if (fs.existsSync("src/svg")) {
  for (const existingSvgFile of globby.sync("src/svg/*.svg")) {
    fs.unlinkSync(existingSvgFile);
  }
} else {
  fs.mkdirSync("src/svg");
}

if (fs.existsSync("src/icons")) {
  for (const existingIconFile of globby.sync("src/icons/*Icon.vue")) {
    fs.unlinkSync(existingIconFile);
  }
} else {
  fs.mkdirSync("src/icons");
}

function makeIconComponent(svgName: string, svgNamePascal: string): string {
  //import { Icon } from "@vicons/utils";
  return `<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/${svgName}.svg";

export default defineComponent({
  name: "${svgNamePascal}Icon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
`;
}

for (const [svgName, svgPath] of svgPaths) {
  const svgNamePascal = convertKebabToPascal(svgName);

  const destSvgPath = path.join("src", "svg", `${svgName}.svg`);
  const destComponentPath = path.join("src", "icons", `${svgNamePascal}Icon.vue`);

  const svg = fs.readFileSync(svgPath, "utf8");
  const sanitisedSvg = svgIconPipeline(svg);
  fs.writeFileSync(destSvgPath, sanitisedSvg);

  const component = makeIconComponent(svgName, svgNamePascal);
  fs.writeFileSync(destComponentPath, component);
}
