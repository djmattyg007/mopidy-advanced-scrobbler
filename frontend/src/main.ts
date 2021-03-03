import { createApp } from "vue";
import router from "./router";
import store from "./store";

import App from "./App.vue";

import waveUiConfigurator from "./waveui";

import "@mdi/font/css/materialdesignicons.min.css";
import "./scss/app.scss";

const app = createApp(App);
app.use(store);
app.use(router);
waveUiConfigurator(app);

app.mount("#app");
