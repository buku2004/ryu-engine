import express from "express";
import axios from "axios";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());

const { PORT, TYPESENSE_API_KEY, TYPESENSE_HOST } = process.env;

if (!TYPESENSE_HOST || !TYPESENSE_API_KEY) {
  console.error("Missing TYPESENSE_HOST or TYPESENSE_API_KEY in environment.");
  console.error("Ensure your .env contains TYPESENSE_HOST and TYPESENSE_API_KEY and restart the server.");
  process.exit(1);
}

const port = PORT || 3000;

console.log(`Using Typesense host: ${TYPESENSE_HOST}`);
console.log(`Backend will listen on port ${port}`);

app.get("/search", async (req, res) => {
  const q = req.query.q?.trim();
  if (!q) {
    return res.status(400).json({ error: "Query is required" });
  }

  try {
    const response = await axios.post(
      `${TYPESENSE_HOST}/collections/posts/documents/search`,
      {
        q,
        query_by: "title,body",
        per_page: 10
      },
      {
        headers: {
          "X-TYPESENSE-API-KEY": TYPESENSE_API_KEY
        }
      }
    );

    res.json(response.data);
  } catch (err) {
    console.error("FULL ERROR ↓↓↓");
    console.error(err.response?.data || err.message);
    res.status(500).json(err.response?.data || err.message);
  }
});


app.listen(port, () => {
  console.log(`Backend running on http://localhost:${port}`);
});
