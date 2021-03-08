<template>
  <main>
    <h1>Plays</h1>
    <br />

    <Promised :promise="plays">
      <template #combined="{ isPending, data, error }">
        <w-card class="w-card__has-table mb10">
          <template #title>
            <w-toolbar>
              <div class="spacer"></div>

              <w-button
                icon="mdi mdi-skip-backward"
                text
                lg
                class="mx1"
                aria-label="First Page"
                :disabled="isPending || isFirstPage"
                @click="goToFirstPage"
              />
              <w-button
                icon="mdi mdi-step-backward"
                text
                lg
                class="mx1"
                aria-label="Previous Page"
                :disabled="isPending || isFirstPage"
                @click="goToPreviousPage"
              />
              <span class="mx2 make-this-text-bold">{{ pageNumber }}</span>
              <w-button
                icon="mdi mdi-step-forward"
                text
                lg
                class="mx1"
                aria-label="Next Page"
                :disabled="isPending || !data || data.length < pageSize"
                @click="goToNextPage"
              />

              <div class="spacer"></div>

              <w-button
                icon="mdi mdi-refresh"
                text
                lg
                class="ml3"
                aria-label="Refresh Plays"
                :disabled="isPending"
                @click="refresh"
              ></w-button>
            </w-toolbar>
          </template>

          <w-table v-if="error" :headers="headers" :items="[]" :mobile-breakpoint="900">
            <template #no-data>
              <p>An error occurred while fetching data.</p>
              <br />
              <p>{{ error }}</p>
            </template>
          </w-table>
          <w-table
            v-else
            :headers="headers"
            :items="data || []"
            :loading="isPending"
            :mobile-breakpoint="900"
          >
            <template #item="{ item, label, header }">
              <template v-if="header.key === 'actions'">
                <w-button
                  v-if="!item.submittedAt"
                  class="ml1"
                  bg-color="secondary"
                  lg
                  @click="editPlay(item)"
                  >Edit</w-button
                >
                <w-menu left hide-on-menu-click>
                  <template #activator="{ on }">
                    <w-button class="ml1" v-on="on" bg-color="secondary" lg>Menu</w-button>
                  </template>

                  <ul class="menu-list">
                    <li v-if="!item.submittedAt">
                      <w-button text lg @click="submitPlay(item)">Submit</w-button>
                    </li>
                    <li v-if="!item.submittedAt">
                      <w-button text lg @click="deletePlay(item)">Delete</w-button>
                    </li>
                  </ul>
                </w-menu>
              </template>
              <template v-else-if="header.key === 'corrected'">
                <corrected-label :value="item.corrected" />
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
      </template>
    </Promised>

    <w-dialog
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
          v-model.trim="playEdit.title"
          class="d-flex mb4"
          label="Title"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model.trim="playEdit.artist"
          class="d-flex mb4"
          label="Artist"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model.trim="playEdit.album"
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
          @click="submitScrobbleRequest"
          >Confirm</w-button
        >
      </template>
    </w-dialog>
  </main>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { Promised } from "vue-promised";
import type { TableHeader } from "wave-ui";

import { Play, Corrected } from "@/types";

import { api } from "@/api";

import CorrectedLabel from "@/components/CorrectedLabel.vue";
import UnixTimestamp from "@/components/UnixTimestamp.vue";

interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
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
      plays: new Promise<ReadonlyArray<Play>>((resolve) => resolve([])),
      selectedPlay: null as Play | null,
      playEdit: null as EditablePlay | null,

      dialogEditShow: false,
      dialogDeleteShow: false,
      dialogSubmitShow: false,

      editFormValid: null,
      editFormSubmitting: false,
      deleteRequestSubmitting: false,
      scrobbleRequestSubmitting: false,
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

      if (!(this.$waveui.breakpoint.md)) {
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
  },
  methods: {
    goToNextPage(): void {
      this.pageNumber += 1;
      this.loadPlays();
    },
    goToPreviousPage(): void {
      if (this.pageNumber === 1) {
        return;
      }

      this.pageNumber -= 1;
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
    async retrievePlays(): Promise<ReadonlyArray<Play>> {
      const response = await api.get<LoadPlaysResponse>("/plays/load", {
        params: {
          page: this.pageNumber,
          page_size: this.pageSize,
        },
      });
      return response.data.plays;
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
    closeDeleteDialog(): void {
      this.dialogDeleteShow = false;
    },
    closeSubmitDialog(): void {
      this.dialogSubmitShow = false;
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
    async submitScrobbleRequest(): Promise<void> {
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
  },
});
</script>
