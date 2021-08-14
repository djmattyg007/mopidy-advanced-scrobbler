<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/pause.svg";

export default defineComponent({
  name: "PauseIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
