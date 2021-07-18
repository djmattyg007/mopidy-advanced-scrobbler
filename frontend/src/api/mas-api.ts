import type { AxiosError, AxiosInstance } from "axios";

import { isAxiosError } from "@/http";
import type { Play, EditablePlay } from "@/types";

interface Notifier {
  success(message: string): void;
  error(message: string): void;
}

export interface LoadPlaysResponse {
  readonly plays: ReadonlyArray<Play>;
  readonly playIdMapping: Record<Play["playId"], number>;
  readonly counts: {
    readonly overall: number;
    readonly unsubmitted: number;
  };
}

export interface ScrobbleResponse {
  readonly success: boolean;
  readonly foundPlays: ReadonlyArray<number>;
  readonly scrobbledPlays: ReadonlyArray<number>;
  readonly markedPlays: ReadonlyArray<number>;
  readonly message: string | null;
}

export class MasApi {
  private readonly http: AxiosInstance;
  private readonly notifier: Notifier;

  public constructor(http: AxiosInstance, notifier: Notifier) {
    this.http = http;
    this.notifier = notifier;
  }

  private handleError(msg: string, err: Error | AxiosError): void {
    console.error(err);

    let errMsg = `${msg}`;
    if (isAxiosError(err) && err.response && err.response.data.message) {
      errMsg += `: ${err.response.data.message}`;
    } else {
      errMsg += ".";
    }

    this.notifier.error(errMsg);
  }

  public async loadPlays(pageNumber: number, pageSize: number): Promise<LoadPlaysResponse> {
    const response = await this.http.get<LoadPlaysResponse>("/plays/load", {
      params: {
        page: pageNumber,
        page_size: pageSize,
      },
    });
    return response.data;
  }

  public async editPlay(play: Readonly<EditablePlay>): Promise<boolean> {
    let success = false;
    try {
      await this.http.post("/plays/edit", { play });
      success = true;
      this.notifier.success("Successfully saved play.");
    } catch (err) {
      this.handleError("Error while saving play", err);
    }

    return success;
  }

  public async approveAutoCorrection(playId: number): Promise<boolean> {
    let success = false;
    try {
      await this.http.post("/approve-auto", { playId });
      success = true;
      this.notifier.success("Successfully approved auto-correction.");
    } catch (err) {
      this.handleError("Error while approving auto-correction", err);
    }

    return success;
  }

  public async submitDelete(playId: number): Promise<boolean> {
    let success = false;
    try {
      await this.http.post("/plays/delete", { playId });
      success = true;
      this.notifier.success("Successfully deleted play.");
    } catch (err) {
      this.handleError("Error while deleting play", err);
    }

    return success;
  }

  public async submitSinglePlay(playId: number): Promise<boolean> {
    let success = false;
    try {
      await this.http.post("/plays/submit", { playId });
      success = true;
      this.notifier.success("Successfully scrobbled play.");
    } catch (err) {
      this.handleError("Error while scrobbling play", err);
    }

    return success;
  }

  public async scrobbleUnsubmitted(checkpointId?: number): Promise<ScrobbleResponse | null> {
    const params: Record<string, unknown> = {};
    if (checkpointId) {
      params["checkpoint"] = checkpointId;
    }

    let response: ScrobbleResponse;
    try {
      response = (await this.http.post<ScrobbleResponse>("/scrobble", params)).data;
      this.notifier.success("Successfully scrobbled plays.");
      return response;
    } catch (err) {
      this.handleError("Error while scrobbling", err);
      return null;
    }
  }

  public async submitMultiDelete(playIds: ReadonlyArray<number>): Promise<boolean> {
    let success = false;
    try {
      await this.http.post("/plays/delete-many", { playIds });
      success = true;
      this.notifier.success("Successfully deleted plays.");
    } catch (err) {
      this.handleError("Error while deleting plays", err);
    }

    return success;
  }

  public async submitMultiScrobble(
    playIds: ReadonlyArray<number>,
  ): Promise<ScrobbleResponse | null> {
    let response: ScrobbleResponse;
    try {
      response = (await this.http.post<ScrobbleResponse>("/plays/scrobble-many", { playIds })).data;
      this.notifier.success("Successfully scrobbled plays.");
      return response;
    } catch (err) {
      this.handleError("Error while scrobbling", err);
      return null;
    }
  }
}
