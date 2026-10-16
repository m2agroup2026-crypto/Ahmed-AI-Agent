import { mathRuns } from "../../../packages/presentation/content";

export function MathText({ text }: { text: string }) {
  return <>{mathRuns(text).map((run, index) => run.math ? <bdi dir="ltr" key={index}>{run.text}</bdi> : run.text)}</>;
}
