import fs from "fs";
import path from "path";

if (process.argv.length < 3) {
  console.error("You must supply the path to the SVG file.");
  process.exit(1);
}

const svgStoragePath = path.join(path.dirname(__dirname), "src", "svg");

const origSvgPath = process.argv[2];
const parsedOrigSvgPath = path.parse(origSvgPath);

const svgName = parsedOrigSvgPath["name"];
const destSvgPath = path.join(svgStoragePath, `${svgName}.svg`);

// Reference: https://github.com/07akioni/xicons/tree/4ba982a83ea8e7cbf13ec461281a0f47b6178398/packages/xicons/scripts

function createXmlAttrRegex(attr: string): RegExp {
  return new RegExp(`\\s${attr}="([^"]*)"`, "g");
}

class SvgSanitiser {
  public constructor(private svg: string) {}

  public removeAttr(...attrs: ReadonlyArray<string>): SvgSanitiser {
    for (const attr of attrs) {
      this.svg = this.svg.replace(createXmlAttrRegex(attr), "");
    }

    return this;
  }

  public removeSvgAttr(...attrs: ReadonlyArray<string>): SvgSanitiser {
    const svgRegex = /<svg[^>]*>/;
    const svgRegexMatch = this.svg.match(svgRegex);
    if (!svgRegexMatch) {
      throw new Error("Invalid SVG supplied.");
    }
    let svgContent = svgRegexMatch[0];
    for (const attr of attrs) {
      svgContent = svgContent.replace(createXmlAttrRegex(attr), "");
    }
    this.svg = this.svg.replace(svgRegex, svgContent);

    return this;
  }

  public removeComments(): SvgSanitiser {
    this.svg = this.svg.replace(/<!--(.*?)-->/g, "");

    return this;
  }

  public removeUselessTags(): SvgSanitiser {
    this.svg = this.svg
      .replace(/<\?xml(.*?)\?>/g, "")
      .replace(/<!DOCTYPE(.*?)>/g, "")
      .replace(/<title>(.*?)<\/title>/g, "")
      .replace(/<desc>(.*?)<\/desc>/g, "")
      .replace(/style="enable-background:([^;]+);"/g, 'enabled-background="$1"')
      .replace(/<svg t="[^"]+"/g, "<svg")
      .replace(/class="[^"]+"/g, "");

    return this;
  }

  public refill(): SvgSanitiser {
    this.svg = this.svg
      .replace(/fill="([^"n]+)"/g, 'fill="currentColor"')
      .replace(/stroke="([^"n]+)"/g, 'stroke="currentColor"')
      .replace(/fill: ([^;n]+);/g, "fill: currentColor;")
      .replace(/stroke: *([^;n]+);/g, "stroke: currentColor;");

    return this;
  }

  public output(): string {
    return this.svg;
  }
}

const svgSanitiser = new SvgSanitiser(fs.readFileSync(origSvgPath, "utf8"));
svgSanitiser
  .removeComments()
  .removeUselessTags()
  .removeAttr("id")
  .removeSvgAttr("width", "height")
  .refill();

fs.writeFileSync(destSvgPath, svgSanitiser.output());
