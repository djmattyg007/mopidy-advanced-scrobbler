<template>
  <div>
    <n-element :class="row1Class">
      <n-text v-if="mopidyState.playback.state === 'stopped'" class="text-center">stopped</n-text>
      <template v-else>
        <n-text v-for="n in 4" :key="n" class="track-info">{{ trackInfo }}</n-text>
      </template>
    </n-element>
    <div class="playback-control-row2">
      <n-element class="playback-position">
        <n-text>{{ positionLabel }} / {{ durationLabel }}</n-text>
      </n-element>
      <div class="mas-spacer"></div>
      <n-element class="track-controls">
        <n-button-group :class="trackControlsBtnGroupClass">
          <n-button @click="skipBackward">
            <template #icon>
              <icon-skip-backward />
            </template>
          </n-button>
          <n-button v-if="mopidyState.playback.state === 'playing'" @click="pause">
            <template #icon>
              <icon-pause />
            </template>
          </n-button>
          <n-button v-else @click="play">
            <template #icon>
              <icon-play />
            </template>
          </n-button>
          <n-button @click="stop">
            <template #icon>
              <icon-stop />
            </template>
          </n-button>
          <n-button @click="skipForward">
            <template #icon>
              <icon-skip-forward />
            </template>
          </n-button>
        </n-button-group>
      </n-element>
    </div>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent } from "vue";
import { NButton, NButtonGroup, NElement, NText, useMessage } from "naive-ui";

import { mopidyHttp } from "@/http";
import { JsonRpcApi, MopidyApi } from "@/api/mopidy-api";
import { mopidyState } from "@/mopidy";
import { formatTime, useIsMobile } from "@/utils";

import IconPause from "@/icons/PauseIcon.vue";
import IconPlay from "@/icons/PlayIcon.vue";
import IconSkipBackward from "@/icons/SkipBackwardIcon.vue";
import IconSkipForward from "@/icons/SkipForwardIcon.vue";
import IconStop from "@/icons/StopIcon.vue";

export default defineComponent({
  name: "NowPlayingPanel",
  components: {
    IconPause,
    IconPlay,
    IconSkipBackward,
    IconSkipForward,
    IconStop,
    NButton,
    NButtonGroup,
    NElement,
    NText,
  },
  setup() {
    const message = useMessage();

    const isMobileRef = useIsMobile();

    const mopidyApi = new MopidyApi(new JsonRpcApi(mopidyHttp), message);

    const row1Class = computed(() => {
      const classes: string[] = ["playback-control-row1"];
      if (mopidyState.playback.state === "stopped") {
        classes.push("text-center");
      }
      return classes;
    });

    const trackInfo = computed((): string => {
      const playing = mopidyState.playing;
      let output = `${playing.title} — ${playing.artist}`;
      if (playing.album) {
        output += ` — ${playing.album}`;
      }
      return output;
    });

    const positionLabel = computed(() => formatTime(mopidyState.playback.position));
    const durationLabel = computed(() => formatTime(mopidyState.playing.duration));

    const trackControlsBtnGroupClass = computed(() => {
      const classes: string[] = [];
      if (isMobileRef.value) {
        classes.push("button-group-fill");
      }
      return classes;
    });

    const skipBackward = () => {
      mopidyApi.previous();
    };
    const skipForward = () => {
      mopidyApi.next();
    };
    const pause = () => {
      mopidyApi.pause();
    };
    const play = () => {
      mopidyApi.play();
    };
    const stop = () => {
      mopidyApi.stop();
    };

    return {
      mopidyState,

      row1Class,

      trackInfo,

      positionLabel,
      durationLabel,

      trackControlsBtnGroupClass,

      skipBackward,
      skipForward,
      pause,
      play,
      stop,
    };
  },
});
</script>

<style lang="scss" scoped>
.playback-control-row1 {
  overflow: hidden;
  white-space: nowrap;
  margin-bottom: 4px;
}

.playback-control-row2 {
  display: flex;
}

.track-info {
  animation: marquee 10s linear infinite;
  display: inline-block;
  padding-right: 25px;
}

.playback-position {
  text-align: center;
}

@keyframes marquee {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-100%);
  }
}

@media only screen and (max-width: 639px) {
  .playback-control-row2 {
    flex-direction: column;
  }
}

@media only screen and (min-width: 640px) {
  .playback-control-row1 {
    margin-bottom: 8px;
  }

  .playback-control-row2 {
    flex-direction: row;

    .mas-spacer {
      min-width: 16px;
    }
  }

  .playback-position {
    display: flex;
    align-items: center;
  }
}
</style>
