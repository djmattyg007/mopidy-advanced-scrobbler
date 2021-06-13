import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import Plays from "@/views/PlaysNaive.vue";
//import Corrections from "@/views/Corrections.vue";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "plays",
    component: Plays,
    alias: "/plays",
  },
  /*{
    path: "/corrections",
    name: "corrections",
    component: Corrections,
  },*/
];

const router = createRouter({
  history: createWebHistory("/advanced_scrobbler/"),
  routes,
});

export default router;
