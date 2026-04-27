// Root application component.

import { Routes, Route, Navigate } from "react-router-dom";

import { Home } from "./pages/Home";
import { Chapters } from "./pages/Chapters";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/books/:bookId/chapters" element={<Chapters />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
