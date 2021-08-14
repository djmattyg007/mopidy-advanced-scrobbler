import { createApp } from "vue";
import router from "./router";
import { initCookie } from "./cookie";

//import "@mdi/font/css/materialdesignicons.min.css";
import "vfonts/Lato.css";
import "./scss/app.scss";

import AppRoot from "./AppRoot.vue";

const app = createApp(AppRoot);
app.use(router);

initCookie(app);

app.mount("#app");
