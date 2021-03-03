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
                icon="mdi mdi-refresh"
                text
                lg
                class="ml3"
                aria-label="Refresh Plays"
                :disabled="isPending"
                @click="retrievePlays"
              ></w-button>
            </w-toolbar>
          </template>

          <w-table v-if="error" :headers="headers" :items="[]">
            <template #no-data>
              <p>An error occurred while fetching data.</p>
              <br />
              <p>{{ error }}</p>
            </template>
          </w-table>
          <w-table v-else :headers="headers" :items="data" :loading="isPending">
            <template #item="{ item, label, header }">
              <template v-if="header.key === 'corrected'">
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
      plays: new Promise<ReadonlyArray<Play>>((resolve) => resolve([])),
      headers: [
        { label: "ID", key: "playId", sortable: false },
        { label: "Title", key: "title", sortable: false },
        { label: "Artist", key: "artist", sortable: false },
        { label: "Album", key: "album", sortable: false },
        { label: "Corrected", key: "corrected", sortable: false },
        { label: "Played At", key: "playedAt", sortable: false },
        { label: "Submitted", key: "submittedAt", sortable: false },
      ],
    };
  },
  created() {
    this.plays = this.retrievePlays();
  },
  methods: {
    async retrievePlays(): Promise<ReadonlyArray<Play>> {
      const response = await api.get<LoadPlaysResponse>("/plays/load");
      return response.data.plays;
    },
  },
});
</script>
