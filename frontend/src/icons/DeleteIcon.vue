<template>
  <n-icon>
    <svg-icon />
  </n-icon>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { NIcon } from "naive-ui";

import SvgIcon from "@/svg/delete.svg";

export default defineComponent({
  name: "DeleteIcon",
  components: {
    NIcon,
    SvgIcon,
  },
});
</script>
