<template>
  <main>
    <n-h1>Corrections</n-h1>

    <n-card :header-style="cardHeaderStyle" :content-style="cardContentStyle">
      <template #header>
        <n-element class="mas-toolbar">
          <template v-if="corrections.value && corrections.value.counts.overall >= 0">
            <span style="white-space: nowrap">
              <n-text strong>{{ corrections.value.counts.overall }}</n-text> corrections
            </span>
          </template>

          <div class="mas-spacer"></div>

          <n-button
            text
            aria-label="First Page"
            title="First Page"
            class="mas-mx1"
            :style="iconButtonStyles"
            :disabled="corrections.isRunning || isFirstPage"
            @click="goToFirstPage"
          >
            <template #icon>
              <icon-skip-backward :size="buttonIconSize" />
            </template>
          </n-button>
          <n-button
            text
            aria-label="Previous Page"
            title="Previous Page"
            class="mas-mx1"
            :style="iconButtonStyles"
            :disabled="corrections.isRunning || isFirstPage"
            @click="goToPreviousPage"
          >
            <template #icon>
              <icon-step-backward :size="buttonIconSize" />
            </template>
          </n-button>
          <n-text strong class="mas-mx2" style="font-size: 28px">{{ pageNumber }}</n-text>
          <n-button
            text
            aria-label="Next Page"
            title="Next Page"
            class="mas-mx1"
            :style="iconButtonStyles"
            :disabled="
              corrections.isRunning ||
              !corrections.value ||
              corrections.value.corrections.length < pageSize
            "
            @click="goToNextPage"
          >
            <template #icon>
              <icon-step-forward :size="buttonIconSize" />
            </template>
          </n-button>

          <div class="mas-spacer"></div>

          <n-button
            text
            aria-label="Refresh List"
            title="Refresh List"
            class="mas-ml3"
            :style="iconButtonStyles"
            :disabled="corrections.isRunning"
            @click="refresh"
          >
            <template #icon>
              <icon-refresh :size="buttonIconSize" />
            </template>
          </n-button>
        </n-element>
      </template>

      <template v-if="corrections.error">
        <n-data-table :columns="columns" :data="[]" table-layout="fixed">
          <template #empty>
            <div class="mas-px3">
              <div class="text-center mas-mb2">
                <n-text strong style="font-size: 24px"
                  >An error occurred while fetching data.</n-text
                >
              </div>
              <div>
                <n-text code>{{ corrections.error }}</n-text>
              </div>
            </div>
          </template>
        </n-data-table>
      </template>
      <n-config-provider v-else abstract :theme-overrides="dataTableThemeOverrides">
        <n-data-table
          :columns="columns"
          :data="corrections.value ? corrections.value.corrections : []"
          table-layout="fixed"
          :row-key="(row) => row.trackUri"
          :loading="corrections.isRunning"
        />
      </n-config-provider>
    </n-card>
  </main>
</template>

<script lang="ts">
import { computed, defineComponent, h, nextTick, reactive, ref, toRaw } from "vue";
import { useAsyncTask } from "vue-concurrency";
import {
  DataTableColumn,
  DialogReactive,
  DropdownOption,
  GlobalThemeOverrides,
  NButton,
  NCard,
  NConfigProvider,
  NDataTable,
  NDropdown,
  NElement,
  NH1,
  NText,
  NTooltip,
  useDialog,
  useMessage,
} from "naive-ui";

import { masHttp, mopidyHttp } from "@/http";
import { MasApi, LoadCorrectionsResponse } from "@/api/mas-api";
import { JsonRpcApi, MopidyApi } from "@/api/mopidy-api";

import { Correction, EditableCorrection } from "@/types";

import { useIsMobile, useIsTablet } from "@/utils";

import EditCorrectionForm from "@/components/EditCorrectionForm.vue";

import IconRefresh from "@/icons/RefreshIcon.vue";
import IconSkipBackward from "@/icons/SkipBackwardIcon.vue";
import IconStepBackward from "@/icons/StepBackwardIcon.vue";
import IconStepForward from "@/icons/StepForwardIcon.vue";

import SvgIconDelete from "@/svg/delete.svg";
import SvgIconEdit from "@/svg/edit.svg";

function startDialogLoading(dialog: DialogReactive): void {
  dialog.loading = true;
  dialog.closable = false;
  dialog.maskClosable = false;
  dialog.negativeText = undefined;
}

export default defineComponent({
  name: "CorrectionsView",
  components: {
    IconRefresh,
    IconSkipBackward,
    IconStepBackward,
    IconStepForward,
    NButton,
    NCard,
    NConfigProvider,
    NDataTable,
    NElement,
    NH1,
    NText,
  },
  setup() {
    const dialog = useDialog();
    const message = useMessage();

    const isMobileRef = useIsMobile();
    const isTabletRef = useIsTablet();

    const masApi = new MasApi(masHttp, message);
    const mopidyApi = new MopidyApi(new JsonRpcApi(mopidyHttp), message);

    const pageNumber = ref(1);
    const pageSize = isMobileRef.value || isTabletRef.value ? 20 : 50;
    const buttonIconSize = 34;

    const columns = computed(() => {
      const trackUriCol: DataTableColumn = {
        title: "URI",
        key: "trackUri",
        sorter: false,
        render(row) {
          const correction = row as unknown as Correction;

          let slicedTrackUri = "";
          if (isMobileRef.value && correction.trackUri.length > 20) {
            slicedTrackUri = correction.trackUri.slice(0, 20) + "...";
          } else if (isTabletRef.value && correction.trackUri.length > 25) {
            slicedTrackUri = correction.trackUri.slice(0, 25) + "...";
          } else if (correction.trackUri.length > 40) {
            slicedTrackUri = correction.trackUri.slice(0, 40) + "...";
          }

          if (slicedTrackUri) {
            return h(
              NTooltip,
              {
                trigger: "hover",
                placement: isMobileRef.value || isTabletRef.value ? "right-start" : "right",
              },
              {
                default: () => h("span", correction.trackUri),
                trigger: () => h("span", slicedTrackUri),
              },
            );
          } else {
            return h("span", correction.trackUri);
          }
        },
      };
      if (isMobileRef.value) {
        trackUriCol.width = 210;
      } else if (isTabletRef.value) {
        trackUriCol.width = 250;
      }

      const titleCol: DataTableColumn = {
        title: "Title",
        key: "title",
        sorter: false,
      };
      const artistCol: DataTableColumn = {
        title: "Artist",
        key: "artist",
        sorter: false,
      };
      const albumCol: DataTableColumn = {
        title: "Album",
        key: "album",
        sorter: false,
      };
      if (isMobileRef.value || isTabletRef.value) {
        titleCol.width = 300;
        artistCol.width = 250;
        albumCol.width = 260;
      }

      const cols: DataTableColumn[] = [
        trackUriCol,
        titleCol,
        artistCol,
        albumCol,
        {
          title: "Actions",
          key: "actions",
          sorter: false,
          align: "center",
          width: 100,
          render(row) {
            const correction = row as unknown as Correction;

            const options: DropdownOption[] = [
              { key: "edit", label: "Edit" },
              { key: "delete", label: "Delete" },
              {
                key: "playback",
                label: "Playback",
                children: [
                  { key: "playbackPlayNext", label: "Play Next" },
                  { key: "playbackAddToBottom", label: "Add to Bottom" },
                ],
              },
            ];

            return h(
              NDropdown,
              {
                "disabled": options.length === 0,
                "options": options,
                "trigger": "hover",
                "placement": "left-end",
                "on-select": (key: string) => {
                  switch (key) {
                    case "edit":
                      editCorrection(correction);
                      break;
                    case "delete":
                      deleteCorrection(correction);
                      break;
                    case "playbackPlayNext":
                      playNext(correction);
                      break;
                    case "playbackAddToBottom":
                      addToBottom(correction);
                      break;
                    default:
                      message.error("Unrecognised action.");
                      break;
                  }
                },
              },
              {
                default: () =>
                  h(
                    NButton,
                    {
                      disabled: options.length === 0,
                      size: "medium",
                    },
                    { default: () => "Menu" },
                  ),
              },
            );
          },
        },
      ];

      return cols;
    });

    const isFirstPage = computed((): boolean => pageNumber.value === 1);

    const retrieveCorrections = async (): Promise<LoadCorrectionsResponse> => {
      return masApi.loadCorrections(pageNumber.value, pageSize);
    };
    const retrieveCorrectionsTask = useAsyncTask((): ReturnType<typeof retrieveCorrections> => {
      return retrieveCorrections();
    }).drop();
    const corrections = ref(retrieveCorrectionsTask.perform());
    const loadCorrections = (): void => {
      corrections.value = retrieveCorrectionsTask.perform();
    };

    const goToNextPage = (): void => {
      pageNumber.value += 1;
      loadCorrections();
    };
    const goToPreviousPage = (): void => {
      const currentPage = pageNumber.value;
      if (currentPage === 1) {
        return;
      }

      pageNumber.value = currentPage - 1;
      loadCorrections();
    };
    const goToFirstPage = (): void => {
      pageNumber.value = 1;
      loadCorrections();
    };
    const refresh = (): void => {
      pageNumber.value = 1;
      loadCorrections();
    };

    const requestSubmitting = ref(false);

    const editCorrection = (correction: Correction): void => {
      const correctionEdit = reactive({
        trackUri: correction.trackUri,
        title: correction.title,
        artist: correction.artist,
        album: correction.album,
        updateAllUnsubmitted: true,
      } as EditableCorrection);

      const contentFunc = () => {
        return h(EditCorrectionForm, {
          "disabled": requestSubmitting.value,
          "modelValue": correctionEdit,
          "onUpdate:modelValue": (newValue: EditableCorrection) => {
            Object.assign(correctionEdit, newValue);
          },
          "onSubmitted": async () => {
            await submitFunc();
            d.destroy();
          },
        });
      };
      const submitFunc = async () => {
        startDialogLoading(d);
        requestSubmitting.value = true;
        const result = await masApi.editCorrection(toRaw(correctionEdit));
        requestSubmitting.value = false;
        if (result === false) {
          return;
        }

        if (correctionEdit.updateAllUnsubmitted === true) {
          nextTick(() => loadCorrections());
        } else {
          Object.assign(correction, {
            title: correctionEdit.title,
            artist: correctionEdit.artist,
            album: correctionEdit.album,
          });
        }
      };
      const d = dialog.info({
        title: "Edit Correction",
        icon: () => h(SvgIconEdit),
        bordered: true,
        content: contentFunc,
        negativeText: "Cancel",
        positiveText: "Save",
        onPositiveClick: () => {
          return submitFunc();
        },
        onNegativeClick: () => d.loading !== true,
        onClose: () => d.loading !== true,
      });
    };

    const deleteCorrection = (correction: Correction): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.warning({
        title: "Delete Correction",
        icon: () => h(SvgIconDelete),
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.deleteCorrection(correction.trackUri);
          requestSubmitting.value = false;
          if (result === true) {
            nextTick(() => loadCorrections());
          }
        },
        onNegativeClick() {
          if (d.loading) {
            return false;
          }
          requestSubmitting.value = false;
          return true;
        },
        onClose() {
          if (d.loading) {
            return false;
          }
          requestSubmitting.value = false;
          return true;
        },
      });
    };

    const playNext = (correction: Correction): void => {
      mopidyApi.playNext([correction.trackUri]);
    };
    const addToBottom = (correction: Correction): void => {
      mopidyApi.addToBottom([correction.trackUri]);
    };

    const cardHeaderStyle = {
      "--padding-left": "12px",
      "overflow-x": "auto",
    };
    const cardContentStyle = {
      "--padding-left": "0",
      "--padding-right": "0",
      "--padding-bottom": "0",
    };

    const iconButtonStyles = {
      "--icon-size": `${buttonIconSize}px`,
    };

    const dataTableThemeOverrides = computed((): GlobalThemeOverrides => {
      return {
        common: {
          fontSizeMedium: "16px",
        },
      };
    });

    return {
      pageNumber,
      pageSize,
      columns,
      isFirstPage,
      corrections,
      goToNextPage,
      goToPreviousPage,
      goToFirstPage,
      refresh,

      requestSubmitting,

      cardHeaderStyle,
      cardContentStyle,

      buttonIconSize,
      iconButtonStyles,

      dataTableThemeOverrides,
    };
  },
});
</script>
