import { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [files, setFiles] = useState([]);
  const [submissionId, setSubmissionId] = useState(null);
  const [analysis, setAnalysis] = useState("");
  const [usage, setUsage] = useState({ total_docs_checked:0, total_reports_generated:0, total_cost:0 });

  const handleFileChange = (e) => setFiles(e.target.files);

  const handleUpload = async () => {
    if (files.length < 2 || files.length > 3) return alert("Upload 2–3 documents only.");
    const formData = new FormData();
    for (let file of files) formData.append("files", file);
    try{
      const res = await axios.post("http://localhost:8000/upload", formData, { headers: {"Content-Type":"multipart/form-data"} });
      setSubmissionId(res.data.submission_id);
      alert("Uploaded successfully!");
      fetchUsage();
    } catch (err) {
      return alert("Error uploading files.", err);
    }
  };

  const handleAnalyze = async () => {
    if(!submissionId) return alert("Upload docs first");
    const res = await axios.post("http://localhost:8000/analyze", { submission_id: submissionId });
    setAnalysis(res.data.analysis);
    fetchUsage();
  };

  const fetchUsage = async () => {
    const res = await axios.get("http://localhost:8000/usage");
    setUsage(res.data);
  };

  useEffect(() => {
    fetchUsage();
    const interval = setInterval(fetchUsage, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Smart Doc Checker</h1>
      <input type="file" multiple onChange={handleFileChange}/>
      <button onClick={handleUpload}>Upload</button>
      <button onClick={handleAnalyze} disabled={!submissionId || files.length < 2}>Analyze</button>

      <h2>Analysis Result:</h2>
      <pre>{analysis}</pre>

      <h2>Usage & Billing:</h2>
      <p>Docs Checked: {usage.total_docs_checked}</p>
      <p>Reports Generated: {usage.total_reports_generated}</p>
      <p>Total Cost: {usage.total_cost}</p>
    </div>
  );
}

export default App;
