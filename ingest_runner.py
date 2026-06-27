from ingest import ingest_documents

# GST FILING DATA 
ingest_documents(
    path="ingestion/t_docs/gst_filing.txt",
    collection_name="gst"
)
print("GST Filing data Activated")

