<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";
//import { Icon } from "@vicons/utils";

import SvgIcon from "@/svg/refresh.svg";

export default defineComponent({
  name: "RefreshIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
