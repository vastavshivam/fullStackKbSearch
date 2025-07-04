// src/App.js
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./auth";
import Upload from "./upload";
import Ask from "./ask";
import Chat from "./chat";
import Register from "./register";

function App() {
  return (
    <>    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/ask" element={<Ask />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/register" element={<Register />} />
      </Routes>
    </Router>
    
    </>
  );
}

export default App;
