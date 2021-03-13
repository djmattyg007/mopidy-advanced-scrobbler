<template>
  <main>
    <h1>Corrections</h1>
    <br />

    <Promised :promise="corrections">
      <template #combined="{ isPending, data, error }">
        <w-card class="mb10" content-class="pa0">
          <template #title>
            <w-toolbar class="px2">
              <span v-if="data && data.counts.overall >= 0">
                <span class="text-bold">{{ data.counts.overall }}</span> corrections
              </span>

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
              <span class="mx2 text-bold">{{ pageNumber }}</span>
              <w-button
                icon="mdi mdi-step-forward"
                text
                lg
                class="mx1"
                aria-label="Next Page"
                :disabled="isPending || !data || data.corrections.length < pageSize"
                @click="goToNextPage"
              />

              <div class="spacer"></div>

              <w-button
                icon="mdi mdi-refresh"
                text
                lg
                class="ml3"
                aria-label="Refresh List"
                :disabled="isPending"
                @click="refresh"
              />
            </w-toolbar>
          </template>

          <w-table v-if="error" :headers="headers" :items="[]" :mobile-breakpoint="900" class="bd0">
            <template #no-data>
              <p>An error occurred while fetching data.</p>
              <br />
              <p>{{ error }}</p>
            </template>
          </w-table>
          <w-table
            v-else
            :headers="headers"
            :items="data ? data.corrections : []"
            :loading="isPending"
            :mobile-breakpoint="900"
            class="bd0"
          >
            <template #item="{ item, label, header }">
              <template v-if="header.key === 'actions'">
                <w-button class="ml1" bg-color="error" lg @click="deleteCorrection(item)"
                  >Delete</w-button
                >

                <w-button class="ml1" bg-color="primary" lg @click="editCorrection(item)"
                  >Edit</w-button
                >
              </template>
              <template v-else-if="header.key === 'trackUri'">
                <w-tooltip top v-if="label.length > 40" transition="scale">
                  <template #activator="{ on }">
                    <span v-on="on">{{ label.slice(0, 40) }}...</span>
                  </template>

                  {{ label }}
                </w-tooltip>
                <span v-else>{{ label }}</span>
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
        Edit Correction
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
        v-if="correctionEdit"
        v-model="editFormValid"
        id="editForm"
        no-keyup-validation
        @submit="submitEditForm"
      >
        <w-input
          v-model.trim="correctionEdit.title"
          class="d-flex mb4"
          label="Title"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model.trim="correctionEdit.artist"
          class="d-flex mb4"
          label="Artist"
          :readonly="editFormSubmitting"
          :validators="[validators.required]"
        />

        <w-input
          v-model.trim="correctionEdit.album"
          class="d-flex mb4"
          label="Album"
          :readonly="editFormSubmitting"
        />

        <w-checkbox
          class="d-flex mb4"
          v-model="correctionEdit.updateAllUnsubmitted"
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
        Delete Correction
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
  </main>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { Promised } from "vue-promised";
import type { TableHeader } from "wave-ui";

import { Correction } from "@/types";

import { api } from "@/api";

interface LoadCorrectionsResponse {
  readonly corrections: ReadonlyArray<Correction>;
  readonly counts: {
    readonly overall: number;
  };
}

interface EditableCorrection {
  readonly trackUri: string;
  title: string;
  artist: string;
  album: string;
  updateAllUnsubmitted: boolean;
}

export default defineComponent({
  name: "CorrectionsView",
  components: {
    Promised,
  },
  data() {
    return {
      pageNumber: 1,
      pageSize: 50,
      corrections: new Promise<LoadCorrectionsResponse>((resolve) => {
        return resolve({
          corrections: [],
          counts: { overall: -1 },
        });
      }),
      selectedCorrection: null as Correction | null,
      correctionEdit: null as EditableCorrection | null,

      dialogEditShow: false,
      dialogDeleteShow: false,

      editFormValid: null,
      editFormSubmitting: false,
      deleteRequestSubmitting: false,
    };
  },
  computed: {
    headers(): TableHeader[] {
      const headers = [
        { label: "URI", key: "trackUri", sortable: false },
        { label: "Title", key: "title", sortable: false },
        { label: "Artist", key: "artist", sortable: false },
        { label: "Album", key: "album", sortable: false },
        { label: "Actions", key: "actions", sortable: false, align: "right" },
      ];

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
    this.loadCorrections();
  },
  watch: {
    dialogEditShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedCorrection = null;
          this.correctionEdit = null;
        });
      }
    },
    dialogDeleteShow(newVal: boolean): void {
      if (!newVal) {
        this.$nextTick(() => {
          this.selectedCorrection = null;
        });
      }
    },
  },
  methods: {
    goToNextPage(): void {
      this.pageNumber += 1;
      this.loadCorrections();
    },
    goToPreviousPage(): void {
      const currentPage = this.pageNumber;
      if (currentPage === 1) {
        return;
      }

      this.pageNumber = currentPage - 1;
      this.loadCorrections();
    },
    goToFirstPage(): void {
      this.pageNumber = 1;
      this.loadCorrections();
    },
    refresh(): void {
      this.pageNumber = 1;
      this.loadCorrections();
    },
    loadCorrections(): void {
      this.corrections = this.retrieveCorrections();
    },
    async retrieveCorrections(): Promise<LoadCorrectionsResponse> {
      const response = await api.get<LoadCorrectionsResponse>("/corrections/load", {
        params: {
          page: this.pageNumber,
          page_size: this.pageSize,
        },
      });
      return response.data;
    },

    editCorrection(correction: Correction): void {
      this.selectedCorrection = correction;
      this.correctionEdit = {
        trackUri: correction.trackUri,
        title: correction.title,
        artist: correction.artist,
        album: correction.album,
        updateAllUnsubmitted: true,
      };
      this.dialogEditShow = true;
    },
    deleteCorrection(correction: Correction): void {
      this.selectedCorrection = correction;
      this.dialogDeleteShow = true;
    },
    closeEditDialog(): void {
      this.dialogEditShow = false;
    },
    closeDeleteDialog(): void {
      this.dialogDeleteShow = false;
    },

    async submitEditForm(): Promise<void> {
      if (this.editFormSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("The edit form is already being submitted.");
        return;
      } else if (!this.correctionEdit || !this.selectedCorrection) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No correction was open for editing.");
        return;
      } else if (this.editFormValid !== true) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("Form is not valid.");
        return;
      }

      this.editFormSubmitting = true;

      try {
        await api.post("/corrections/edit", {
          correction: this.correctionEdit,
        });
      } catch (err) {
        console.error(err);

        let errMsg = "Error while saving correction";
        if (err.isAxisoError && err.response && err.response.data.message) {
          errMsg += `: ${err.response.data.message}`;
        } else {
          errMsg += ".";
        }

        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert(errMsg);
        this.editFormSubmitting = false;
        return;
      }

      Object.assign(this.selectedCorrection, {
        artist: this.correctionEdit.artist,
        title: this.correctionEdit.title,
        album: this.correctionEdit.album,
      });

      this.dialogEditShow = false;
      this.$nextTick(() => {
        this.editFormSubmitting = false;
      });
    },
    async submitDeleteRequest(): Promise<void> {
      if (this.deleteRequestSubmitting) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("A delete request is already pending.");
        return;
      } else if (!this.selectedCorrection) {
        // TODO: replace with a wave-ui notification once they can be centrally managed
        alert("No correction was selected for deletion.");
        return;
      }

      this.deleteRequestSubmitting = true;

      let success = false;
      try {
        await api.post("/corrections/delete", {
          trackUri: this.selectedCorrection.trackUri,
        });
        success = true;
      } catch (err) {
        console.error(err);

        let errMsg = "Error while deleting correction";
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
          this.loadCorrections();
        }
      });
    },
  },
});
</script>
