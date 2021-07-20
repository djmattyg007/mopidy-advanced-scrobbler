<template>
  <main>
    <n-h1>Plays</n-h1>

    <n-card :header-style="cardHeaderStyle" :content-style="cardContentStyle">
      <template #header>
        <n-element class="mas-toolbar">
          <template v-if="plays.value && plays.value.counts.overall >= 0">
            <span style="white-space: nowrap">
              <n-text strong>{{ plays.value.counts.overall }}</n-text> plays (<n-text strong>{{
                plays.value.counts.unsubmitted
              }}</n-text>
              unsubmitted)
            </span>
          </template>

          <div class="mas-spacer"></div>

          <n-button
            text
            aria-label="First Page"
            title="First Page"
            class="mas-mx1"
            :style="iconButtonStyles"
            :disabled="plays.isRunning || isFirstPage"
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
            :disabled="plays.isRunning || isFirstPage"
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
            :disabled="plays.isRunning || !plays.value || plays.value.plays.length < pageSize"
            @click="goToNextPage"
          >
            <template #icon>
              <icon-step-forward :size="buttonIconSize" />
            </template>
          </n-button>

          <div class="mas-spacer"></div>

          <n-button
            text
            aria-label="Delete Selected"
            title="Delete Selected"
            class="mas-ml3"
            :style="iconButtonStyles"
            :disabled="plays.isRunning || requestSubmitting || !canDeleteMultiSelection"
            @click="deleteMultiSelected"
          >
            <template #icon>
              <icon-delete :size="buttonIconSize" />
            </template>
          </n-button>
          <n-button
            text
            aria-label="Scrobble Selected"
            title="Scrobble Selected"
            class="mas-ml3"
            :style="iconButtonStyles"
            :disabled="plays.isRunning || requestSubmitting || !canScrobbleMultiSelection"
            @click="scrobbleMultiSelected"
          >
            <template #icon>
              <icon-scrobble :size="buttonIconSize" />
            </template>
          </n-button>
          <n-button
            text
            aria-label="Scrobble Unsubmitted"
            title="Scrobble Unsubmitted"
            class="mas-ml3"
            :style="iconButtonStyles"
            :disabled="plays.isRunning || requestSubmitting"
            @click="scrobbleUnsubmitted"
          >
            <template #icon>
              <icon-scrobble-all :size="buttonIconSize" />
            </template>
          </n-button>
          <n-button
            text
            aria-label="Refresh List"
            title="Refresh List"
            class="mas-ml3"
            :style="iconButtonStyles"
            :disabled="plays.isRunning"
            @click="refresh"
          >
            <template #icon>
              <icon-refresh :size="buttonIconSize" />
            </template>
          </n-button>
        </n-element>
      </template>

      <template v-if="plays.error">
        <p>{{ plays.error }}</p>
        <n-data-table :columns="columns" :data="[]" table-layout="fixed" />
      </template>
      <n-config-provider v-else abstract :theme-overrides="dataTableThemeOverrides">
        <n-data-table
          :columns="columns"
          :data="plays.value ? plays.value.plays : []"
          table-layout="fixed"
          :row-key="(row) => row.playId"
          v-model:checked-row-keys="selectedRowKeys"
          :loading="plays.isRunning"
        />
      </n-config-provider>
    </n-card>
  </main>
</template>

<script lang="ts">
import { computed, defineComponent, h, nextTick, reactive, ref, toRaw, Ref, VNode } from "vue";
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
  NDescriptions,
  NDescriptionsItem,
  NDropdown,
  NElement,
  NH1,
  NText,
  NTooltip,
  useDialog,
  useMessage,
} from "naive-ui";

import { masHttp, mopidyHttp } from "@/http";
import { MasApi, LoadPlaysResponse, ScrobbleResponse } from "@/api/mas-api";
import { JsonRpcApi, MopidyApi } from "@/api/mopidy-api";

import { Play, Corrected, EditablePlay } from "@/types";

import { useIsMobile } from "@/utils";

import IconDelete from "@/icons/DeleteIcon.vue";
import IconRefresh from "@/icons/RefreshIcon.vue";
import IconScrobble from "@/icons/ScrobbleIcon.vue";
import IconScrobbleAll from "@/icons/ScrobbleAllIcon.vue";
import IconSkipBackward from "@/icons/SkipBackwardIcon.vue";
import IconStepBackward from "@/icons/StepBackwardIcon.vue";
import IconStepForward from "@/icons/StepForwardIcon.vue";
import IconTick from "@/icons/TickIcon.vue";

import CorrectedLabel from "@/components/CorrectedLabel.vue";
import UnixTimestamp from "@/components/UnixTimestamp.vue";
import EditPlayForm from "@/components/EditPlayForm.vue";

import SvgIconDelete from "@/svg/delete.svg";
import SvgIconEdit from "@/svg/edit.svg";
import SvgIconScrobble from "@/svg/scrobble.svg";
import SvgIconScrobbleAll from "@/svg/scrobble-all.svg";

function startDialogLoading(dialog: DialogReactive): void {
  dialog.loading = true;
  dialog.closable = false;
  dialog.maskClosable = false;
  dialog.negativeText = undefined;
}

function renderScrobbleResult(result: ScrobbleResponse): VNode {
  const children: VNode[] = [];

  children.push(
    h(NDescriptions, { labelPlacement: "top" }, () => [
      h(NDescriptionsItem, { label: "Found Plays" }, () => String(result.foundPlays.length)),
      h(NDescriptionsItem, { label: "Scrobbled Plays" }, () =>
        String(result.scrobbledPlays.length),
      ),
      h(NDescriptionsItem, { label: "Marked Plays" }, () => String(result.markedPlays.length)),
    ]),
  );

  if (result.message) {
    children.push(h("br"));
    children.push(h("p", result.message));
  }

  return h("div", children);
}

export default defineComponent({
  name: "PlaysView",
  components: {
    IconDelete,
    IconRefresh,
    IconScrobble,
    IconScrobbleAll,
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

    const masApi = new MasApi(masHttp, message);
    const mopidyApi = new MopidyApi(new JsonRpcApi(mopidyHttp), message);

    const pageNumber = ref(1);
    const pageSize = isMobileRef.value ? 20 : 50;
    const buttonIconSize = 34;

    const columns = computed(() => {
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
      if (isMobileRef.value) {
        titleCol.width = 270;
        artistCol.width = 240;
        albumCol.width = 250;
      }

      const cols: DataTableColumn[] = [
        {
          type: "selection",
        },
        {
          title: "ID",
          key: "playId",
          sorter: false,
          width: 85,
        },
        titleCol,
        artistCol,
        albumCol,
        {
          title: "Played At",
          key: "playedAt",
          sorter: false,
          width: 195,
          render(row) {
            const play = row as unknown as Play;
            return h(UnixTimestamp, { value: play.playedAt });
          },
        },
        {
          title: "Corrected",
          key: "corrected",
          sorter: false,
          width: 110,
          align: "center",
          render(row) {
            const play = row as unknown as Play;

            if (play.corrected === Corrected.NOT_CORRECTED) {
              return h(CorrectedLabel, { value: play.corrected });
            }

            return h(
              NTooltip,
              { class: "correction-info", placement: "bottom", trigger: "hover" },
              {
                trigger: () => h(CorrectedLabel, { value: play.corrected }),
                default: () => {
                  return h("dl", [
                    h("dt", "Orig. Title"),
                    h("dd", play.origTitle),
                    h("dt", "Orig. Artist"),
                    h("dd", play.origArtist),
                    h("dt", "Orig. Album"),
                    h("dd", play.origAlbum),
                  ]);
                },
              },
            );
          },
        },
        {
          title: "Submitted",
          key: "submittedAt",
          sorter: false,
          width: 100,
          align: "center",
          render(row) {
            const play = row as unknown as Play;

            const spanChildren = [];
            if (play.submittedAt) {
              spanChildren.push(h(IconTick, { color: "green", size: 20 }));
            }

            return h("span", spanChildren);
          },
        },
        {
          title: "Actions",
          key: "actions",
          sorter: false,
          align: "center",
          width: 100,
          render(row) {
            const play = row as unknown as Play;

            const options: DropdownOption[] = [];
            if (!play.submittedAt) {
              options.push(
                { key: "edit", label: "Edit" },
                { key: "submit", label: "Submit" },
                { key: "delete", label: "Delete" },
                { key: "scrobbleToHere", label: "Scrobble To Here" },
              );
            }
            if (play.corrected === Corrected.AUTO_CORRECTED) {
              options.splice(1, 0, {
                key: "approveAutoCorrection",
                label: "Approve Auto-Correction",
              });
            }

            options.push({
              key: "playback",
              label: "Playback",
              children: [
                { key: "playbackPlayNext", label: "Play Next" },
                { key: "playbackAddToBottom", label: "Add to Bottom" },
              ],
            });

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
                      editPlay(play);
                      break;
                    case "approveAutoCorrection":
                      approveAutoCorrection(play);
                      break;
                    case "submit":
                      submitPlay(play);
                      break;
                    case "delete":
                      deletePlay(play);
                      break;
                    case "scrobbleToHere":
                      scrobbleToCheckpoint(play);
                      break;
                    case "playbackPlayNext":
                      playNext(play);
                      break;
                    case "playbackAddToBottom":
                      addToBottom(play);
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
    const selectedRowKeys = ref([]) as Ref<number[]>;

    const retrievePlays = async (): Promise<LoadPlaysResponse> => {
      return masApi.loadPlays(pageNumber.value, pageSize);
    };
    const retrievePlaysTask = useAsyncTask((): ReturnType<typeof retrievePlays> => {
      return retrievePlays();
    }).drop();
    const plays = ref(retrievePlaysTask.perform());
    const loadPlays = (): void => {
      selectedRowKeys.value = [];
      plays.value = retrievePlaysTask.perform();
    };

    const playsMultiSelected = computed((): boolean => selectedRowKeys.value.length > 0);
    const multiSelectPlays = computed((): ReadonlyArray<Play> => {
      const playsData = plays.value.value;
      if (!playsData) {
        return [];
      }

      const selectedPlays: Play[] = [];

      for (const selectedRowKey of selectedRowKeys.value) {
        const pos = playsData.playIdMapping[selectedRowKey];
        selectedPlays.push(playsData.plays[pos]);
      }

      return selectedPlays;
    });
    const canDeleteMultiSelection = computed(
      (): boolean =>
        playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt),
    );
    const canScrobbleMultiSelection = computed(
      (): boolean =>
        playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt),
    );
    const playsMultiSelectedCountLabel = computed((): string => {
      const count = selectedRowKeys.value.length;
      if (count === 1) {
        return `${count} play`;
      } else {
        return `${count} plays`;
      }
    });

    const goToNextPage = (): void => {
      pageNumber.value += 1;
      loadPlays();
    };
    const goToPreviousPage = (): void => {
      const currentPage = pageNumber.value;
      if (currentPage === 1) {
        return;
      }

      pageNumber.value = currentPage - 1;
      loadPlays();
    };
    const goToFirstPage = (): void => {
      pageNumber.value = 1;
      loadPlays();
    };
    const refresh = (): void => {
      pageNumber.value = 1;
      loadPlays();
    };

    const requestSubmitting = ref(false);

    const editPlay = (play: Play): void => {
      const playEdit = reactive({
        playId: play.playId,
        trackUri: play.trackUri,
        title: play.title,
        artist: play.artist,
        album: play.album,
        saveCorrection: true,
        updateAllUnsubmitted: true,
      } as EditablePlay);

      const contentFunc = () => {
        return h(EditPlayForm, {
          "disabled": requestSubmitting.value,
          "modelValue": playEdit,
          "onUpdate:modelValue": (newValue: EditablePlay) => {
            Object.assign(playEdit, newValue);
          },
        });
      };
      const d = dialog.info({
        title: "Edit Play",
        icon: () => h(SvgIconEdit),
        bordered: true,
        content: contentFunc,
        negativeText: "Cancel",
        positiveText: "Save",
        onPositiveClick: async () => {
          startDialogLoading(d);
          requestSubmitting.value = true;
          const result = await masApi.editPlay(toRaw(playEdit));
          requestSubmitting.value = false;
          if (result === false) {
            return;
          }

          if (playEdit.updateAllUnsubmitted === true) {
            nextTick(() => loadPlays());
          } else {
            Object.assign(play, {
              title: playEdit.title,
              artist: playEdit.artist,
              album: playEdit.album,
              corrected: Corrected.MANUALLY_CORRECTED,
            });
          }
        },
        onNegativeClick: () => d.loading === false,
        onClose: () => () => d.loading === false,
      });
    };

    const approveAutoCorrection = (play: Play): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.success({
        title: "Approve Auto-Correction",
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.approveAutoCorrection(play.playId);
          requestSubmitting.value = false;
          if (result === true) {
            Object.assign(play, {
              corrected: Corrected.MANUALLY_CORRECTED,
            });
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

    const deletePlay = (play: Play): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.warning({
        title: "Delete Play",
        icon: () => h(SvgIconDelete),
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.submitDelete(play.playId);
          requestSubmitting.value = false;
          if (result === true) {
            nextTick(() => loadPlays());
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

    const submitPlay = (play: Play): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.success({
        title: "Submit Play",
        icon: () => h(SvgIconScrobble),
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.submitSinglePlay(play.playId);
          requestSubmitting.value = false;
          if (result === true) {
            Object.assign(play, {
              submittedAt: Math.floor(Date.now() / 1000),
            });
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

    const scrobbleToCheckpoint = (play: Play): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.success({
        title: "Scrobble",
        icon: () => h(SvgIconScrobbleAll),
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.scrobbleUnsubmitted(play.playId);
          requestSubmitting.value = false;
          if (result === null) {
            return;
          }

          nextTick(() => {
            dialog.info({
              title: "Success",
              bordered: true,
              content: () => renderScrobbleResult(result),
              positiveText: "Close",
            });

            nextTick(() => loadPlays());
          });
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

    const scrobbleUnsubmitted = (): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      }

      requestSubmitting.value = true;

      const d = dialog.success({
        title: "Scrobble",
        icon: () => h(SvgIconScrobbleAll),
        bordered: true,
        content: "Are you sure?",
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.scrobbleUnsubmitted();
          requestSubmitting.value = false;
          if (result === null) {
            return;
          }

          nextTick(() => {
            dialog.info({
              title: "Success",
              bordered: true,
              content: () => renderScrobbleResult(result),
              positiveText: "Close",
            });

            nextTick(() => refresh());
          });
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

    const deleteMultiSelected = (): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      } else if (canDeleteMultiSelection.value !== true) {
        message.error("Invalid plays selection.");
        return;
      }

      requestSubmitting.value = true;
      const selectedPlayIds = selectedRowKeys.value.slice();

      const d = dialog.warning({
        title: "Delete Plays",
        icon: () => h(SvgIconDelete),
        bordered: true,
        content: `Are you sure you want to delete ${playsMultiSelectedCountLabel.value}?`,
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.submitMultiDelete(selectedPlayIds);
          requestSubmitting.value = false;
          if (result === true) {
            nextTick(() => loadPlays());
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

    const scrobbleMultiSelected = (): void => {
      if (requestSubmitting.value === true) {
        message.error("A request is already pending.");
        return;
      } else if (canScrobbleMultiSelection.value !== true) {
        message.error("Invalid plays selection.");
        return;
      }

      requestSubmitting.value = true;
      const selectedPlayIds = selectedRowKeys.value.slice();

      const d = dialog.success({
        title: "Scrobble Plays",
        icon: () => h(SvgIconScrobble),
        bordered: true,
        content: `Are you sure you want to scrobble ${playsMultiSelectedCountLabel.value}?`,
        negativeText: "Cancel",
        positiveText: "Confirm",
        onPositiveClick: async () => {
          startDialogLoading(d);
          const result = await masApi.submitMultiScrobble(selectedPlayIds);
          requestSubmitting.value = false;
          if (result === null) {
            return;
          }

          nextTick(() => {
            dialog.info({
              title: "Success",
              bordered: true,
              content: () => renderScrobbleResult(result),
              positiveText: "Close",
            });

            nextTick(() => loadPlays());
          });
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

    const playNext = (play: Play): void => {
      mopidyApi.playNext([play.trackUri]);
    };
    const addToBottom = (play: Play): void => {
      mopidyApi.addToBottom([play.trackUri]);
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
      selectedRowKeys,
      plays,
      playsMultiSelected,
      multiSelectPlays,
      canDeleteMultiSelection,
      canScrobbleMultiSelection,
      playsMultiSelectedCountLabel,
      goToNextPage,
      goToPreviousPage,
      goToFirstPage,
      refresh,
      scrobbleUnsubmitted,
      deleteMultiSelected,
      scrobbleMultiSelected,

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
