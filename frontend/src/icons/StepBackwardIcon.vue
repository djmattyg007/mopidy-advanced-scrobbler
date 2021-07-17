<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/step-backward.svg";

export default defineComponent({
  name: "StepBackwardIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
