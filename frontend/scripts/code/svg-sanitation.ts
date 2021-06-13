// Reference: https://github.com/07akioni/xicons/tree/4ba982a83ea8e7cbf13ec461281a0f47b6178398/packages/xicons/scripts

import { pipeline } from "./utils";

function createXmlAttrRegex(attr: string): RegExp {
  return new RegExp(`\\s${attr}="([^"]*)"`, "g");
}

export function removeComments(svg: string): string {
  return svg.replace(/<!--(.*?)-->/g, "");
}

export function removeUselessTags(svg: string): string {
  return svg
    .replace(/<\?xml(.*?)\?>/g, "")
    .replace(/<!DOCTYPE(.*?)>/g, "")
    .replace(/<title>(.*?)<\/title>/g, "")
    .replace(/<desc>(.*?)<\/desc>/g, "")
    .replace(/style="enable-background:([^;]+);"/g, 'enabled-background="$1"')
    .replace(/<svg t="[^"]+"/g, "<svg")
    .replace(/class="[^"]+"/g, "");
}

export function removeAttrs(svg: string, ...attrs: ReadonlyArray<string>): string {
  for (const attr of attrs) {
    svg = svg.replace(createXmlAttrRegex(attr), "");
  }

  return svg;
}

export function removeSvgAttrs(svg: string, ...attrs: ReadonlyArray<string>): string {
  const svgRegex = /<svg[^>]*>/;
  const svgRegexMatch = svg.match(svgRegex);
  if (!svgRegexMatch) {
    throw new Error("Invalid SVG supplied.");
  }

  let svgContent = svgRegexMatch[0];
  for (const attr of attrs) {
    svgContent = svgContent.replace(createXmlAttrRegex(attr), "");
  }

  return svg.replace(svgRegex, svgContent);
}

export function refill(svg: string): string {
  return svg
    .replace(/fill="([^"n]+)"/g, 'fill="currentColor"')
    .replace(/stroke="([^"n]+)"/g, 'stroke="currentColor"')
    .replace(/fill: ([^;n]+);/g, "fill: currentColor;")
    .replace(/stroke: *([^;n]+);/g, "stroke: currentColor;");
}

export const svgIconPipeline = pipeline<string>(
  removeComments,
  removeUselessTags,
  (svg) => removeAttrs(svg, "id"),
  (svg) => removeSvgAttrs(svg, "width", "height"),
  refill,
);
