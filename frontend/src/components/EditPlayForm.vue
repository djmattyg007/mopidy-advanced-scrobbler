<template>
  <n-form :model="formValue">
    <n-form-item label="Title" path="title">
      <n-input v-model:value="formValue.title" :disabled="disabled" />
    </n-form-item>
    <n-form-item label="Artist" path="artist">
      <n-input v-model:value="formValue.artist" :disabled="disabled" />
    </n-form-item>
    <n-form-item label="Album" path="album">
      <n-input v-model:value="formValue.album" :disabled="disabled" />
    </n-form-item>
    <n-checkbox v-model:checked="formValue.saveCorrection" :disabled="disabled"
      >Save as Correction</n-checkbox
    >
    <n-checkbox v-model:checked="formValue.updateAllUnsubmitted" :disabled="disabled"
      >Update All Unsubmitted Plays</n-checkbox
    >
  </n-form>
</template>

<script lang="ts">
import { defineComponent, reactive, watch, PropType } from "vue";
import { NCheckbox, NForm, NFormItem, NInput } from "naive-ui";

import type { EditablePlay } from "@/types";

export default defineComponent({
  name: "EditPlayForm",
  components: {
    NCheckbox,
    NForm,
    NFormItem,
    NInput,
  },
  props: {
    modelValue: {
      type: Object as PropType<EditablePlay>,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    }
  },
  emits: ["update:modelValue"],
  setup(props, { emit }) {
    const formValue = reactive(Object.assign({}, props.modelValue));
    watch(
      () => formValue,
      (newValue: EditablePlay): void => {
        emit("update:modelValue", newValue);
      },
      { deep: true },
    );

    return { formValue };
  },
});
</script>
