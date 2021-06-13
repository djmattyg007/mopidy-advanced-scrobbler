<template>
  <div class="root-container">
    <n-layout>
      <n-layout-header bordered class="nav" :style="headerStyle">
        <n-text class="app-title">Advanced Scrobbler</n-text>
        <n-space class="mas-spacer" justify="end">
          <app-toolbar />
        </n-space>
      </n-layout-header>
      <n-layout-content :content-style="layoutContentStyle">
        <div class="content-wrap mas-flex mas-flex-no-shrink" :style="contentWrapStyle">
          <div class="main-content mas-flex mas-flex-column">
            <router-view />
          </div>
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent } from "vue";
import { NLayout, NLayoutContent, NLayoutHeader, NSpace, NText } from "naive-ui";

import { useIsMobile } from "@/utils";

import AppToolbar from "@/components/AppToolbar.vue";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
    NLayout,
    NLayoutContent,
    NLayoutHeader,
    NSpace,
    NText,
  },
  setup() {
    const isMobileRef = useIsMobile();

    const layoutContentStyle = {
      "display": "flex",
      "flex-direction": "column",
    };

    const paddingStyle = computed(() => {
      if (isMobileRef.value) {
        return {
          "--side-padding": "16px",
        };
      } else {
        return {
          "--side-padding": "32px",
        };
      }
    });

    return {
      headerStyle: paddingStyle,
      contentWrapStyle: paddingStyle,
      layoutContentStyle,
    };
  },
});
</script>

<style scoped>
.nav {
  display: flex;
  padding: 6px var(--side-padding) 0;
  background-color: rgb(227, 242, 253);
}
.app-title {
  font-size: 22px;
  font-weight: var(--font-weight-strong);
}
</style>
