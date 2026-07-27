/**
 * Header KPI statistics for the dispatcher workspace.
 */

export interface WorkspaceStats {
  /** Number of currently active incidents. */
  activeIncidents: number;
  /** Units available for dispatch. */
  freeUnits: number;
  /** Units currently engaged (operational but not available). */
  busyUnits: number;
  /** Average ETA across assigned units, in seconds (null when unknown). */
  avgEtaSeconds: number | null;
}
