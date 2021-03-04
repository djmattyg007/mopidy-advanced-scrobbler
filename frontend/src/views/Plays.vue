<template>
  <main>
    <h1>Plays</h1>
    <br />

    <Promised :promise="plays">
      <template #combined="{ isPending, data, error }">
        <w-card class="w-card__has-table">
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
                <w-button class="ml1" bg-color="secondary" lg>Edit</w-button>
                <w-menu bottom align-right>
                  <template #activator="{ on }">
                    <w-button class="ml1" v-on="on" bg-color="secondary" lg>Menu</w-button>
                  </template>

                  <w-button lg>Submit</w-button>
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
  </main>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { Promised } from "vue-promised";
import type { TableHeader } from "wave-ui";

import type { Play } from "@/types";

import { api } from "@/api";

import CorrectedLabel from "@/components/CorrectedLabel.vue";
import UnixTimestamp from "@/components/UnixTimestamp.vue";

interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
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
  },
  created() {
    this.loadPlays();
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
  },
});
</script>
