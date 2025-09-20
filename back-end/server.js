const express = require("express");
const cors = require("cors");
const multer = require("multer");
const cloudinary = require("cloudinary").v2;
const streamifier = require("streamifier");
const { v4: uuidv4 } = require("uuid");
const { Pool } = require("pg");

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// CORS
app.use(cors({ origin: "http://localhost:3000" }));

// Inline Cloudinary credentials (for testing)
cloudinary.config({
  cloud_name: "dm3de3gy3",
  api_key: "384768686711434",
  api_secret: 'xoumq71Vh_KZtYT6f_S54BgJfTA',
});

// PostgreSQL connection
const pool = new Pool({
  user: "postgres",
  host: "localhost",
  database: "documents_dev",
  password: "123",
  port: 5432,
});

// Upload multiple documents
app.post("/upload-multiple", upload.array("files"), async (req, res) => {
  if (!req.files || req.files.length === 0)
    return res.status(400).send("No files uploaded");

  const submissionId = uuidv4(); // unique ID for this batch
  const uploadedDocs = [];

  try {
    for (const file of req.files) {
      // Upload each file to Cloudinary
      const result = await new Promise((resolve, reject) => {
        const uploadStream = cloudinary.uploader.upload_stream(
          { resource_type: "raw", folder: "smart-docs" },
          (err, fileResult) => {
            if (err) reject(err);
            else resolve(fileResult);
          }
        );
        streamifier.createReadStream(file.buffer).pipe(uploadStream);
      });

      // Save each document to PostgreSQL
      await pool.query(
        `INSERT INTO documents.submissions (document_name, submission_id) 
         VALUES ($1, $2)`,
        [result.original_filename, submissionId]
      );

      uploadedDocs.push({
        name: result.original_filename,
        url: result.secure_url,
        cloudinary_id: result.public_id,
      });
    }

    res.json({ message: "Files uploaded successfully!", submissionId, uploadedDocs });
  } catch (err) {
    console.error(err);
    res.status(500).send("Upload error: " + err.message);
  }
});

app.listen(5000, () => console.log("Backend running on port 5000"));
