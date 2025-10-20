import { Routes, Route, Navigate, Link } from "react-router-dom";
import Landing from "./pages/Landing";

import Dashboard from "./pages/Dashboard";
import Assistant from "./pages/Assistant";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/assistant" element={<Assistant />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
