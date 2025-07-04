<<<<<<< HEAD
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
=======
import React, { useState } from "react";
import { askQuestion, uploadFile, generateToken, startTraining } from "./services/api";

function App() {
  const [question, setQuestion] = useState("");
  const [file, setFile] = useState(null);
  const [answer, setAnswer] = useState("");

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await uploadFile(formData);
    alert(res.data.message);
  };

  const handleAsk = async () => {
    const res = await askQuestion(question, file.name); // assuming file.name as ID
    setAnswer(res.data.answer);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Support Assistant</h1>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload} className="bg-blue-500 text-white p-2 m-2">Upload</button>
      <br />
      <input
        type="text"
        placeholder="Ask a question..."
        className="border p-2 w-1/2"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button onClick={handleAsk} className="bg-green-500 text-white p-2 m-2">Ask</button>
      {answer && <div className="mt-4 p-4 border bg-gray-100">{answer}</div>}
    </div>
>>>>>>> 0749768e729f020b9286c79bd022133edae0d9d6
  );
}

export default App;
