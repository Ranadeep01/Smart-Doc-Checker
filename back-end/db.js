const { Pool } = require("pg");

const pool = new Pool({
  user: "postgres",
  host: "localhost",
  database: "documents_dev",
  password: "123",
  port: 5432,
});

module.exports = pool;

// cloudinary.config({
//   cloud_name: "dm3de3gy3",
//   api_key: "384768686711434",
//   api_secret: 'xoumq71Vh_KZtYT6f_S54BgJfTA',
// });