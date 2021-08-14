import { useBreakpoint, useMemo } from "vooks";

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function useIsMobile() {
  const breakpointRef = useBreakpoint();
  return useMemo(() => {
    return breakpointRef.value === "xs";
  });
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function useIsTablet() {
  const breakpointRef = useBreakpoint();
  return useMemo(() => {
    return breakpointRef.value === "s";
  });
}

export function formatTime(time: number): string {
  const sign = time < 0 ? "-" : "";
  time = Math.abs(time);

  const minutes = Math.floor(time / 60);
  const seconds = time % 60;
  const secondsStr = seconds < 10 ? `0${seconds}` : String(seconds);

  return `${sign}${minutes}:${secondsStr}`;
}
