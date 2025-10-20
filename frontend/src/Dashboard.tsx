import Dashboard from "./pages/Dashboard";

export default function DashboardPage() {
  return (
    <Dashboard
      onExport={() => { /* export CSV/PDF */ }}
      onReset={() => { /* reset filters */ }}
      className="max-w-[1400px] mx-auto"
    />
  );
}
