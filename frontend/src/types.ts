export enum Corrected {
  NOT_CORRECTED = 0,
  MANUALLY_CORRECTED = 1,
  AUTO_CORRECTED = 2,
}

export interface Play {
  readonly playId: number; // Integer
  readonly trackUri: string;
  readonly artist: string;
  readonly title: string;
  readonly album: string;
  readonly origArtist: string;
  readonly origTitle: string;
  readonly origAlbum: string;
  readonly corrected: Corrected;
  readonly musicbrainzId: string | null;
  readonly duration: number; // Number of seconds as an integer
  readonly playedAt: number; // UNIX timestamp
  readonly submittedAt: number | null; // UNIX timestamp
}

export interface Correction {
  readonly trackUri: string;
  readonly artist: string;
  readonly title: string;
  readonly album: string;
}

export interface EditablePlay {
  readonly playId: number;
  readonly trackUri: string;
  title: string;
  artist: string;
  album: string;
  saveCorrection: boolean;
  updateAllUnsubmitted: boolean;
}

export type SelectedTheme = "os-theme" | "light" | "dark";
export type ActualTheme = "light" | "dark";

export function sanitiseSelectedTheme(userInput: string): SelectedTheme {
  if (userInput === "os-theme" || userInput === "light" || userInput === "dark") {
    return userInput;
  }

  return "os-theme";
}
