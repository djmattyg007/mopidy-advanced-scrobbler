<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/tick.svg";

export default defineComponent({
  name: "TickIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
