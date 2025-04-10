from locutus.sessions import SessionManager
from locutus import get_code_index

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


def get_editor(body, editor):
    if body and "editor" in body:
        editor = body["editor"]
        del body["editor"]
    return SessionManager.create_user_id(editor=editor)


def generate_paired_string(thing_one, thing_two):
    ''' 
    Returns the parameters as a string separated by a pipe.
    Use case: Identifying a mapping. code|mapping
    '''
    return f'{thing_one}|{thing_two}'


def generate_mapping_index(thing_one, thing_two):
    ''' 
    Returns the parameters as a string separated by a pipe.

    Ensures the mapping's identifier/index is formatted properly for db indexing

    Use case: Identifying a mapping. code|mapping
    '''
    index_left = get_code_index(thing_one)
    index_right = get_code_index(thing_two)

    return generate_paired_string(index_left,index_right)