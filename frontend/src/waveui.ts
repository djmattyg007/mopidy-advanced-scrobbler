import type { App } from "vue";
import WaveUI from "wave-ui";
//import "wave-ui/dist/wave-ui.css";
//import "../node_modules/wave-ui/dist/wave-ui.css";
//import "wave-ui/src/wave-ui/scss/index.scss";

export default function (app: App): WaveUI {
  return new WaveUI(app);
}
