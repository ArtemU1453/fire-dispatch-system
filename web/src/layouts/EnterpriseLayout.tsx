import { Outlet } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { Footer } from "@/components/layout/Footer";
import { NotificationPanel } from "@/components/layout/NotificationPanel";

/** The main Enterprise layout: Header / Sidebar / Content / Footer + Notifications. */
export function EnterpriseLayout() {
  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="min-h-0 flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
      <Footer />
      <NotificationPanel />
    </div>
  );
}
