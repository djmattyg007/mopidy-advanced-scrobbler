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
