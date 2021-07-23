<template>
  <n-config-provider
    :theme="actualTheme"
    :theme-overrides="themeOverrides"
    namespace="advanced-scrobbler"
  >
    <n-message-provider>
      <n-dialog-provider>
        <App :selected-theme="selectedTheme" @theme-selected="handleThemeChange" />
      </n-dialog-provider>
    </n-message-provider>
    <n-global-style />
  </n-config-provider>
</template>

<script lang="ts">
import { computed, defineComponent, ref, Ref } from "vue";
import { useOsTheme, darkTheme } from "naive-ui";
import {
  GlobalThemeOverrides,
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NMessageProvider,
} from "naive-ui";

import App from "./App.vue";

import type { SelectedTheme } from "@/types";

export default defineComponent({
  name: "AppRoot",
  components: {
    App,
    NConfigProvider,
    NDialogProvider,
    NGlobalStyle,
    NMessageProvider,
  },
  setup() {
    const osThemeRef = useOsTheme();
    const selectedTheme = ref("os-theme") as Ref<SelectedTheme>;
    const handleThemeChange = (newTheme: SelectedTheme): void => {
      selectedTheme.value = newTheme;
    };

    const actualTheme = computed(() => {
      switch (selectedTheme.value) {
        case "dark":
          return darkTheme;
        case "light":
          return null;
        case "os-theme":
        default:
          return osThemeRef.value === "dark" ? darkTheme : null;
      }
    });
    const themeOverrides = computed((): GlobalThemeOverrides => {
      return {
        common: {
          fontWeightStrong: "700",
        },
      };
    });

    return {
      selectedTheme,
      handleThemeChange,
      actualTheme,
      themeOverrides,
    };
  },
});
</script>
