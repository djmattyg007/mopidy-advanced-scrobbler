<template>
  <n-config-provider
    :theme="theme"
    :theme-overrides="themeOverrides"
    namespace="advanced-scrobbler"
  >
    <n-message-provider>
      <n-dialog-provider>
        <App />
      </n-dialog-provider>
    </n-message-provider>
    <n-global-style />
  </n-config-provider>
</template>

<script lang="ts">
import { computed, defineComponent } from "vue";
import { useOsTheme, darkTheme } from "naive-ui";
import {
  GlobalThemeOverrides,
  NConfigProvider,
  NDialogProvider,
  NGlobalStyle,
  NMessageProvider,
} from "naive-ui";

import App from "./App.vue";

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

    const theme = computed(() => (osThemeRef.value === "dark" ? darkTheme : null));
    const themeOverrides = computed((): GlobalThemeOverrides => {
      return {
        common: {
          fontWeightStrong: "700",
        },
      };
    });

    return {
      theme,
      themeOverrides,
      osTheme: osThemeRef,
    };
  },
});
</script>
