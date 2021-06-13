export type PipelineStep<T> = (arg: T) => T;

export function pipeline<T>(...fns: PipelineStep<T>[]): (arg: T) => T {
  return (arg: T): T => fns.reduce((data: T, fn: PipelineStep<T>) => fn(data), arg);
}

export function convertKebabToPascal(text: string): string {
  return text.replace(/(^\w|-\w)/g, (match) => match.replace(/-/, "").toUpperCase());
}
