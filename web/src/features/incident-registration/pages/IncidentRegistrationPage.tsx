/**
 * IncidentRegistrationPage — the `/incidents/new` route. Renders inside the
 * existing EnterpriseLayout <Outlet/> and fills the available height.
 */
import { IncidentRegistration } from "../components";

export default function IncidentRegistrationPage() {
  return (
    <div className="h-full min-h-[640px]">
      <IncidentRegistration />
    </div>
  );
}
