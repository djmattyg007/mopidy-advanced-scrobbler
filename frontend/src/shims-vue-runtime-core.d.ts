import WaveUI from "wave-ui";

declare module "@vue/runtime-core" {
  export interface ComponentCustomProperties {
    $waveui: WaveUI;
  }
}
