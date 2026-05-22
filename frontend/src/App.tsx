import { Routes, Route, Navigate } from "react-router-dom";

import { Home } from "./pages/Home";
import { BookMap } from "./pages/BookMap";
import { TopicStudy } from "./pages/Study";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/books/:bookId" element={<BookMap />} />
      <Route path="/books/:bookId/topics/:topicId" element={<TopicStudy />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
