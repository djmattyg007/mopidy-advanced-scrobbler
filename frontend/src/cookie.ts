import { App } from "vue";
import { VueCookieNext } from "vue-cookie-next";

export function initCookie(app: App): void {
  VueCookieNext.config({
    expire: "14d",
    path: "/advanced_scrobbler/",
  });

  app.use(VueCookieNext);
}
