<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/skip-backward.svg";

export default defineComponent({
  name: "SkipBackwardIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
