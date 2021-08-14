<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/play.svg";

export default defineComponent({
  name: "PlayIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
