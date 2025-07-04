import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router";
import { askQuestion, uploadFile, generateToken, startTraining } from "./services/api";
import Ask from "./Ask";

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
/* <Router>
      <Routes>
 <Route path="/ask" element={<Ask />} />
      </Routes>
</Router> */
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
  );
}

export default App;
