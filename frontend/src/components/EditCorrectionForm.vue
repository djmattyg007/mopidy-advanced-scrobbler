<template>
  <n-form :model="formValue" :id="formId" :on-submit="handleFormSubmit">
    <n-form-item label="Title" path="title">
      <n-input v-model:value="formValue.title" :disabled="disabled" />
    </n-form-item>
    <n-form-item label="Artist" path="artist">
      <n-input v-model:value="formValue.artist" :disabled="disabled" />
    </n-form-item>
    <n-form-item label="Album" path="album">
      <n-input v-model:value="formValue.album" :disabled="disabled" />
    </n-form-item>
    <n-checkbox v-model:checked="formValue.updateAllUnsubmitted" :disabled="disabled"
      >Update All Unsubmitted Plays</n-checkbox
    >

    <!-- Make submission with enter work correctly -->
    <input
      type="submit"
      style="position: absolute; left: -9999px; width: 1px; height: 1px"
      tabindex="-1"
    />
  </n-form>
</template>

<script lang="ts">
import { defineComponent, reactive, watch, PropType } from "vue";
import { NCheckbox, NForm, NFormItem, NInput } from "naive-ui";

import type { EditableCorrection } from "@/types";

export default defineComponent({
  name: "EditCorrectionForm",
  components: {
    NCheckbox,
    NForm,
    NFormItem,
    NInput,
  },
  props: {
    modelValue: {
      type: Object as PropType<EditableCorrection>,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    formId: {
      type: String,
      default: "form-edit-play",
    },
  },
  emits: ["update:modelValue", "submitted"],
  setup(props, { emit }) {
    const formValue = reactive(Object.assign({}, props.modelValue));
    watch(
      () => formValue,
      (newValue: EditableCorrection): void => {
        emit("update:modelValue", newValue);
      },
      { deep: true },
    );

    const handleFormSubmit = (e: Event): void => {
      e.preventDefault();
      emit("submitted", e);
    };

    return { formValue, handleFormSubmit };
  },
});
</script>
