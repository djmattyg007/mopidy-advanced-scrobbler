<template>
  <main>
    <n-h1>Plays</n-h1>

    <n-card :content-style="cardContentStyle">
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
            size="large"
            aria-label="First Page"
            title="First Page"
            :disabled="plays.isRunning || isFirstPage"
            @click="goToFirstPage"
          >
            <template #icon>
              <n-icon>
                <icon-page-first />
              </n-icon>
            </template>
          </n-button>
          <n-button
            text
            size="large"
            aria-label="Previous Page"
            title="Previous Page"
            :disabled="plays.isRunning || isFirstPage"
            @click="goToPreviousPage"
          >
            <template #icon>
              <n-icon>
                <icon-page-prev />
              </n-icon>
            </template>
          </n-button>
          <n-text strong>{{ pageNumber }}</n-text>
          <n-button
            text
            size="large"
            aria-label="Next Page"
            title="Next Page"
            :disabled="plays.isRunning || !plays.value || plays.value.plays.length < pageSize"
            @click="goToNextPage"
          >
            <template #icon>
              <n-icon>
                <icon-page-next />
              </n-icon>
            </template>
          </n-button>

          <div class="mas-spacer"></div>

          <n-button
            text
            size="large"
            aria-label="Delete Selected"
            title="Delete Selected"
            :disabled="plays.isRunning || deleteRequestSubmitting || !canDeleteMultiSelection"
            @click="deleteMultiSelected"
          >
            <template #icon>
              <n-icon>
                <icon-delete />
              </n-icon>
            </template>
          </n-button>
          <n-button
            text
            size="large"
            aria-label="Scrobble Selected"
            title="Scrobble Selected"
            :disabled="plays.isRunning || scrobbleRequestSubmitting || !canScrobbleMultiSelection"
            @click="scrobbleMultiSelected"
          >
            <template #icon>
              <n-icon>
                <icon-upload />
              </n-icon>
            </template>
          </n-button>
          <n-button
            text
            size="large"
            aria-label="Scrobble Unsubmitted"
            title="Scrobble Unsubmitted"
            :disabled="plays.isRunning || scrobbleRequestSubmitting"
            @click="scrobbleUnsubmitted"
          >
            <template #icon>
              <icon-scrobble-all />
            </template>
          </n-button>
          <n-button
            text
            size="large"
            aria-label="Refresh List"
            title="Refresh List"
            :disabled="plays.isRunning"
            @click="refresh"
          >
            <template #icon>
              <icon-refresh />
            </template>
          </n-button>
        </n-element>
      </template>

      <template v-if="plays.error">
        <p>{{ plays.error }}</p>
        <n-data-table :columns="columns" :data="[]" />
      </template>
      <n-data-table
        v-else
        :columns="columns"
        :data="plays.value ? plays.value.plays : []"
        :row-key="(row) => row.playId"
        v-model:checked-row-keys="selectedRows"
        :loading="plays.isRunning"
      />
    </n-card>
  </main>
</template>

<script lang="ts">
import { computed, defineComponent, h, ref, Ref } from "vue";
import { useAsyncTask } from "vue-concurrency";
import { DataTableColumn, NButton, NCard, NDataTable, NElement, NH1, NIcon, NText } from "naive-ui";
import {
  FastBackward as IconPageFirst,
  StepBackward as IconPagePrev,
  StepForward as IconPageNext,
  TrashAlt as IconDelete,
  Upload as IconUpload,
} from "@vicons/fa";

import { api } from "@/api";

import { Play } from "@/types";

import IconRefresh from "@/icons/RefreshIcon.vue";
import IconScrobbleAll from "@/icons/ScrobbleAllIcon.vue";

import CorrectedLabel from "@/components/CorrectedLabel.vue";
import UnixTimestamp from "@/components/UnixTimestamp.vue";

interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
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
    IconPageFirst,
    IconPageNext,
    IconPagePrev,
    IconRefresh,
    IconScrobbleAll,
    IconUpload,
    NButton,
    NCard,
    NDataTable,
    NElement,
    NH1,
    NIcon,
    NText,
  },
  setup() {
    const pageNumber = ref(1);
    const pageSize = ref(10);

    const selectedPlay = ref(null) as Ref<Play | null>;
    const playEdit = ref(null) as Ref<EditablePlay | null>;

    const columns = computed(() => {
      const cols: DataTableColumn[] = [
        {
          title: "ID",
          key: "playId",
          sorter: false,
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
          align: "center",
          // @ts-ignore
          render(row) {
            // @ts-ignore
            return h(CorrectedLabel, { value: row.corrected });
          },
        },
        {
          title: "Played At",
          key: "playedAt",
          sorter: false,
          // @ts-ignore
          render(row) {
            // @ts-ignore
            return h(UnixTimestamp, { value: row.playedAt });
          },
        },
        {
          title: "Submitted",
          key: "submittedAt",
          sorter: false,
          align: "center",
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

    const retrievePlays = async (): Promise<LoadPlaysResponse> => {
      const response = await api.get<LoadPlaysResponse>("/plays/load", {
        params: {
          page: pageNumber.value,
          page_size: pageSize.value,
        },
      });
      return response.data;
    };
    const retrievePlaysTask = useAsyncTask((): ReturnType<typeof retrievePlays> => {
      return retrievePlays();
    }).drop();
    const plays = ref(retrievePlaysTask.perform());
    const loadPlays = (): void => {
      plays.value = retrievePlaysTask.perform();
    };

    const selectedRows = ref([]) as Ref<number[]>;
    const playsMultiSelected = computed((): boolean => selectedRows.value.length > 0);
    const multiSelectPlays = computed((): ReadonlyArray<Play> => {
      const playsData = plays.value.value;
      if (!playsData) {
        return [];
      }

      const selectedPlays: Play[] = [];

      for (const selectedRowNum of selectedRows.value) {
        selectedPlays.push(playsData.plays[selectedRowNum]);
      }

      return selectedPlays;
    });
    const canDeleteMultiSelection = computed((): boolean => playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt));
    const canScrobbleMultiSelection = computed((): boolean => playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt));
    const playsMultiSelectedCountLabel = computed((): string => {
      const count = selectedRows.value.length;
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

    const cardContentStyle = {
      "--padding-left": "0",
      "--padding-right": "0",
      "--padding-bottom": "0",
    };

    return {
      pageNumber,
      pageSize,
      selectedPlay,
      playEdit,
      //dialogShow,
      columns,
      isFirstPage,
      plays,
      selectedRows,
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

      cardContentStyle,
    };
  },
});
</script>
