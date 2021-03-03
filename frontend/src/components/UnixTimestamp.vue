<template>
  <span>{{ label }}</span>
</template>

<script lang="ts">
import { defineComponent } from "vue";

import { DateTime } from "luxon";

export default defineComponent({
  name: "UnixTimestamp",
  props: {
    value: {
      type: Number,
      required: true,
    },
  },
  computed: {
    label(): string {
      const dtUtc = DateTime.fromSeconds(this.value, { zone: "UTC" });
      const dtLocal = dtUtc.toLocal();
      return dtLocal.toLocaleString(DateTime.DATETIME_MED);
    },
  },
});
</script>
