from sessions import SessionManager

default_headers = [
    ("Content-Type", "application/fhir+json"),
]


# Whenever you delete a document where a collection is anchored, you must also
# delete the collection, since the document's delete doesn't actually know
# anything about the collection itself.
def delete_collection(collection, batch_size=100):
    completed = False
    del_count = batch_size
    total_deleted = 0
    while del_count > 0:
        del_count = 0
        docs = collection.list_documents(page_size=batch_size)
        for doc in docs:
            doc.delete()
            del_count += 1
            total_deleted += 1

    return total_deleted


def get_editor(body):
    editor = None

    if "editor" in body:
        editor = body["editor"]
        del body["editor"]
    return SessionManager.create_user_id(editor=editor)
