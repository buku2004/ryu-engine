import express from "express";
import axios from "axios";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());

const { PORT, TYPESENSE_API_KEY, TYPESENSE_HOST } = process.env;

app.get("/search", async (req, res) => {
  const q = req.query.q || "";

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
    res.status(500).json({ error: "Search failed" });
  }
});

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
