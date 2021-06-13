<template>
  <main>
    <n-h1>Plays</n-h1>

    <n-card :header-style="cardHeaderStyle" :content-style="cardContentStyle">
      <template #header>
        <n-element class="mas-toolbar">
          <span v-if="plays.value && plays.value.counts.overall >= 0">
            <n-text strong>{{ plays.value.counts.overall }}</n-text> plays (<n-text strong>{{
              plays.value.counts.unsubmitted
            }}</n-text>
            unsubmitted)
          </span>

          <div class="mas-spacer"></div>

          <n-button
            text
            aria-label="First Page"
            title="First Page"
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
            :style="iconButtonStyles"
            :disabled="plays.isRunning || isFirstPage"
            @click="goToPreviousPage"
          >
            <template #icon>
              <icon-step-backward :size="buttonIconSize" />
            </template>
          </n-button>
          <n-text strong>{{ pageNumber }}</n-text>
          <n-button
            text
            aria-label="Next Page"
            title="Next Page"
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
            :style="iconButtonStyles"
            :disabled="plays.isRunning || deleteRequestSubmitting || !canDeleteMultiSelection"
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
            :style="iconButtonStyles"
            :disabled="plays.isRunning || scrobbleRequestSubmitting || !canScrobbleMultiSelection"
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
            :style="iconButtonStyles"
            :disabled="plays.isRunning || scrobbleRequestSubmitting"
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
      <n-data-table
        v-else
        :columns="columns"
        :data="plays.value ? plays.value.plays : []"
        table-layout="fixed"
        :row-key="(row) => row.playId"
        v-model:checked-row-keys="selectedRowKeys"
        :loading="plays.isRunning"
      />
    </n-card>
  </main>
</template>

<script lang="ts">
import { computed, defineComponent, h, ref, Ref } from "vue";
import { useAsyncTask } from "vue-concurrency";
import {
  DataTableColumn,
  NButton,
  NCard,
  NDataTable,
  NElement,
  NH1,
  NText,
  NTooltip,
} from "naive-ui";

import { api } from "@/api";

import { Play, Corrected } from "@/types";

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

interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
  readonly playIdMapping: Record<Play["playId"], number>;
  readonly counts: {
    readonly overall: number;
    readonly unsubmitted: number;
  };
}

/*interface ScrobbleResponse {
  readonly success: boolean;
  readonly foundPlays: ReadonlyArray<number>;
  readonly scrobbledPlays: ReadonlyArray<number>;
  readonly markedPlays: ReadonlyArray<number>;
  readonly message: string | null;
}*/

interface EditablePlay {
  readonly playId: number;
  readonly trackUri: string;
  title: string;
  artist: string;
  album: string;
  saveCorrection: boolean;
  updateAllUnsubmitted: boolean;
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
    NDataTable,
    NElement,
    NH1,
    NText,
  },
  setup() {
    const pageNumber = ref(1);
    const pageSize = 50;
    const buttonIconSize = 34;

    const selectedPlay = ref(null) as Ref<Play | null>;
    const playEdit = ref(null) as Ref<EditablePlay | null>;

    const columns = computed(() => {
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
        {
          title: "Title",
          key: "title",
          sorter: false,
        },
        {
          title: "Artist",
          key: "artist",
          sorter: false,
        },
        {
          title: "Album",
          key: "album",
          sorter: false,
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
              { placement: "bottom", trigger: "hover" },
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
          title: "Played At",
          key: "playedAt",
          sorter: false,
          width: 175,
          render(row) {
            const play = row as unknown as Play;
            return h(UnixTimestamp, { value: play.playedAt });
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
          align: "right",
        },
      ];

      return cols;
    });

    const isFirstPage = computed((): boolean => pageNumber.value === 1);
    const selectedRowKeys = ref([]) as Ref<number[]>;

    const retrievePlays = async (): Promise<LoadPlaysResponse> => {
      const response = await api.get<LoadPlaysResponse>("/plays/load", {
        params: {
          page: pageNumber.value,
          page_size: pageSize,
        },
      });
      return response.data;
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

    const editPlay = (play: Play): void => {
      selectedPlay.value = play;
      playEdit.value = {
        playId: play.playId,
        trackUri: play.trackUri,
        title: play.title,
        artist: play.artist,
        album: play.album,
        saveCorrection: true,
        updateAllUnsubmitted: true,
      };
      //dialogShow.edit = true;
    };
    const approveAutoCorrection = (play: Play): void => {
      selectedPlay.value = play;
      //dialogShow.approveAutoCorrection = true;
    };
    const deletePlay = (play: Play): void => {
      selectedPlay.value = play;
      //dialogShow.delete = true;
    };
    const submitPlay = (play: Play): void => {
      selectedPlay.value = play;
      //dialogShow.submit = true;
    };
    const scrobbleToCheckpoint = (play: Play): void => {
      selectedPlay.value = play;
      //dialogShow.scrobble = true;
    };

    const scrobbleUnsubmitted = (): void => {
      //dialogShow.scrobble = true;
    };
    const deleteMultiSelected = (): void => {
      if (canDeleteMultiSelection.value === true) {
        //dialogShow.multiDelete = true;
      } else {
        alert("Invalid selection - must select only deleteable plays.");
      }
    };
    const scrobbleMultiSelected = (): void => {
      if (canScrobbleMultiSelection.value === true) {
        //dialogShow.multiScrobble = true;
      } else {
        alert("Invalid selection - must select only submittable plays.");
      }
    };

    const scrobblingOverlay = ref(false);
    const deleteRequestSubmitting = ref(false);
    const scrobbleRequestSubmitting = ref(false);

    const cardHeaderStyle = {
      "--padding-left": "12px",
    };
    const cardContentStyle = {
      "--padding-left": "0",
      "--padding-right": "0",
      "--padding-bottom": "0",
    };

    const iconButtonStyles = {
      "--icon-size": `${buttonIconSize}px`,
    };

    return {
      pageNumber,
      pageSize,
      selectedPlay,
      playEdit,
      //dialogShow,
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
      editPlay,
      approveAutoCorrection,
      deletePlay,
      submitPlay,
      scrobbleToCheckpoint,
      scrobbleUnsubmitted,
      deleteMultiSelected,
      scrobbleMultiSelected,

      scrobblingOverlay,
      deleteRequestSubmitting,
      scrobbleRequestSubmitting,

      cardHeaderStyle, // Doesn't currently work
      cardContentStyle,

      buttonIconSize,
      iconButtonStyles,
    };
  },
});
</script>
