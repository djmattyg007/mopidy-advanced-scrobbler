<template>
  <main>
    <h1>Plays</h1>
    <br />

    <w-card class="mb10" content-class="pa0">
      <template #title>
        <w-toolbar class="px2">
          <span v-if="plays.value && plays.value.counts.overall >= 0">
            <span class="text-bold">{{ plays.value.counts.overall }}</span> plays
            <span class="text-bold">({{ plays.value.counts.unsubmitted }}</span> unsubmitted)
          </span>

          <div class="spacer"></div>

          <w-button
            icon="mdi mdi-skip-backward"
            text
            lg
            class="mx1"
            aria-label="First Page"
            :disabled="plays.isRunning || isFirstPage"
            @click="goToFirstPage"
          />
          <w-button
            icon="mdi mdi-step-backward"
            text
            lg
            class="mx1"
            aria-label="Previous Page"
            :disabled="plays.isRunning || isFirstPage"
            @click="goToPreviousPage"
          />
          <span class="mx2 text-bold">{{ pageNumber }}</span>
          <w-button
            icon="mdi mdi-step-forward"
            text
            lg
            class="mx1"
            aria-label="Next Page"
            :disabled="plays.isRunning || !plays.value || plays.value.plays.length < pageSize"
            @click="goToNextPage"
          />

          <div class="spacer"></div>

          <w-button
            icon="mdi mdi-delete-forever"
            text
            lg
            class="ml3"
            aria-label="Delete Selected"
            title="Delete Selected"
            :disabled="plays.isRunning || deleteRequestSubmitting || !canDeleteMultiSelection"
            @click="deleteMultiSelected"
          ></w-button>
          <w-button
            icon="mdi mdi-upload"
            text
            lg
            class="ml3"
            aria-label="Scrobble Selected"
            title="Scrobble Selected"
            :disabled="plays.isRunning || scrobbleRequestSubmitting || !canScrobbleMultiSelection"
            @click="scrobbleMultiSelected"
          ></w-button>
          <w-button
            icon="mdi mdi-auto-upload"
            text
            lg
            class="ml3"
            aria-label="Scrobble Unsubmitted"
            title="Scrobble Unsubmitted"
            :disabled="plays.isRunning || scrobbleRequestSubmitting"
            @click="scrobbleUnsubmitted"
          ></w-button>
          <w-button
            icon="mdi mdi-refresh"
            text
            lg
            class="ml3"
            aria-label="Refresh List"
            title="Refresh List"
            :disabled="plays.isRunning"
            @click="refresh"
          ></w-button>
        </w-toolbar>
      </template>

      <w-table
        v-if="plays.error"
        :headers="headers"
        :items="[]"
        :mobile-breakpoint="900"
        class="bd0"
      >
        <template #no-data>
          <p>An error occurred while fetching data.</p>
          <br />
          <p>{{ plays.error }}</p>
        </template>
      </w-table>
      <w-table
        v-else
        :headers="headers"
        :items="plays.value ? plays.value.plays : []"
        :selectable-rows="true"
        v-model:selected-rows="selectedRows"
        :loading="plays.isRunning"
        :mobile-breakpoint="900"
        class="bd0"
      >
        <template #item-cell="{ item, label, header }">
          <template v-if="header.key === 'actions'">
            <w-menu left hide-on-menu-click>
              <template #activator="{ on }">
                <w-button class="ml1" v-on="on" bg-color="secondary" lg>Menu</w-button>
              </template>

              <ul class="menu-list">
                <li v-if="!item.submittedAt">
                  <w-button text lg @click="editPlay(item)">Edit</w-button>
                </li>
                <li v-if="item.corrected === 2">
                  <!-- IF auto-corrected -->
                  <w-button text lg @click="approveAutoCorrection(item)"
                    >Approve Auto-Correction</w-button
                  >
                </li>
                <li v-if="!item.submittedAt">
                  <w-button text lg @click="submitPlay(item)">Submit</w-button>
                </li>
                <li v-if="!item.submittedAt">
                  <w-button text lg @click="deletePlay(item)">Delete</w-button>
                </li>
                <li v-if="!item.submittedAt">
                  <w-button text lg @click="scrobbleToCheckpoint(item)">Scrobble To Here</w-button>
                </li>
              </ul>
            </w-menu>
          </template>
          <template v-else-if="header.key === 'corrected'">
            <template v-if="[1, 2].includes(item.corrected)">
              <w-tooltip :detach-to="true">
                <template #activator="{ on }">
                  <corrected-label v-on="on" :value="item.corrected" />
                </template>

                <dl>
                  <dt>Orig. Artist</dt>
                  <dd>{{ item.origArtist }}</dd>

                  <dt>Orig. Title</dt>
                  <dd>{{ item.origTitle }}</dd>

                  <dt>Orig. Album</dt>
                  <dd>{{ item.origAlbum }}</dd>
                </dl>
              </w-tooltip>
            </template>
            <template v-else>
              <corrected-label :value="item.corrected" />
            </template>
          </template>
          <template v-else-if="header.key === 'playedAt'">
            <unix-timestamp :value="item.playedAt" />
          </template>
          <template v-else-if="header.key === 'submittedAt'">
            <span>
              <w-icon v-if="item.submittedAt" xl color="green">mdi mdi-check</w-icon>
            </span>
          </template>
          <template v-else>
            <span>{{ label }}</span>
          </template>
        </template>
      </w-table>
    </w-card>

    <!--w-dialog
      v-model="dialogEditShow"
      title-class="primary-light1--bg white"
      width="400px"
      :persistent="editFormSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-pencil</w-icon>
        Edit Play
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="editFormSubmitting"
          @click="closeEditDialog"
        ></w-button>
      </template>

      <w-form
        v-if="playEdit"
        v-model="editFormValid"
        id="editForm"
        no-keyup-validation
        @submit="submitEditForm"
      >
        <w-input
          v-model="playEdit.title"
          class="d-flex mb4"
          label="Title"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model="playEdit.artist"
          class="d-flex mb4"
          label="Artist"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model="playEdit.album"
          class="d-flex mb4"
          label="Album"
          :readonly="editFormSubmitting"
        />

        <w-checkbox
          class="d-flex mb4"
          v-model="playEdit.saveCorrection"
          label="Save as Correction"
          :disabled="editFormSubmitting"
        />

        <w-checkbox
          class="d-flex mb4"
          v-model="playEdit.updateAllUnsubmitted"
          label="Update All Unsubmitted Plays"
          :disabled="editFormSubmitting"
        />
      </w-form>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="warning"
          lg
          :disabled="editFormSubmitting"
          @click="closeEditDialog"
          >Cancel</w-button
        >
        <w-button
          type="submit"
          form="editForm"
          class="ml4"
          bg-color="success"
          lg
          :loading="editFormSubmitting"
          :disabled="editFormValid === false || editFormSubmitting"
          >Save</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogApproveAutoCorrectionShow"
      title-class="primary-light1--bg white"
      width="370px"
      :persistent="autoCorrectionApprovalSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-delete</w-icon>
        Approve Auto-Correction
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="autoCorrectionApprovalSubmitting"
          @click="closeApproveAutoCorrectionDialog"
        ></w-button>
      </template>

      <p>Are you sure?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="secondary"
          lg
          :disabled="autoCorrectionApprovalSubmitting"
          @click="closeApproveAutoCorrectionDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="success"
          lg
          :loading="autoCorrectionApprovalSubmitting"
          :disabled="autoCorrectionApprovalSubmitting"
          @click="submitAutoCorrectionApproval"
          >Confirm</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogDeleteShow"
      title-class="error-dark1--bg white"
      width="300px"
      :persistent="deleteRequestSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-delete</w-icon>
        Delete Play
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="deleteRequestSubmitting"
          @click="closeDeleteDialog"
        ></w-button>
      </template>

      <p>Are you sure?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="confirm"
          lg
          :disabled="deleteRequestSubmitting"
          @click="closeDeleteDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="error"
          lg
          :loading="deleteRequestSubmitting"
          :disabled="deleteRequestSubmitting"
          @click="submitDeleteRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogSubmitShow"
      title-class="primary-light1--bg white"
      width="300px"
      :persistent="scrobbleRequestSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-music-box</w-icon>
        Submit Play
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="scrobbleRequestSubmitting"
          @click="closeSubmitDialog"
        ></w-button>
      </template>

      <p>Are you sure?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="secondary"
          lg
          :disabled="scrobbleRequestSubmitting"
          @click="closeSubmitDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="success"
          lg
          :loading="scrobbleRequestSubmitting"
          :disabled="scrobbleRequestSubmitting"
          @click="submitSingleScrobbleRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogScrobbleShow"
      title-class="primary-light1--bg white"
      width="300px"
      :persistent="scrobbleRequestSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-auto-upload</w-icon>
        Scrobble
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="scrobbleRequestSubmitting"
          @click="closeScrobbleDialog"
        ></w-button>
      </template>

      <p>Are you sure?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="secondary"
          lg
          :disabled="scrobbleRequestSubmitting"
          @click="closeScrobbleDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="success"
          lg
          :loading="scrobbleRequestSubmitting"
          :disabled="scrobbleRequestSubmitting"
          @click="submitScrobbleRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogMultiDeleteShow"
      title-class="error-dark1--bg white"
      width="400px"
      :persistent="deleteRequestSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-delete</w-icon>
        Delete Plays
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="deleteRequestSubmitting"
          @click="closeDeleteMultiSelectedDialog"
        >
        </w-button>
      </template>

      <p>Are you sure you want to delete {{ playsMultiSelectedCountLabel }}?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="confirm"
          lg
          :disabled="deleteRequestSubmitting"
          @click="closeDeleteMultiSelectedDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="error"
          lg
          :loading="deleteRequestSubmitting"
          :disabled="deleteRequestSubmitting"
          @click="submitMultiDeleteRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog>

    <w-dialog
      v-model="dialogMultiScrobbleShow"
      title-class="primary-light1--bg white"
      width="400px"
      :persistent="scrobbleRequestSubmitting"
    >
      <template #title>
        <w-icon class="mr2">mdi mdi-upload</w-icon>
        Scrobble
        <div class="spacer" />
        <w-button
          icon="mdi mdi-close"
          color="white"
          text
          xl
          :disabled="scrobbleRequestSubmitting"
          @click="closeScrobbleMultiSelectedDialog"
        ></w-button>
      </template>

      <p>Are you sure you want to scrobble {{ playsMultiSelectedCountLabel }}?</p>

      <template #actions>
        <div class="spacer" />
        <w-button
          class="ml4"
          bg-color="secondary"
          lg
          :disabled="scrobbleRequestSubmitting"
          @click="closeScrobbleMultiSelectedDialog"
          >Cancel</w-button
        >
        <w-button
          class="ml4"
          bg-color="success"
          lg
          :loading="scrobbleRequestSubmitting"
          :disabled="scrobbleRequestSubmitting"
          @click="submitMultiScrobbleRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog-->

    <w-overlay v-model="scrobblingOverlay" :persistent="true" :opacity="0.5">
      <w-progress class="ma1" circle color="green" size="96" />
    </w-overlay>

    <!--w-dialog v-model="dialogScrobbleSuccessShow" title-class="success-light2--bg" width="400px">
      <template #title>
        <w-icon class="mr2">mdi mdi-check-circle</w-icon>
        Success
        <div class="spacer" />
        <w-button icon="mdi mdi-close" text xl @click="closeScrobbleSuccessDialog" />
      </template>

      <div v-if="scrobblingResponse">
        <ol style="list-style: none">
          <li>
            <span class="text-bold">Found Plays</span>:
            <span :class="{ error: scrobblingResponse.foundPlays.length === 0 }">{{
              scrobblingResponse.foundPlays.length
            }}</span>
          </li>
          <li>
            <span class="text-bold">Scrobbled Plays</span>:
            <span
              :class="{
                error:
                  scrobblingResponse.scrobbledPlays.length < scrobblingResponse.foundPlays.length,
              }"
              >{{ scrobblingResponse.scrobbledPlays.length }}</span
            >
          </li>
          <li>
            <span class="text-bold">Marked Plays</span>:
            <span
              :class="{
                error:
                  scrobblingResponse.markedPlays.length < scrobblingResponse.scrobbledPlays.length,
              }"
              >{{ scrobblingResponse.markedPlays.length }}</span
            >
          </li>
        </ol>
        <template v-if="scrobblingResponse.message">
          <br />
          <p>{{ scrobblingResponse.message }}</p>
        </template>
      </div>

      <template #actions>
        <div class="spacer" />
        <w-button class="ml4" bg-color="primary" lg @click="closeScrobbleSuccessDialog"
          >Close</w-button
        >
      </template>
    </w-dialog-->
  </main>
</template>

<script lang="ts">
import { defineComponent, computed, reactive, ref, Ref } from "vue";
import { useAsyncTask } from "vue-concurrency";
import type { Play } from "@/types";

import { masApi } from "@/http";

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
    CorrectedLabel,
    UnixTimestamp,
  },
  setup() {
    const pageNumber = ref(1);
    const pageSize = ref(50);

    const selectedPlay = ref(null) as Ref<Play | null>;
    const playEdit = ref(null) as Ref<EditablePlay | null>;

    const dialogShow = reactive({
      edit: false,
      approveAutoCorrection: false,
      delete: false,
      submit: false,
      scrobble: false,
      multiDelete: false,
      multiScrobble: false,
    });

    const headers = computed(() => {
      const headers = [
        { label: "ID", key: "playId", sortable: false },
        { label: "Title", key: "title", sortable: false },
        { label: "Artist", key: "artist", sortable: false },
        { label: "Corrected", key: "corrected", sortable: false, align: "center" },
        { label: "Played At", key: "playedAt", sortable: false },
        { label: "Submitted", key: "submittedAt", sortable: false, align: "center" },
        { label: "Actions", key: "actions", sortable: false, align: "right" },
      ];

      //if (!this.$waveui.breakpoint.md) {
      headers.splice(3, 0, { label: "Album", key: "album", sortable: false });
      //}

      return headers;
    });

    const isFirstPage = computed((): boolean => pageNumber.value === 1);

    const retrievePlays = async (): Promise<LoadPlaysResponse> => {
      const response = await masApi.get<LoadPlaysResponse>("/plays/load", {
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
    const canDeleteMultiSelection = computed(
      (): boolean =>
        playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt),
    );
    const canScrobbleMultiSelection = computed(
      (): boolean =>
        playsMultiSelected.value && multiSelectPlays.value.every((play) => !play.submittedAt),
    );
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
      dialogShow.edit = true;
    };
    const approveAutoCorrection = (play: Play): void => {
      selectedPlay.value = play;
      dialogShow.approveAutoCorrection = true;
    };
    const deletePlay = (play: Play): void => {
      selectedPlay.value = play;
      dialogShow.delete = true;
    };
    const submitPlay = (play: Play): void => {
      selectedPlay.value = play;
      dialogShow.submit = true;
    };
    const scrobbleToCheckpoint = (play: Play): void => {
      selectedPlay.value = play;
      dialogShow.scrobble = true;
    };

    const scrobbleUnsubmitted = (): void => {
      dialogShow.scrobble = true;
    };
    const deleteMultiSelected = (): void => {
      if (canDeleteMultiSelection.value === true) {
        dialogShow.multiDelete = true;
      } else {
        alert("Invalid selection - must select only deleteable plays.");
      }
    };
    const scrobbleMultiSelected = (): void => {
      if (canScrobbleMultiSelection.value === true) {
        dialogShow.multiScrobble = true;
      } else {
        alert("Invalid selection - must select only submittable plays.");
      }
    };

    const scrobblingOverlay = ref(false);
    const deleteRequestSubmitting = ref(false);
    const scrobbleRequestSubmitting = ref(false);

    return {
      pageNumber,
      pageSize,
      selectedPlay,
      playEdit,
      dialogShow,
      headers,
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
    };
  },
});
</script>

<!--script lang="ts">
import { defineComponent } from "vue";
import { Promised } from "vue-promised";
import type { TableHeader, TableRowSelectEvent } from "wave-ui";

import { Play, Corrected } from "@/types";

import { api } from "@/api";

import CorrectedLabel from "@/components/CorrectedLabel.vue";
import UnixTimestamp from "@/components/UnixTimestamp.vue";

interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
  readonly counts: {
    readonly overall: number;
    readonly unsubmitted: number;
  };
}

interface ScrobbleResponse {
  readonly success: boolean;
  readonly foundPlays: ReadonlyArray<number>;
  readonly scrobbledPlays: ReadonlyArray<number>;
  readonly markedPlays: ReadonlyArray<number>;
  readonly message: string | null;
}

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
    CorrectedLabel,
    Promised,
    UnixTimestamp,
  },
  data() {
    return {
      pageNumber: 1,
      pageSize: 50,
      plays: new Promise<LoadPlaysResponse>((resolve) => {
        return resolve({
          plays: [],
          counts: { overall: -1, unsubmitted: -1 },
        });
      }),
      selectedPlay: null as Play | null,
      playEdit: null as EditablePlay | null,

      multiSelectPlays: [] as Play[],

      dialogEditShow: false,
      dialogApproveAutoCorrectionShow: false,
      dialogDeleteShow: false,
      dialogSubmitShow: false,
      dialogMultiDeleteShow: false,
      dialogMultiScrobbleShow: false,

      editFormValid: null,
      editFormSubmitting: false,
      autoCorrectionApprovalSubmitting: false,
      deleteRequestSubmitting: false,
      scrobbleRequestSubmitting: false,

      dialogScrobbleShow: false,
      scrobblingOverlay: false,
      scrobblingResponse: null as ScrobbleResponse | null,
      dialogScrobbleSuccessShow: false,

      selectedRows: [],
    };
  },
  computed: {
    headers(): TableHeader[] {
      const headers = [
        { label: "ID", key: "playId", sortable: false },
        { label: "Title", key: "title", sortable: false },
        { label: "Artist", key: "artist", sortable: false },
        { label: "Corrected", key: "corrected", sortable: false, align: "center" },
        { label: "Played At", key: "playedAt", sortable: false },
        { label: "Submitted", key: "submittedAt", sortable: false, align: "center" },
        { label: "Actions", key: "actions", sortable: false, align: "right" },
      ];

      if (!this.$waveui.breakpoint.md) {
        headers.splice(3, 0, { label: "Album", key: "album", sortable: false });
      }

      return headers;
    },
    isFirstPage(): boolean {
      return this.pageNumber === 1;
    },

    validators(): { [key: string]: (value: unknown) => true | string } {
      return {
        required: (value: unknown) => {
          if (typeof value !== "string") {
            return "Value is not a string.";
          }

          if (value.trim().length === 0) {
            return "Value cannot be empty.";
          }

          return true;
        },
      };
    },
    playsMultiSelected(): boolean {
      return this.multiSelectPlays.length > 0;
    },
    canDeleteMultiSelection(): boolean {
      return this.playsMultiSelected && this.multiSelectPlays.every((play) => !play.submittedAt);
    },
    canScrobbleMultiSelection(): boolean {
      return this.playsMultiSelected && this.multiSelectPlays.every((play) => !play.submittedAt);
    },
    playsMultiSelectedCountLabel(): string {
      const count = this.multiSelectPlays.length;
      if (count === 1) {
        return `${count} play`;
      } else {
        return `${count} plays`;
      }
    },
  },
  created() {
    this.loadPlays();
  },
  watch: {
    dialogEditShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedPlay = null;
          this.playEdit = null;
        });
      }
    },
    dialogDeleteShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedPlay = null;
        });
      }
    },
    dialogSubmitShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedPlay = null;
        });
      }
    },
    dialogScrobbleSuccessShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedPlay = null;
          this.scrobblingResponse = null;
        });
      }
    },
  },
  methods: {
    goToNextPage(): void {
      this.pageNumber += 1;
      this.loadPlays();
    },
    goToPreviousPage(): void {
      const currentPage = this.pageNumber;
      if (currentPage === 1) {
        return;
      }

      this.pageNumber = currentPage - 1;
      this.loadPlays();
    },
    goToFirstPage(): void {
      this.pageNumber = 1;
      this.loadPlays();
    },
    refresh(): void {
      this.pageNumber = 1;
      this.loadPlays();
    },
    loadPlays(): void {
      this.plays = this.retrievePlays();
    },
    async retrievePlays(): Promise<LoadPlaysResponse> {
      const response = await api.get<LoadPlaysResponse>("/plays/load", {
        params: {
          page: this.pageNumber,
          page_size: this.pageSize,
        },
      });
      return response.data;
    },
    updateMultiSelectPlays(data: TableRowSelectEvent<Play>): void {
      this.multiSelectPlays = data.selectedRows;
    },

    editPlay(play: Play): void {
      this.selectedPlay = play;
      this.playEdit = {
        playId: play.playId,
        trackUri: play.trackUri,
        title: play.title,
        artist: play.artist,
        album: play.album,
        saveCorrection: true,
        updateAllUnsubmitted: true,
      };
      this.dialogEditShow = true;
    },
    approveAutoCorrection(play: Play): void {
      this.selectedPlay = play;
      this.dialogApproveAutoCorrectionShow = true;
    },
    deletePlay(play: Play): void {
      this.selectedPlay = play;
      this.dialogDeleteShow = true;
    },
    submitPlay(play: Play): void {
      this.selectedPlay = play;
      this.dialogSubmitShow = true;
    },
    closeEditDialog(): void {
      this.dialogEditShow = false;
    },
    closeApproveAutoCorrectionDialog(): void {
      this.dialogApproveAutoCorrectionShow = false;
    },
    closeDeleteDialog(): void {
      this.dialogDeleteShow = false;
    },
    closeSubmitDialog(): void {
      this.dialogSubmitShow = false;
    },

    scrobbleUnsubmitted(): void {
      this.dialogScrobbleShow = true;
    },
    scrobbleToCheckpoint(play: Play): void {
      this.selectedPlay = play;
      this.dialogScrobbleShow = true;
    },
    closeScrobbleDialog(): void {
      this.dialogScrobbleShow = false;
    },
    closeScrobbleSuccessDialog(): void {
      this.dialogScrobbleSuccessShow = false;
    },

    deleteMultiSelected(): void {
      if (this.canDeleteMultiSelection === true) {
        this.dialogMultiDeleteShow = true;
      } else {
        alert("Invalid selection - must select only deleteable plays.");
      }
    },
    closeDeleteMultiSelectedDialog(): void {
      this.dialogMultiDeleteShow = false;
    },
    scrobbleMultiSelected(): void {
      if (this.canScrobbleMultiSelection === true) {
        this.dialogMultiScrobbleShow = true;
      } else {
        alert("Invalid selection - must select only submittable plays.");
      }
    },
    closeScrobbleMultiSelectedDialog(): void {
      this.dialogMultiScrobbleShow = false;
    },

    async submitEditForm(): Promise<void> {
      if (this.editFormSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("The edit form is already being submitted.");
        return;
      } else if (!this.playEdit || !this.selectedPlay) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No play was open for editing.");
        return;
      } else if (this.editFormValid !== true) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("Form is not valid.");
        return;
      }

      this.editFormSubmitting = true;
      const updateAllUnsubmitted = this.playEdit.updateAllUnsubmitted;

      try {
        await api.post("/plays/edit", {
          play: this.playEdit,
        });
      } catch (err) {
        console.error(err);

        let errMsg = "Error while saving play";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
        this.editFormSubmitting = false;
        return;
      }

      if (updateAllUnsubmitted === false) {
        Object.assign(this.selectedPlay, {
          artist: this.playEdit.artist,
          title: this.playEdit.title,
          album: this.playEdit.album,
          corrected: Corrected.MANUALLY_CORRECTED,
        });
      }

      this.dialogEditShow = false;
      this.$nextTick(() => {
        this.editFormSubmitting = false;
        if (updateAllUnsubmitted === true) {
          this.loadPlays();
        }
      });
    },
    async submitAutoCorrectionApproval(): Promise<void> {
      if (this.autoCorrectionApprovalSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("An approval is already submitting.");
        return;
      } else if (!this.selectedPlay) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No play was selected.");
        return;
      }

      this.autoCorrectionApprovalSubmitting = true;

      let success = false;
      try {
        await api.post("/approve-auto", {
          playId: this.selectedPlay.playId,
        });
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while approving auto-correction";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
      }

      if (success === true) {
        Object.assign(this.selectedPlay, {
          corrected: Corrected.MANUALLY_CORRECTED,
        });
      }

      this.dialogApproveAutoCorrectionShow = false;
      this.$nextTick(() => {
        this.autoCorrectionApprovalSubmitting = false;
      });
    },
    async submitDeleteRequest(): Promise<void> {
      if (this.deleteRequestSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("A delete request is already pending.");
        return;
      } else if (!this.selectedPlay) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No play was selected for deletion.");
        return;
      }

      this.deleteRequestSubmitting = true;

      let success = false;
      try {
        await api.post("/plays/delete", {
          playId: this.selectedPlay.playId,
        });
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while deleting play";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
      }

      this.dialogDeleteShow = false;
      this.$nextTick(() => {
        this.deleteRequestSubmitting = false;
        if (success === true) {
          this.loadPlays();
        }
      });
    },
    async submitSingleScrobbleRequest(): Promise<void> {
      if (this.scrobbleRequestSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("A scrobble request is already pending.");
        return;
      } else if (!this.selectedPlay) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No play was selected for submission.");
        return;
      }

      this.scrobbleRequestSubmitting = true;

      let success = false;
      try {
        await api.post("/plays/submit", {
          playId: this.selectedPlay.playId,
        });
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while submitting play";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
      }

      if (success === true) {
        Object.assign(this.selectedPlay, { submittedAt: Math.floor(Date.now() / 1000) });
      }

      this.dialogSubmitShow = false;
      this.$nextTick(() => {
        this.scrobbleRequestSubmitting = false;
      });
    },
    async submitScrobbleRequest(): Promise<void> {
      if (this.scrobbleRequestSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("A scrobble request is already pending.");
        return;
      }

      this.scrobbleRequestSubmitting = true;
      this.scrobblingOverlay = true;
      this.dialogScrobbleShow = false;

      const params: Record<string, unknown> = {};
      if (this.selectedPlay) {
        params["checkpoint"] = this.selectedPlay.playId;
      }

      let success = false;
      let response: ScrobbleResponse;
      try {
        response = (await api.post<ScrobbleResponse>("/scrobble", params)).data;
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while scrobbling";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);

        this.scrobblingOverlay = false;
        this.$nextTick(() => {
          this.scrobbleRequestSubmitting = false;
          this.selectedPlay = null;
        });
        return;
      }

      this.scrobblingResponse = response;
      this.dialogScrobbleSuccessShow = true;
      this.scrobblingOverlay = false;

      this.$nextTick(() => {
        this.scrobbleRequestSubmitting = false;
        this.selectedPlay = null;
        if (success === true) {
          this.refresh();
        }
      });
    },

    async submitMultiDeleteRequest(): Promise<void> {
      if (this.deleteRequestSubmitting) {
        alert("A delete request is already pending.");
        return;
      } else if (!this.canDeleteMultiSelection) {
        alert("Invalid plays selection.");
        return;
      }

      this.deleteRequestSubmitting = true;

      const params = {
        playIds: this.multiSelectPlays.map((play) => play.playId),
      };

      let success = false;
      try {
        await api.post("/plays/delete-many", params);
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while deleting plays";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
      }

      this.dialogMultiDeleteShow = false;
      this.$nextTick(() => {
        this.deleteRequestSubmitting = false;
        if (success === true) {
          this.loadPlays();
          this.multiSelectPlays = [];
        }
      });
    },
    async submitMultiScrobbleRequest(): Promise<void> {
      if (this.scrobbleRequestSubmitting) {
        alert("A scrobble request is already pending.");
        return;
      } else if (!this.canScrobbleMultiSelection) {
        alert("Invalid plays selection.");
        return;
      }

      this.scrobbleRequestSubmitting = true;
      this.scrobblingOverlay = true;
      this.dialogMultiScrobbleShow = false;

      const params = {
        playIds: this.multiSelectPlays.map((play) => play.playId),
      };

      let success = false;
      let response: ScrobbleResponse;
      try {
        response = (await api.post<ScrobbleResponse>("/plays/scrobble-many", params)).data;
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while scrobbling";
        if (err.isAxiosError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);

        this.scrobblingOverlay = false;
        this.$nextTick(() => {
          this.scrobbleRequestSubmitting = false;
        });
        return;
      }

      this.scrobblingResponse = response;
      this.dialogScrobbleSuccessShow = true;
      this.scrobblingOverlay = false;

      this.$nextTick(() => {
        this.scrobbleRequestSubmitting = false;
        this.multiSelectPlays = [];
        if (success === true) {
          this.refresh();
        }
      });
    },
  },
});
</script-->
