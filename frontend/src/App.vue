<template>
  <n-layout>
    <n-layout-header bordered>
      <div>Advanced Scrobbler</div>
      <n-space justify="end">
        <app-toolbar />
      </n-space>
    </n-layout-header>
    <n-layout>
      <router-view />
    </n-layout>
  </n-layout>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NLayout, NLayoutHeader, NSpace } from "naive-ui";

import AppToolbar from "@/components/AppToolbar.vue";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
    NLayout,
    NLayoutHeader,
    NSpace,
  },
});
</script>
