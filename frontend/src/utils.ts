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
