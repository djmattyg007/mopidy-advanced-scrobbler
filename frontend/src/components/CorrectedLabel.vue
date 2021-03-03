<template>
  <span>{{ label }}</span>
</template>

<script lang="ts">
import { defineComponent } from "vue";

import { Corrected } from "@/types";

export default defineComponent({
  name: "CorrectedLabel",
  props: {
    value: {
      type: Number,
      required: true,
    },
  },
  computed: {
    label(): string {
      switch (this.value) {
        case Corrected.NOT_CORRECTED:
          return "No";
        case Corrected.MANUALLY_CORRECTED:
          return "Manual";
        case Corrected.AUTO_CORRECTED:
          return "Auto";
        default:
          return "Unknown";
      }
    },
  },
});
</script>
