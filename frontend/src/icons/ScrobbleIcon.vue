<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/scrobble.svg";

export default defineComponent({
  name: "ScrobbleIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
