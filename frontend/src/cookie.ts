import { inject, App } from "vue";
import { VueCookieNext } from "vue-cookie-next";

export function initCookie(app: App): void {
  VueCookieNext.config({
    expire: "14d",
    path: "/advanced_scrobbler/",
  });

  app.use(VueCookieNext);
  app.provide("cookie", VueCookieNext);
}

export function useCookie(): typeof VueCookieNext {
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return inject("cookie")!;
}
