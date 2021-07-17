<template>
  <n-menu mode="horizontal" :options="menuOptions" :render-label="renderMenuLabel" />
</template>

<script lang="ts">
import { defineComponent, h } from "vue";
import { NMenu, MenuOption } from "naive-ui";
import { RouterLink } from "vue-router";

export default defineComponent({
  name: "AppToolbar",
  components: { NMenu },
  setup() {
    const menuOptions: MenuOption[] = [
      {
        label: "Plays",
        key: "plays",
      },
      {
        label: "Corrections",
        key: "corrections",
        disabled: true,
      },
    ];

    const renderMenuLabel = (option: MenuOption) => {
      return h(RouterLink, { to: option.key as string }, { default: () => option.label as string });
    };

    return { menuOptions, renderMenuLabel };
  },
});
</script>
