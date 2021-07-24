<template>
  <n-config-provider
    :theme="actualTheme"
    :theme-overrides="themeOverrides"
    namespace="advanced-scrobbler"
  >
    <n-message-provider>
      <n-dialog-provider>
        <App
          :selected-theme="selectedTheme"
          :actual-theme-name="actualThemeName"
          @theme-selected="handleThemeChange"
        />
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

import { useCookie } from "@/cookie";

import { sanitiseSelectedTheme, ActualTheme, SelectedTheme } from "@/types";

const SelectedThemeCookieName = "selectedTheme";

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
    const cookie = useCookie();

    const preselectedTheme = cookie.getCookie(SelectedThemeCookieName);
    const selectedTheme = ref(sanitiseSelectedTheme(preselectedTheme)) as Ref<SelectedTheme>;
    const handleThemeChange = (newTheme: SelectedTheme): void => {
      newTheme = sanitiseSelectedTheme(newTheme);
      selectedTheme.value = newTheme;
      cookie.setCookie(SelectedThemeCookieName, newTheme);
    };

    const osThemeRef = useOsTheme();
    const actualThemeName = computed((): ActualTheme => {
      switch (selectedTheme.value) {
        case "dark":
        case "light":
          return selectedTheme.value;
        case "os-theme":
        default:
          return osThemeRef.value === "dark" ? "dark" : "light";
      }
    });
    const actualTheme = computed(() => {
      if (actualThemeName.value === "light") {
        return null;
      } else if (actualThemeName.value === "dark") {
        return darkTheme;
      } else {
        throw new Error("Unrecognised theme selected.");
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
      actualThemeName,
      actualTheme,
      themeOverrides,
    };
  },
});
</script>
