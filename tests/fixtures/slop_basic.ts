export function build(input: Input) {
  const cfg = { providerId: input.pid, externalRef: input.ref, providerId: input.pid ?? undefined };
  let unused = computeExpensive(input);
  unused = 0;
  return cfg;
}
