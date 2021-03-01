declare module "wave-ui" {
  import { App } from "@vue/runtime-core";

  export interface WaveUIConfigParam {
    breakpoints?: {
      xs?: number;
      sm?: number;
      md?: number;
      lg?: number;
      xl?: number; // Xl only needs a greater value than lg but starts from lg and goes to infinity.
    };
    colors?: {
      primary?: string;
      secondary?: string;
      success?: string;
      error?: string;
      warning?: string;
      info?: string;
    };
    disableColorShades?: boolean;
  }

  /*export interface WaveUI {
    breakpoint: {
      name: string;
      xs: boolean;
      sm: boolean;
      md: boolean;
      lg: boolean;
      xl: boolean;
    }
  }

  export default class WaveUIConstructor {
    new (app: App, config?: WaveUIConfigParam): WaveUI;
    install(app: App): void;
    registered: boolean;
    instance: WaveUI;
  }*/

  export default class WaveUI {
    constructor(app: App, config?: WaveUIConfigParam);
    static install(app: App): void;
    static registered: boolean;
    static instance: WaveUI;

    breakpoint: {
      name: string;
      xs: boolean;
      sm: boolean;
      md: boolean;
      lg: boolean;
      xl: boolean;
    };
  }
}
