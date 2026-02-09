import express from "express";
import axios from "axios";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());

const { PORT, TYPESENSE_API_KEY, TYPESENSE_HOST } = process.env;

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


app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
