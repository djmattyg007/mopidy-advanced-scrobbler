<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/scrobble-all.svg";

export default defineComponent({
  name: "ScrobbleAllIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
