# Developer Notes

### Special characters 
Take EXTRA care when dealing with `Coding`(s)/`CodingMapping`(s) and how they are stored in the db. 

Within functions, the format of the code or mapping_code might change format. 

Placeholders are first set in the request to `locutus` and be present in any `code` or `mapped_code` param. But not expected in the request body.

* Firestore `Document` or `Collection` ids cannot/shouldn't contain certain special characters. When referencing a Firestore path, the document id should be a generated index.

* When `Coding`(s) and `CodingMapping`(s) are stored they should be in the 
normalized format. i.e. remove any placeholders.