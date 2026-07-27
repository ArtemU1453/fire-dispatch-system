/**
 * DispatcherWorkspacePage — the `/dashboard` route content. Renders inside the
 * existing EnterpriseLayout's <Outlet/>; fills the available height.
 */
import { DispatcherWorkspace } from "../components";

export default function DispatcherWorkspacePage() {
  return (
    <div className="h-full min-h-[640px]">
      <DispatcherWorkspace />
    </div>
  );
}
