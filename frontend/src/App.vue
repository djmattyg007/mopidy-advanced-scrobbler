<template>
  <w-app>
    <header class="no-shrink">
      <app-toolbar />
    </header>
    <div class="content-wrap w-flex no-shrink">
      <div class="main-content w-flex column grow">
        <router-view class="grow" />
      </div>
    </div>
  </w-app>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import "wave-ui/dist/wave-ui.css";

import AppToolbar from "@/components/AppToolbar.vue";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
  },
});
</script>
