import { createApp } from "vue";
import router from "./router";
import store from "./store";

import App from "./App.vue";

import waveUiConfigurator from "./waveui";

const app = createApp(App);
app.use(store);
app.use(router);
waveUiConfigurator(app);

app.mount("#app");
