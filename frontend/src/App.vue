<template>
  <div :class="rootContainerClass">
    <n-layout>
      <n-layout-header bordered class="nav" :style="headerStyle">
        <n-text class="app-title">Advanced Scrobbler</n-text>
        <n-space class="mas-spacer" justify="end">
          <n-popover trigger="click" placement="bottom-end" :style="nowPlayingPopoverStyle">
            <template #trigger>
              <n-button style="--height: 90%">
                <template #icon>
                  <music-icon />
                </template>
              </n-button>
            </template>

            <now-playing-panel :style="nowPlayingPanelStyle" />
          </n-popover>
          <n-dropdown trigger="click" :options="themeDropdownOptions" @select="handleThemeSelect">
            <n-button style="--height: 90%">
              <template v-if="selectedTheme === 'os-theme'" #icon>
                <theme-auto-icon />
              </template>
              <template v-else-if="selectedTheme === 'light'" #icon>
                <theme-light-icon />
              </template>
              <template v-else-if="selectedTheme === 'dark'" #icon>
                <theme-dark-icon />
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
  NPopover,
  NSpace,
  NText,
} from "naive-ui";

import { mopidyState, MopidyConnectionState } from "@/mopidy";
import { useIsMobile } from "@/utils";

import AppToolbar from "@/components/AppToolbar.vue";
import NowPlayingPanel from "@/components/NowPlayingPanel.vue";

import MusicIcon from "@/icons/MusicIcon.vue";
import ThemeAutoIcon from "@/icons/ThemeAutoIcon.vue";
import ThemeDarkIcon from "@/icons/ThemeDarkIcon.vue";
import ThemeLightIcon from "@/icons/ThemeLightIcon.vue";

import type { SelectedTheme, ActualTheme } from "@/types";

export default defineComponent({
  name: "App",
  components: {
    AppToolbar,
    MusicIcon,
    NowPlayingPanel,
    NButton,
    NDropdown,
    NLayout,
    NLayoutContent,
    NLayoutHeader,
    NPopover,
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
    },
    actualThemeName: {
      type: String as PropType<ActualTheme>,
      required: true,
    },
  },
  emits: ["theme-selected"],
  setup(props, { emit }) {
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
      { key: "light", label: "Light" },
      { key: "dark", label: "Dark" },
    ];
    const handleThemeSelect = (key: SelectedTheme): void => {
      emit("theme-selected", key);
    };

    const rootContainerClass = computed(() => {
      const classes = ["root-container"];
      switch (props.actualThemeName) {
        case "light":
          classes.push("app-theme-light");
          break;
        case "dark":
          classes.push("app-theme-dark");
          break;
        default:
          throw new Error("Unrecognised theme selected.");
      }
      return classes;
    });

    const nowPlayingPopoverStyle = computed(() => {
      let borderColor: string;
      switch (mopidyState.online) {
        case MopidyConnectionState.OFFLINE:
          borderColor = "#ff3d00";
          break;
        case MopidyConnectionState.RECONNECTING:
          borderColor = "#ffc107";
          break;
        default:
          borderColor = "transparent";
          break;
      }

      return { border: `2px solid ${borderColor}` };
    });
    const nowPlayingPanelStyle = computed(() => {
      return {
        "max-width": isMobileRef.value ? "260px" : "320px",
      };
    });

    return {
      headerStyle: paddingStyle,
      contentWrapStyle: paddingStyle,
      layoutContentStyle,
      themeDropdownOptions,
      handleThemeSelect,
      rootContainerClass,
      nowPlayingPopoverStyle,
      nowPlayingPanelStyle,
    };
  },
});
</script>

<style scoped lang="scss">
.nav {
  display: flex;
  padding: 6px var(--side-padding) 0;

  .app-theme-light & {
    background-color: #e8ecef;
  }

  .app-theme-dark & {
    background-color: #465158;
  }
}

.app-title {
  font-size: 22px;
  font-weight: var(--font-weight-strong);
}
</style>
