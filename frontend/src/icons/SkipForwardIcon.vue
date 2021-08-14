<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/skip-forward.svg";

export default defineComponent({
  name: "SkipForwardIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
