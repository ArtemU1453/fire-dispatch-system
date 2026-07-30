/**
 * IncidentManagementPage — the `/incidents/:incidentId` route. Reads the id from
 * the URL and renders the management screen inside the existing layout.
 */
import { useParams } from "react-router-dom";
import { IncidentManagement } from "../components";

export default function IncidentManagementPage() {
  const { incidentId } = useParams<{ incidentId: string }>();

  if (!incidentId) {
    return <p className="p-4 text-sm text-danger">Не указан идентификатор происшествия.</p>;
  }

  return (
    <div className="h-full min-h-[680px]">
      <IncidentManagement incidentId={incidentId} />
    </div>
  );
}
