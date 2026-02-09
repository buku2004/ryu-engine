import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

const { TYPESENSE_API_KEY, TYPESENSE_HOST } = process.env;
const COLLECTION = "posts";

// Create collection
async function createCollection() {
  const schema = {
    name: COLLECTION,
    fields: [
      { name: "id", type: "string" },
      { name: "title", type: "string" },
      { name: "body", type: "string" },
      { name: "author", type: "string", facet: true },
      { name: "created_at", type: "int64", facet: true },
      { name: "source", type: "string", facet: true },
    ]
  };

  try {
    await axios.post(`${TYPESENSE_HOST}/collections`, schema, {
      headers: { "X-TYPESENSE-API-KEY": TYPESENSE_API_KEY },
    });
    console.log("Collection created");
  } catch (err) {
    if (
      err.response?.data?.message?.includes("already exists")
    ) {
      console.log("Collection already exists, continuing...");
    } else {
      console.error("COLLECTION CREATION FAILED:");
      console.error(err.response?.data || err.message);
      process.exit(1);
    }
  }
}


// Fetch sample Reddit data
async function fetchRedditSample() {
  const url = "https://www.reddit.com/r/minecraft.json?limit=50";
  const res = await axios.get(url, {
    headers: { "User-Agent": "topic-search-engine" },
  });

  return res.data.data.children.map((item) => ({
    id: item.data.id,
    title: item.data.title,
    body: item.data.selftext || "",
    author: item.data.author,
    created_at: item.data.created_utc,
    source: "reddit",
  }));
}

// Import into Typesense
async function importDocs(docs) {
  const payload = docs.map((d) => JSON.stringify(d)).join("\n");

  const res = await axios.post(
    `${TYPESENSE_HOST}/collections/${COLLECTION}/documents/import?action=upsert`,
    payload,
    {
      headers: {
        "X-TYPESENSE-API-KEY": TYPESENSE_API_KEY,
        "Content-Type": "text/plain",
      },
    }
  );

  console.log(res.data);
}

(async function run() {
  await createCollection();
  const docs = await fetchRedditSample();
  await importDocs(docs);
})();
