import type { App } from "vue";
import PrimeVue from "primevue/config";

import "primevue/resources/themes/saga-blue/theme.css";
import "primevue/resources/primevue.css";
import "primeflex/primeflex.css";

export default function (app: App): void {
  app.use(PrimeVue);
}
