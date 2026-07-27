import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppProviders } from "@/providers/AppProviders";
import { AuthProvider } from "@/providers/AuthProvider";
import { EnterpriseLayout } from "@/layouts/EnterpriseLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { paths } from "@/routes/paths";
import { Loader } from "@/components/ui/loader";
import { LoginPage } from "@/pages/LoginPage";
import { IncidentsPage } from "@/pages/IncidentsPage";
import { ResourcesPage } from "@/pages/ResourcesPage";
import { MapPage } from "@/pages/MapPage";
import { JournalPage } from "@/pages/JournalPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { AdminPage } from "@/pages/AdminPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

// Code-split the dispatcher workspace (it pulls in OpenLayers).
const DispatcherWorkspacePage = lazy(
  () => import("@/features/dispatcher-workspace/pages/DispatcherWorkspacePage"),
);
// Code-split the incident-registration workflow (also OpenLayers-heavy).
const IncidentRegistrationPage = lazy(
  () => import("@/features/incident-registration/pages/IncidentRegistrationPage"),
);

export function App() {
  return (
    <AppProviders>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path={paths.login} element={<LoginPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <EnterpriseLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Navigate to={paths.dashboard} replace />} />
              <Route
                path={paths.dashboard}
                element={
                  <Suspense
                    fallback={
                      <div className="flex h-full items-center justify-center">
                        <Loader label="Загрузка рабочего места…" />
                      </div>
                    }
                  >
                    <DispatcherWorkspacePage />
                  </Suspense>
                }
              />
              <Route
                path="/incidents/new"
                element={
                  <Suspense
                    fallback={
                      <div className="flex h-full items-center justify-center">
                        <Loader label="Загрузка формы регистрации…" />
                      </div>
                    }
                  >
                    <IncidentRegistrationPage />
                  </Suspense>
                }
              />
              <Route path={paths.incidents} element={<IncidentsPage />} />
              <Route path={paths.resources} element={<ResourcesPage />} />
              <Route path={paths.map} element={<MapPage />} />
              <Route path={paths.journal} element={<JournalPage />} />
              <Route path={paths.reports} element={<ReportsPage />} />
              <Route path={paths.settings} element={<SettingsPage />} />
              <Route
                path={paths.admin}
                element={
                  <ProtectedRoute permission="admin.access">
                    <AdminPage />
                  </ProtectedRoute>
                }
              />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </AppProviders>
  );
}
