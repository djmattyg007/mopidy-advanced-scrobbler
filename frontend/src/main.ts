import { createApp } from "vue";
import router from "./router";
import store from "./store";

//import "@mdi/font/css/materialdesignicons.min.css";
import "vfonts/Lato.css";
import "./scss/app.scss";

import AppRoot from "./AppRoot.vue";

const app = createApp(AppRoot);
// TODO: remove vuex
app.use(store);
app.use(router);

app.mount("#app");
