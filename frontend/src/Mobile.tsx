import MobileView from "./pages/mobile_view";

export default function MobileDemo() {
  return (
    <MobileView
      onMenu={() => {/* open drawer */}}
      onBell={() => {/* open notifications */}}
      onSearch={() => {/* focus search or open search screen */}}
      onNavHome={() => {/* navigate('/home') */}}
      onNavDashboard={() => {/* navigate('/dashboard') */}}
      onNavChat={() => {/* open chat */}}
      onNavSettings={() => {/* navigate('/settings') */}}
      className="max-w-[400px] mx-auto"
    />
  );
}
