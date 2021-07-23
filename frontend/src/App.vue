<template>
  <div class="root-container">
    <n-layout>
      <n-layout-header bordered class="nav" :style="headerStyle">
        <n-text class="app-title">Advanced Scrobbler</n-text>
        <n-space class="mas-spacer" justify="end">
          <n-dropdown trigger="click" :options="themeDropdownOptions" @select="handleThemeSelect">
            <n-button>
              <template v-if="selectedTheme === 'os-theme'" #icon>
                <theme-auto-icon />
              </template>
              <template v-else-if="selectedTheme === 'dark'" #icon>
                <theme-dark-icon />
              </template>
              <template v-else-if="selectedTheme === 'light'" #icon>
                <theme-light-icon />
              </template>
            </n-button>
          </n-dropdown>
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
import { computed, defineComponent, PropType } from "vue";
import {
  NButton,
  NDropdown,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NSpace,
  NText,
} from "naive-ui";

import { useIsMobile } from "@/utils";

import AppToolbar from "@/components/AppToolbar.vue";

import ThemeAutoIcon from "@/icons/ThemeAutoIcon.vue";
import ThemeDarkIcon from "@/icons/ThemeDarkIcon.vue";
import ThemeLightIcon from "@/icons/ThemeLightIcon.vue";

import type { SelectedTheme } from "@/types";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
    NButton,
    NDropdown,
    NLayout,
    NLayoutContent,
    NLayoutHeader,
    NSpace,
    NText,
    ThemeAutoIcon,
    ThemeDarkIcon,
    ThemeLightIcon,
  },
  props: {
    selectedTheme: {
      type: String as PropType<SelectedTheme>,
      required: true,
    }
  },
  emits: ["theme-selected"],
  setup(_props, { emit }) {
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

    const themeDropdownOptions = [
      { key: "os-theme", label: "Auto" },
      { key: "dark", label: "Dark" },
      { key: "light", label: "Light" },
    ];
    const handleThemeSelect = (key: SelectedTheme): void => {
      emit("theme-selected", key);
    };

    return {
      headerStyle: paddingStyle,
      contentWrapStyle: paddingStyle,
      layoutContentStyle,
      themeDropdownOptions,
      handleThemeSelect,
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
