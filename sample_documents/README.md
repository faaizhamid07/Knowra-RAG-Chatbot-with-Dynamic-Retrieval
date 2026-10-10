# Sample Documents

These PDFs are optional example documents for demonstrating Knowra's document-based retrieval. They are **not loaded or indexed automatically**.

## Use the samples in a demo

1. Choose the example documents relevant to the question you want to demonstrate.
2. Copy those files into the project's `data/` directory (the application reads documents from `data/`, not from this folder).
3. Start Knowra.
4. Open **Data Management** and select **Rebuild Vectorstore**.
5. Ask questions about the content of the selected documents.

For another use case, use your own relevant PDF or TXT files instead. Replace the runtime files in `data/` and rebuild the vector store. Keep this folder as a source of optional demo examples.

Do not place private or sensitive documents in a public repository. Files placed in `data/` are intended to be local runtime data and are excluded from Git.
