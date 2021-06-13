<template>
  <div class="root-container">
    <n-layout>
      <n-layout-header bordered>
        <div>Advanced Scrobbler</div>
        <n-space justify="end">
          <app-toolbar />
        </n-space>
      </n-layout-header>
      <n-layout-content :content-style="layoutContentStyle">
        <div class="content-wrap mas-flex mas-flex-no-shrink">
          <div class="main-content mas-flex mas-flex-column">
            <router-view />
          </div>
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NLayout, NLayoutContent, NLayoutHeader, NSpace } from "naive-ui";

import AppToolbar from "@/components/AppToolbar.vue";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
    NLayout,
    NLayoutContent,
    NLayoutHeader,
    NSpace,
  },
  setup() {
    const layoutContentStyle = {
      "display": "flex",
      "flex-direction": "column",
    };

    return { layoutContentStyle };
  },
});
</script>
