<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/theme-auto.svg";

export default defineComponent({
  name: "ThemeAutoIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
