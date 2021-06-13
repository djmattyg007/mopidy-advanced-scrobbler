<template>
  <n-menu mode="horizontal" :options="menuOptions" />
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NMenu, MenuOption } from "naive-ui";

export default defineComponent({
  name: "AppToolbar",
  components: { NMenu },
  setup() {
    const menuOptions: MenuOption[] = [
      {
        label: "Plays",
        key: "plays",
        //urlPath: "/plays",
      },
      {
        label: "Corrections",
        key: "corrections",
        disabled: true,
        //urlPath: "/corrections",
      },
    ];

    return { menuOptions };
  },
});
</script>
