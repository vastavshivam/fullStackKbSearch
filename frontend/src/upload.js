// src/Upload.js
import React, { useState } from "react";
import { uploadFile } from "./api";

function Upload() {
  const [file, setFile] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    const res = await uploadFile(file);
    console.log("Uploaded:", res);
    alert(res.message);
  };

  return (
    <div>
      <h2>Upload File</h2>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
}

export default Upload;
