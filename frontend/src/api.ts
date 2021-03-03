import axios from "axios";

export const api = axios.create({
  baseURL: "/advanced_scrobbler/api/",
  timeout: 10000,
});
