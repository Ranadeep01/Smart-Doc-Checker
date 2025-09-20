import React, { useState } from "react";
import axios from "axios";

function App() {
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("");

  // Handle multiple file selection
  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files)); // convert FileList to array
  };

  const handleUpload = async () => {
    if (files.length === 0) return alert("Select at least one file!");

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file)); // append all files

    try {
      setStatus("Uploading...");
      const res = await axios.post("http://localhost:5000/upload-multiple", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus(
        `Upload successful! Submission ID: ${res.data.submissionId}`
      );
      console.log(res.data.cloudinaryResponses);
    } catch (err) {
      console.error(err);
      setStatus("Upload failed");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-2xl font-bold mb-4">Smart Doc Checker - Upload Docs</h1>
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        className="mb-4"
      />
      <button
        onClick={handleUpload}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Upload
      </button>
      <p className="mt-4">{status}</p>
      {files.length > 0 && (
        <ul className="mt-2">
          {files.map((file, idx) => (
            <li key={idx}>{file.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
