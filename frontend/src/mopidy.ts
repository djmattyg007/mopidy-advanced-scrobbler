import { reactive } from "vue";

import { MasApi, PlaybackDataResponse } from "@/api/mas-api";
import { masHttp } from "@/http";

export enum MopidyConnectionState {
  OFFLINE,
  RECONNECTING,
  ONLINE,
}

export const mopidyState = reactive({
  online: MopidyConnectionState.RECONNECTING,
  playback: {
    state: "stopped" as "playing" | "paused" | "stopped",
    position: 0, // seconds
  },
  playing: {
    trackUri: "",
    title: "",
    artist: "",
    album: "",
    duration: 0, // seconds
  },
});

const dummyNotifier = {
  /* eslint-disable @typescript-eslint/no-empty-function */
  success: () => {},
  error: () => {},
  /* eslint-enable @typescript-eslint/no-empty-function */
};
const masApi = new MasApi(masHttp, dummyNotifier);

let failureCount = 0;
const getMopidyState = async (): Promise<void> => {
  let playbackData: PlaybackDataResponse;
  try {
    playbackData = await masApi.loadPlaybackData();
  } catch (err) {
    console.error(err);
    if (failureCount < 5) {
      mopidyState.online = MopidyConnectionState.RECONNECTING;
      failureCount += 1;
    } else {
      mopidyState.online = MopidyConnectionState.OFFLINE;
    }
    const backoffFactor = Math.pow(2, failureCount);
    setTimeout(getMopidyState, 500 * backoffFactor);
    return;
  }

  failureCount = 0;
  mopidyState.online = MopidyConnectionState.ONLINE;
  mopidyState.playback.state = playbackData.playback.state;
  mopidyState.playback.position = playbackData.playback.position;
  mopidyState.playing.trackUri = playbackData.playing.trackUri;
  mopidyState.playing.title = playbackData.playing.title;
  mopidyState.playing.artist = playbackData.playing.artist;
  mopidyState.playing.album = playbackData.playing.album;
  mopidyState.playing.duration = playbackData.playing.duration;

  setTimeout(getMopidyState, 500);
};
setTimeout(getMopidyState, 2000);
