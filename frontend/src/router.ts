import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import Plays from "@/views/Plays.vue";
import Corrections from "@/views/Corrections.vue";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "plays",
    component: Plays,
    alias: "/plays",
  },
  {
    path: "/corrections",
    name: "corrections",
    component: Corrections,
  },
  // {
  //   path: "/about",
  //   name: "About",
  //   // route level code-splitting
  //   // this generates a separate chunk (about.[hash].js) for this route
  //   // which is lazy-loaded when the route is visited.
  //   component: () => import(/* webpackChunkName: "about" */ "../views/About.vue"),
  // },
];

const router = createRouter({
  history: createWebHistory("/advanced_scrobbler/"),
  routes,
});

export default router;
