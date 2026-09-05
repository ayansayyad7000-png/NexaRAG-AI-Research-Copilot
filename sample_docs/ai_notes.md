# Sample AI Notes

Retrieval-Augmented Generation, usually called RAG, combines information retrieval with language-model generation.

A basic RAG pipeline first converts document chunks into embeddings. These embeddings are stored so they can be searched later.

When a user asks a question, the question is converted into an embedding. The system compares the question vector with document vectors and retrieves the most relevant chunks.

The retrieved chunks are added to the language model prompt. This gives the model evidence that is specific to the user's knowledge base.

Source citations are useful because they let a user inspect the evidence behind an answer.

Local models can improve privacy because documents can remain on the user's own computer instead of being sent to a remote model provider.
