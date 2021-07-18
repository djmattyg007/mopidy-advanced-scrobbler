import axios from "axios";
import type { AxiosError } from "axios";

export const masHttp = axios.create({
  baseURL: "/advanced_scrobbler/api/",
  timeout: 10000,
});

export const mopidyHttp = axios.create({
  baseURL: "/mopidy/rpc",
  timeout: 10000,
});

export function isAxiosError(err: Error | AxiosError): err is AxiosError {
  return "isAxiosError" in err && err.isAxiosError === true;
}
