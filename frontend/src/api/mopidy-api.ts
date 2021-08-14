import type { AxiosError, AxiosInstance } from "axios";

import { isAxiosError } from "@/http";

interface Notifier {
  success(message: string): void;
  error(message: string): void;
}

interface JsonRpcResponse<T> {
  readonly jsonrpc: "2.0";
  readonly id: number;
  readonly result: T;
}

function formatError(msg: string, err: Error | AxiosError): string {
  let errMsg = `${msg}`;

  if (isAxiosError(err) && err.response && err.response.data.message) {
    errMsg += `: ${err.response.data.message}`;
  } else {
    errMsg += ".";
  }

  return errMsg;
}

export class JsonRpcApi {
  private readonly http: AxiosInstance;

  private requestCounter = 0;

  public constructor(http: AxiosInstance) {
    this.http = http;
  }

  public async request<T>(method: string, params?: Record<string, unknown>): Promise<T> {
    const id = ++this.requestCounter;
    const data = params ? { jsonrpc: "2.0", id, method, params } : { jsonrpc: "2.0", id, method };
    try {
      const response = (await this.http.post<JsonRpcResponse<T>>("", data)).data;
      if (response.id !== id) {
        throw new Error("Mis-matched ID");
      }
      return response.result;
    } catch (err) {
      console.error(err);
      throw new Error(formatError(`Error calling '${method}'`, err));
    }
  }
}

export class MopidyApi {
  private readonly jsonrpc: JsonRpcApi;
  private readonly notifier: Notifier;

  public constructor(jsonrpc: JsonRpcApi, notifier: Notifier) {
    this.jsonrpc = jsonrpc;
    this.notifier = notifier;
  }

  private handleError(err: Error | AxiosError): void {
    console.error(err);
    this.notifier.error(String(err));
  }

  public async previous(): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.playback.previous");
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Success.");
    return true;
  }

  public async next(): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.playback.next");
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Success.");
    return true;
  }

  public async pause(): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.playback.pause");
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Success.");
    return true;
  }

  public async play(): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.playback.play");
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Success.");
    return true;
  }

  public async stop(): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.playback.stop");
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Success.");
    return true;
  }

  public async playNext(uris: ReadonlyArray<string>): Promise<boolean> {
    let index: number;
    try {
      index = await this.jsonrpc.request("core.tracklist.index", {});
    } catch (err) {
      this.handleError(err);
      return false;
    }

    try {
      await this.jsonrpc.request("core.tracklist.add", { at_position: index + 1, uris });
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Added track to playlist.");
    return true;
  }

  public async addToBottom(uris: ReadonlyArray<string>): Promise<boolean> {
    try {
      await this.jsonrpc.request("core.tracklist.add", { uris });
    } catch (err) {
      this.handleError(err);
      return false;
    }

    this.notifier.success("Added track to playlist.");
    return true;
  }
}
