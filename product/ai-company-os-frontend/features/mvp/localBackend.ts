// Server-only configuration; neither request parameters nor public environment may select host/path.
export function localBackendPort(raw: string | undefined = process.env.AICOS_D0_BACKEND_PORT): number {
  if (raw === undefined) return 8000;
  if (!/^[1-9][0-9]{3,4}$/.test(raw)) throw Error('invalid local backend port');
  const port = Number(raw);
  if (!Number.isInteger(port) || port < 1024 || port > 49151) throw Error('invalid local backend port');
  return port;
}
